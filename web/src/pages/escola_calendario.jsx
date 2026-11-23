import GestaoBase, { bodyGestao, tituloGestao } from '../components/GestaoBase';
import { dataBR } from '../core/formatos';

export const bodyClass = bodyGestao();
export const titulo = tituloGestao('Calendário escolar');

export default function EscolaCalendario({ d }) {
    return (
        <GestaoBase titulo="Calendário escolar" error={d.error}>
            <section className="page-heading"><div><span className="eyebrow">ORGANIZAÇÃO DO ANO</span><h1>Calendário escolar</h1><p>Dias letivos planejados e datas cadastradas pela escola.</p></div></section>
            {d.calendarios.length ? d.calendarios.map((c) => {
                const eventos = d.eventos.filter((e) => e.calendario_id === c.id);
                return (
                    <section key={c.id} className="panel course-panel"><span className="eyebrow">{c.ano}</span><h2>{c.nome}</h2><p>{dataBR(c.inicio)} a {dataBR(c.fim)}</p><div className="school-summary"><p><strong>{d.resumos[c.id].dias_planejados}</strong>dias letivos planejados</p><p><strong>{d.resumos[c.id].meta}</strong>meta definida pela escola</p></div><div className="school-timeline">{eventos.length ? eventos.map((e) => <article key={e.id} className="course-outline"><span className="eyebrow">{dataBR(e.dia)} · {e.tipo}</span><h3>{e.titulo}</h3></article>) : <p>Nenhum evento cadastrado neste calendário.</p>}</div><p className="course-meta">A contagem é um planejamento de dias, não um registro de frequência ou comprovação de aulas realizadas.</p></section>
                );
            }) : <section className="panel course-panel"><p>A escola ainda não publicou um calendário.</p></section>}
        </GestaoBase>
    );
}
