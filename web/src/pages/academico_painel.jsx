import GestaoBase, { bodyGestao, tituloGestao } from '../components/GestaoBase';
import Token from '../components/Token';
import { urlFor } from '../core/urls';

export const bodyClass = bodyGestao();
export const titulo = tituloGestao('Diário e avaliações');

export default function AcademicoPainel({ d, g }) {
    const admin = ['admin', 'superadmin'].includes(g.sessao.user_role);
    return (
        <GestaoBase titulo="Diário e avaliações" error={d.error}>
            <section className="page-heading"><div><span className="eyebrow">VIDA ACADÊMICA</span><h1>Diário e avaliações</h1><p>Notas e médias organizadas por turma, ano e período. Os registros anteriores são preservados.</p></div></section>
            {admin && <>
                <div className="course-actions"><a className="button button-primary" href={urlFor('academico.lista_reconciliacao')}>Revisar atribuições antigas</a><a className="button" href={urlFor('academico.notas_antigas')}>Vincular notas anteriores</a></div>
                <section className="panel course-panel"><h2>Criar período letivo</h2><form method="post" action={urlFor('academico.criar_periodo')} className="course-form"><Token /><label>Turma e ano<select name="turma_id" required><option value="">Selecione</option>{d.turmas.map((t) => <option key={t.id} value={t.id}>{t.nome} · {t.ano_letivo}</option>)}</select></label><label>Nome do período<input name="nome" placeholder="1º bimestre, trimestre ou semestre" maxLength={80} required /></label><label>Ordem<input type="number" name="ordem" min="1" max="24" required /></label><label>Média de referência da instituição<input type="number" name="media_referencia" min="0" max="10" step="0.01" defaultValue="6" required /></label><p>A média de referência é configurável. A situação acadêmica completa também pode depender de frequência, recuperação e regras da instituição.</p><button className="button button-primary">Criar período</button></form></section>
            </>}
            {d.vinculos.length ? d.vinculos.map(([vinculo, turma, disciplina]) => {
                const periodos = d.periodos.filter((p) => p.turma_id === turma.id);
                return (
                    <section key={vinculo.id} className="panel course-panel"><span className="eyebrow">{turma.ano_letivo} · {turma.nome}</span><h2>{disciplina.nome}</h2>
                        {periodos.length ? periodos.map((p) => {
                            const avaliacoes = d.avaliacoes.filter((a) => a.turma_disciplina_id === vinculo.id && a.periodo_id === p.id);
                            return (
                                <details key={p.id} className="course-outline" open><summary>{p.nome} · {p.fechado ? 'Fechado' : 'Aberto'}</summary>
                                    {avaliacoes.length ? avaliacoes.map((a) => <a key={a.id} href={urlFor('academico.diario', { avaliacao_id: a.id })}>{a.titulo} · peso {a.peso} · {a.publicada ? 'Publicada' : 'Rascunho'}</a>) : <p>Nenhuma avaliação neste período.</p>}
                                    {!p.fechado && <details><summary>Nova avaliação</summary><form className="course-form" method="post" action={urlFor('academico.criar_avaliacao')}><Token /><input type="hidden" name="turma_disciplina_id" value={vinculo.id} /><input type="hidden" name="periodo_id" value={p.id} /><label>Título<input name="titulo" maxLength={150} required /></label><label>Peso<input name="peso" type="number" min="0.01" max="100" step="0.01" defaultValue="1" required /></label><button className="button button-primary">Criar avaliação</button></form></details>}
                                    {admin && <details><summary>{p.fechado ? 'Reabrir período' : 'Fechar período'}</summary><form className="course-form" method="post" action={urlFor('academico.estado_periodo', { periodo_id: p.id })}><Token /><input type="hidden" name="estado" value={p.fechado ? 'aberto' : 'fechado'} /><label>Motivo<input name="motivo" minLength={5} maxLength={500} required /></label><button className="button">Confirmar</button></form></details>}
                                </details>
                            );
                        }) : <p>A secretaria ainda precisa cadastrar os períodos desta turma.</p>}
                    </section>
                );
            }) : <section className="panel course-panel"><h2>Nenhuma atribuição disponível</h2><p>A secretaria precisa confirmar professor, disciplina e turma na revisão de atribuições.</p></section>}
        </GestaoBase>
    );
}
