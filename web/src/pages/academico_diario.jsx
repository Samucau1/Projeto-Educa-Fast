import GestaoBase, { bodyGestao } from '../components/GestaoBase';
import Token from '../components/Token';
import { urlFor } from '../core/urls';

export const bodyClass = bodyGestao();
export const titulo = (d, g) => `${d.avaliacao.titulo} | ${g.escola?.nome ?? 'Educa Fast'}`;

export default function AcademicoDiario({ d, g }) {
    const { avaliacao, periodo, turma, disciplina, ativa } = d;
    const editavel = !periodo.fechado && ativa && !avaliacao.publicada;
    return (
        <GestaoBase titulo={avaliacao.titulo} error={d.error}>
            <a href={urlFor('academico.painel')}>← Diário e avaliações</a><section className="page-heading"><div><span className="eyebrow">{turma.nome} · {turma.ano_letivo} · {periodo.nome}</span><h1>{avaliacao.titulo}</h1><p>{disciplina.nome} · peso {avaliacao.peso} · {avaliacao.publicada ? 'Publicada para os alunos' : 'Rascunho privado'}</p></div></section>
            {(periodo.fechado || !ativa) && <div className="notice notice-error">Lançamentos bloqueados: período fechado ou turma arquivada.</div>}
            <section className="panel course-panel"><h2>Lançamentos por aluno</h2><p>Nota ausente é uma pendência, não zero. Recarregue a página antes de corrigir uma nota alterada por outra sessão.</p>
                {editavel && <details className="course-outline"><summary>Editar avaliação em rascunho</summary><form className="course-form" method="post" action={urlFor('academico.configurar_avaliacao', { avaliacao_id: avaliacao.id })}><Token /><input type="hidden" name="acao" value="salvar" /><label>Título<input name="titulo" defaultValue={avaliacao.titulo} maxLength={150} required /></label><label>Peso<input type="number" name="peso" defaultValue={avaliacao.peso} min="0.01" max="100" step="0.01" required /></label><button className="button">Salvar avaliação</button></form><form method="post" action={urlFor('academico.configurar_avaliacao', { avaliacao_id: avaliacao.id })}><Token /><input type="hidden" name="acao" value="remover" /><button className="button">Remover avaliação vazia</button></form></details>}
                {d.alunos.length ? d.alunos.map((aluno) => {
                    const nota = d.notas[aluno.id];
                    return (
                        <details key={aluno.id} className="course-outline" open><summary>{aluno.nome} · {aluno.matricula} · {nota ? nota.valor : 'Pendente'}</summary>
                            {g.sessao.user_role === 'professor' && !periodo.fechado && ativa
                                ? <form className="course-form" method="post" action={urlFor('academico.lancar', { avaliacao_id: avaliacao.id, aluno_id: aluno.id })}><Token /><input type="hidden" name="versao" value={nota ? nota.versao : 0} /><label>Nota de {aluno.nome}<input type="number" name="valor" min="0" max="10" step="0.01" defaultValue={nota ? nota.valor : ''} required /></label><label>Observação<textarea name="observacao" maxLength={255} defaultValue={nota ? nota.observacao : ''}></textarea></label><button className="button button-primary">Salvar nota</button></form>
                                : <p>{nota ? nota.observacao : 'Sem lançamento.'}</p>}
                        </details>
                    );
                }) : <p>Nenhum aluno matriculado nesta turma.</p>}
                {editavel && <form method="post" action={urlFor('academico.publicar', { avaliacao_id: avaliacao.id })}><Token /><button className="button button-primary">Publicar notas para os alunos</button></form>}
            </section>
        </GestaoBase>
    );
}
