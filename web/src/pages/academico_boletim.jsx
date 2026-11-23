import GestaoBase, { bodyGestao, tituloGestao } from '../components/GestaoBase';
import { TabelaRolagem } from '../components/tabelas';

export const bodyClass = bodyGestao();
export const titulo = tituloGestao('Boletim por período');

const ouPendente = (valor) => (valor !== null && valor !== undefined ? valor : 'Pendente');

export default function AcademicoBoletim({ d }) {
    return (
        <GestaoBase titulo="Boletim por período" error={d.error}>
            <section className="page-heading"><div><span className="eyebrow">HISTÓRICO ACADÊMICO</span><h1>Boletim de {d.aluno.nome}</h1><p>Notas publicadas por turma, ano e período. Seu histórico permanece disponível após o encerramento da turma.</p></div></section>
            {d.periodos.length ? d.periodos.map((item, i) => (
                <section key={i} className="panel course-panel"><span className="eyebrow">{item.turma} · {item.ano} · {item.periodo} · {item.fechado ? 'Fechado' : 'Em andamento'}</span><h2>{item.disciplina}</h2><div className="course-scroll"><TabelaRolagem><table className="course-table"><thead><tr><th>Avaliação</th><th>Peso</th><th>Nota</th><th>Observação</th></tr></thead><tbody>{item.avaliacoes.map((a, j) => <tr key={j}><td>{a.titulo}</td><td>{a.peso}</td><td>{ouPendente(a.nota)}</td><td>{a.observacao}</td></tr>)}</tbody></table></TabelaRolagem></div><p><strong>Média ponderada: {ouPendente(item.media)}</strong> · Referência: {item.media_referencia} · {item.situacao}</p><p className="course-meta">A média só é exibida após publicar e lançar todas as avaliações previstas. A situação aqui compara notas com a referência; a aprovação institucional pode incluir outros critérios.</p></section>
            )) : <section className="panel course-panel"><h2>Nenhuma avaliação publicada</h2><p>As avaliações e notas liberadas pelos professores aparecerão aqui.</p></section>}
            {d.legadas.length > 0 && <section className="panel course-panel"><h2>Registros anteriores sem período confirmado</h2><p>Estes registros foram preservados e não entram na média dos novos períodos. A secretaria pode revisar seu vínculo histórico.</p>{d.legadas.map((n) => <p key={n.id}>{n.disciplina} — {n.nota} · {n.observacao}</p>)}</section>}
            {d.anuais.length > 0 && <section className="panel course-panel"><h2>Resultado anual conforme as regras da escola</h2>{d.anuais.map((item, i) => <article key={i} className="course-outline"><span className="eyebrow">{item.turma} · {item.ano} · {item.politica}</span><h3>{item.disciplina}</h3><p>Média anual: <strong>{ouPendente(item.media)}</strong> · {item.situacao}</p><p className="course-meta">Pesos dos períodos: {item.pesos.join(' / ')}. O resultado fica pendente até fechar todos os períodos e concluir seus lançamentos. A comparação de notas não substitui os demais critérios institucionais.</p></article>)}</section>}
        </GestaoBase>
    );
}
