from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from config import Config

engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    hide_parameters=True,
    connect_args=({"ssl_ca": Config.DB_SSL_CA, "ssl_verify_cert": True, "ssl_verify_identity": True}
                  if Config.DB_SSL_CA else {}),
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_session():
    return SessionLocal()


def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_schema_updates()
    _protect_legacy_fields()


def _protect_legacy_fields():
    """Migrate only known personal-data columns; ciphertext is never double encrypted."""
    from app.crypto import PREFIX, cpf_index, decrypt, encrypt
    inspector = inspect(engine)
    fields_by_table = {"alunos": ("cpf", "data_nascimento"), "professores": ("cpf", "telefone")}
    # Detect legacy formatting duplicates before touching schema or ciphertext.
    with engine.connect() as connection:
        for table in fields_by_table:
            seen = set()
            for value in connection.execute(text(f"SELECT cpf FROM {table} WHERE cpf IS NOT NULL")).scalars():
                index = cpf_index(decrypt(str(value)))
                if index and index in seen:
                    raise RuntimeError(f"CPFs legados duplicados em {table}. Reconcilie os cadastros no backup de homologacao antes de migrar.")
                seen.add(index)
    for table, fields in fields_by_table.items():
        columns = {c["name"]: c for c in inspector.get_columns(table)}
        with engine.begin() as connection:
            if "cpf_hash" not in columns:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN cpf_hash VARCHAR(64) NULL"))
            if engine.dialect.name == "mysql":
                for field in fields:
                    if getattr(columns[field]["type"], "length", None) != 512:
                        nullable = "NOT NULL" if table == "professores" and field == "cpf" else "NULL"
                        connection.execute(text(f"ALTER TABLE {table} MODIFY {field} VARCHAR(512) {nullable}"))
            rows = connection.execute(text(f"SELECT id, {', '.join(fields)}, cpf_hash FROM {table}")).mappings()
            for row in rows:
                changes = {}
                for field in fields:
                    value = row[field]
                    if value is not None and not str(value).startswith(PREFIX):
                        changes[field] = encrypt(value)
                if row["cpf"] and not row["cpf_hash"]:
                    changes["cpf_hash"] = cpf_index(decrypt(str(row["cpf"])))
                if changes:
                    assignments = ", ".join(f"{field} = :{field}" for field in changes)
                    connection.execute(text(f"UPDATE {table} SET {assignments} WHERE id = :id"), {**changes, "id": row["id"]})
        indexes = inspector.get_indexes(table)
        constraints = inspector.get_unique_constraints(table)
        if not any(item.get("column_names") == ["cpf_hash"] for item in indexes + constraints):
            with engine.begin() as connection:
                connection.execute(text(f"CREATE UNIQUE INDEX uq_{table}_cpf_hash ON {table} (cpf_hash)"))


def _ensure_schema_updates():
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    if "alunos" in table_names:
        _add_missing_columns(
            inspector,
            "alunos",
            {
                "cpf": "VARCHAR(14) NULL",
                "curso_serie": "VARCHAR(80) NULL",
                "status_matricula": "VARCHAR(20) NULL",
                "foto_perfil": "VARCHAR(255) NULL",
            },
        )

    if "professores" in table_names:
        _add_missing_columns(
            inspector,
            "professores",
            {
                "disciplina_principal": "VARCHAR(80) NULL",
                "formacao_academica": "VARCHAR(120) NULL",
                "regime_trabalho": "VARCHAR(50) NULL",
                "foto_perfil": "VARCHAR(255) NULL",
                "data_admissao": "DATE NULL",
            },
        )

    if "documentos" in table_names:
        _make_nullable_if_needed(inspector, "documentos", "aluno_id", "INTEGER NULL")
        _make_nullable_if_needed(inspector, "documentos", "professor_id", "INTEGER NULL")

    if "solicitacoes_documentos" in table_names:
        _add_missing_columns(
            inspector,
            "solicitacoes_documentos",
            {
                "professor_id": "INTEGER NULL",
            },
        )
        _make_nullable_if_needed(
            inspector,
            "solicitacoes_documentos",
            "aluno_id",
            "INTEGER NULL",
        )

    if "atividades" in table_names:
        _add_missing_columns(
            inspector,
            "atividades",
            {
                "caminho_arquivo": "VARCHAR(255) NULL",
            },
        )


def _add_missing_columns(inspector, table_name, columns_to_add):
    columns = {column["name"] for column in inspector.get_columns(table_name)}
    missing_columns = [
        (column_name, column_definition)
        for column_name, column_definition in columns_to_add.items()
        if column_name not in columns
    ]
    if not missing_columns:
        return

    # Atualiza bancos antigos sem exigir ferramenta de migracao neste projeto.
    with engine.begin() as connection:
        for column_name, column_definition in missing_columns:
            connection.execute(
                text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
            )


def _make_nullable_if_needed(inspector, table_name, column_name, column_definition):
    columns = {column["name"]: column for column in inspector.get_columns(table_name)}
    column = columns.get(column_name)
    if not column or column.get("nullable"):
        return

    if engine.dialect.name != "mysql":
        return

    with engine.begin() as connection:
        connection.execute(
            text(f"ALTER TABLE {table_name} MODIFY COLUMN {column_name} {column_definition}")
        )
