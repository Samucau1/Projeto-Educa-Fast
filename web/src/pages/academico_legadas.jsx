import GestaoBase, { bodyGestao, tituloGestao } from '../components/GestaoBase';
import Token from '../components/Token';
import { urlFor } from '../core/urls';

export const bodyClass = bodyGestao();
export const titulo = tituloGestao('Histórico de notas');

export default function AcademicoLegadas({ d }) {
    return (
        <GestaoBase titulo="Histórico de notas" error={d.error}>
            <section className="page-heading"><div><span className="eyebrow">PRESERVAÇÃO DO HISTÓRICO</span><h1>Vincular notas anteriores</h1><p>Confirme o destino de cada nota. A origem é preservada e só pode ser vinculada uma vez. Nenhum lançamento existente é sobrescrito.</p></div></section>
            {d.notas.length ? d.notas.map(([nota, aluno, disciplina]) => {
                const destinos = d.destinos[nota.id];
                return (
                    <section key={nota.id} className="panel course-panel"><h2>{aluno.nome} — {disciplina.nome}</h2><p>Nota anterior: {nota.nota} · {nota.observacao || ''}</p>
                        {d.migradas.includes(nota.id) ? <p>Vínculo histórico já confirmado.</p>
                            : destinos && destinos.length ? <form className="course-form" method="post" action={urlFor('academico.vincular_nota', { nota_id: nota.id })}><Token /><input type="hidden" name="valor_confirmado" value={nota.nota} /><label>Destino confirmado<select name="avaliacao_id" required><option value="">Selecione a turma, o período e a avaliação corretos</option>{destinos.map(([a, p, t]) => <option key={a.id} value={a.id}>{t.nome} · {t.ano_letivo} · {p.nome} · {a.titulo}</option>)}</select></label><button className="button button-primary">Confirmar vínculo desta nota</button></form>
                                : <p>Cadastre uma avaliação em rascunho na mesma disciplina e em uma turma com matrícula deste aluno antes de confirmar o vínculo.</p>}
                    </section>
                );
            }) : <section className="panel course-panel"><p>Nenhuma nota anterior para revisar.</p></section>}
        </GestaoBase>
    );
}
