"""Exemplos apenas para banco sintético vazio e validado."""
from decimal import Decimal
from app.database import get_session
from app.models import (TurmaModel, DisciplinaModel, AlunoTurmaModel, ProfessorTurmaModel,
                        ProfessorDisciplinaModel, TurmaDisciplinaModel, NotaModel)
from app.models.curso_model import (CursoModel, CapituloModel, TemaModel, AulaModel, OfertaCursoModel,
    ProgressoAulaModel, EstadoTurmaModel)
from app.models.academico_model import PeriodoLetivoModel, AvaliacaoModel, LancamentoNotaModel
from app.services.cursos import atribuir
from fixtures import exigir_banco_em_memoria


def popular_homologacao(ids):
    exigir_banco_em_memoria()
    with get_session() as db:
        if db.query(TurmaModel).count():
            raise RuntimeError('Exemplos só podem ser criados em banco sintético vazio.')
        mat = DisciplinaModel(nome='Matemática — demonstração', codigo='MAT-DEMO', carga_horaria=60)
        fis = DisciplinaModel(nome='Física — demonstração', codigo='FIS-DEMO', carga_horaria=60)
        turmas = [TurmaModel(nome='Turma A', codigo=f'DEMO-{ano}', ano_letivo=ano) for ano in (2026, 2027)]
        antiga = TurmaModel(nome='Turma antiga para revisão', codigo='DEMO-LEGADA', ano_letivo=2025)
        db.add_all([mat, fis, antiga, *turmas])
        db.flush()
        prof, aluno = ids['professor_id'], ids['aluno_id']
        db.add_all([ProfessorDisciplinaModel(professor_id=prof, disciplina_id=d.id) for d in (mat, fis)])
        db.flush()
        for turma in turmas:
            db.add(EstadoTurmaModel(turma_id=turma.id))
            db.add(AlunoTurmaModel(turma_id=turma.id, aluno_id=aluno))
            atribuir(db, prof, turma.id, mat.id)
        atribuir(db, prof, turmas[0].id, fis.id)
        db.add_all([ProfessorTurmaModel(professor_id=prof, turma_id=antiga.id),
            AlunoTurmaModel(turma_id=antiga.id, aluno_id=aluno),
            TurmaDisciplinaModel(turma_id=antiga.id, disciplina_id=mat.id),
            TurmaDisciplinaModel(turma_id=antiga.id, disciplina_id=fis.id),
            NotaModel(aluno_id=aluno, professor_id=prof, disciplina_id=mat.id, nota=Decimal('7.25'), observacao='Registro antigo para revisão explícita')])
        curso = CursoModel(disciplina_id=mat.id, professor_id=prof, titulo='Álgebra para todos os anos',
            descricao='O mesmo conteúdo nas turmas de 2026 e 2027. Vídeo demonstrativo com identificador sintético.', estado='publicado')
        db.add(curso)
        db.flush()
        cap = CapituloModel(curso_id=curso.id, titulo='Fundamentos', posicao=1)
        db.add(cap)
        db.flush()
        tema = TemaModel(capitulo_id=cap.id, titulo='Equações', posicao=1)
        db.add(tema)
        db.flush()
        aula = AulaModel(tema_id=tema.id, titulo='Primeiros passos', descricao='Substitua o vídeo por material autorizado na homologação institucional.', video_id='abcdefghijk', posicao=1)
        db.add(aula)
        db.flush()
        for index, turma in enumerate(turmas):
            vinculo = db.query(TurmaDisciplinaModel).filter_by(turma_id=turma.id, disciplina_id=mat.id).one()
            oferta = OfertaCursoModel(curso_id=curso.id, turma_disciplina_id=vinculo.id)
            periodo = PeriodoLetivoModel(turma_id=turma.id, nome='1º bimestre', ordem=1, media_referencia=Decimal('6'))
            db.add_all([oferta, periodo])
            db.flush()
            av = AvaliacaoModel(turma_disciplina_id=vinculo.id, periodo_id=periodo.id,
                               titulo=f'Avaliação {turma.ano_letivo}', peso=Decimal('1'), publicada=True)
            db.add(av)
            db.flush()
            db.add(LancamentoNotaModel(avaliacao_id=av.id, aluno_id=aluno, professor_id=prof,
                   valor=Decimal('8.50') if index == 0 else Decimal('5.00'), observacao='Exemplo sintético', versao=1))
            if index == 0:
                db.add(ProgressoAulaModel(aluno_id=aluno, oferta_id=oferta.id, aula_id=aula.id))
        db.commit()
