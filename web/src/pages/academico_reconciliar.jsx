import GestaoBase, { bodyGestao, tituloGestao } from '../components/GestaoBase';
import Token from '../components/Token';
import { urlFor } from '../core/urls';

export const bodyClass = bodyGestao();
export const titulo = tituloGestao('Revisar atribuições');

export default function AcademicoReconciliar({ d }) {
    return (
        <GestaoBase titulo="Revisar atribuições" error={d.error}>
            <section className="page-heading"><div><span className="eyebrow">REVISÃO DA SECRETARIA</span><h1>Confirmar quem leciona cada matéria</h1><p>Os vínculos antigos são sugestões para revisão. Nenhuma combinação nova é concedida automaticamente.</p></div></section>
            {d.turma ? <>
                <a href={urlFor('academico.lista_reconciliacao')}>← Todas as turmas</a><section className="panel course-panel"><h2>{d.turma.nome} · {d.turma.ano_letivo}</h2><p>Marque somente as combinações confirmadas. Ao salvar, as combinações não marcadas ficam revogadas nesta turma. Notas e materiais existentes são preservados.</p><form method="post" className="course-form"><Token /><input type="hidden" name="revisao" value={d.revisao} />{d.pares.length ? d.pares.map(([professor, disciplina]) => {
                    const chave = `${professor.id}:${disciplina.id}`;
                    return <label key={chave} style={{ display: 'flex', alignItems: 'center' }}><input style={{ width: 'auto' }} type="checkbox" name="confirmadas" value={chave} defaultChecked={d.ativos.includes(chave)} />{professor.nome} — {disciplina.nome}</label>;
                }) : <p>Nenhuma combinação antiga encontrada. Cadastre atribuições na Gestão acadêmica.</p>}{d.pares.length > 0 && <button className="button button-primary">Confirmar atribuições revisadas</button>}</form></section>
            </> : <section className="panel course-panel">{d.turmas.length ? d.turmas.map((t) => <a key={t.id} className="course-outline" style={{ display: 'block' }} href={urlFor('academico.reconciliar', { turma_id: t.id })}>{t.nome} · {t.ano_letivo} · {d.estados[t.id] ? 'Gestão explícita' : 'Revisão pendente'}</a>) : <p>Nenhuma turma cadastrada.</p>}</section>}
        </GestaoBase>
    );
}
