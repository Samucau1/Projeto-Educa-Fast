"""Migrações aditivas v1-v3; não deduzem vínculos ou notas históricas."""
from sqlalchemy import inspect, select

VERSION = 3
PREFIXES = ('cursos', 'curso_', 'atribuicoes_docentes', 'turma_estados', 'academico_', 'escola_')


def tabelas_cursos(metadata):
    return [table for table in metadata.sorted_tables if table.name.startswith(PREFIXES)]


def migrar_cursos(engine, metadata):
    versions = metadata.tables['educafast_migracoes']
    versions.create(engine, checkfirst=True)
    with engine.begin() as connection:
        applied = connection.execute(select(versions.c.versao)).scalars().all()
        if applied and max(applied) > VERSION:
            raise RuntimeError('Banco possui uma migração mais recente. Use uma versão compatível da aplicação.')
        for version in range(1, VERSION + 1):
            if version in applied:
                continue
            # DDL do MySQL não é transacional: checkfirst permite retomar uma execução interrompida.
            for table in tabelas_cursos(metadata):
                table_version = 3 if table.name.startswith('escola_') else 2 if table.name.startswith('academico_') else 1
                if table_version == version:
                    table.create(connection, checkfirst=True)
            connection.execute(versions.insert().values(versao=version))
    missing = {table.name for table in tabelas_cursos(metadata)} - set(inspect(engine).get_table_names())
    if missing:
        raise RuntimeError('Migração de cursos incompleta: ' + ', '.join(sorted(missing)))
