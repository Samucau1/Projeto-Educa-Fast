"""Migração aditiva v1 dos cursos. Não deduz atribuições dos pares legados."""
from sqlalchemy import inspect, select

VERSION = 2
PREFIXES = ('cursos', 'curso_', 'atribuicoes_docentes', 'turma_estados', 'academico_')


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
                if table.name.startswith('academico_') == (version == 2):
                    table.create(connection, checkfirst=True)
            connection.execute(versions.insert().values(versao=version))
    missing = {table.name for table in tabelas_cursos(metadata)} - set(inspect(engine).get_table_names())
    if missing:
        raise RuntimeError('Migração de cursos incompleta: ' + ', '.join(sorted(missing)))
