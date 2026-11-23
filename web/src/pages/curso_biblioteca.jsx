import GestaoBase, { bodyGestao, tituloGestao } from '../components/GestaoBase';
import Token from '../components/Token';
import { urlFor } from '../core/urls';

export const bodyClass = bodyGestao();
export const titulo = tituloGestao('Cursos');

export default function CursoBiblioteca({ d, g }) {
    const role = g.sessao.user_role;
    const cursos = d.cursos || [];
    const cards = d.cards || [];
    return (
        <GestaoBase titulo="Cursos" error={d.error}>
            <section className="page-heading"><div><span className="eyebrow">APRENDIZAGEM</span><h1>{role === 'aluno' ? 'Meus cursos' : 'Biblioteca de cursos'}</h1><p>Material organizado para aprender, ensinar e reutilizar em diferentes turmas e anos.</p></div></section>
            {role !== 'aluno' && (
                <section className="panel course-panel"><h2>Novo curso</h2>
                    <form method="post" action={urlFor('cursos.criar')} className="course-form">
                        <Token />
                        <label>Título<input name="titulo" maxLength={150} required /></label>
                        <label>Disciplina<select name="disciplina_id" required><option value="">Selecione</option>{(d.disciplinas || []).map((disc) => <option key={disc.id} value={disc.id}>{disc.nome}</option>)}</select></label>
                        {(role === 'admin' || role === 'superadmin') && <label>Professor responsável<select name="professor_id" required><option value="">Selecione</option>{(d.professores || []).map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}</select></label>}
                        <label>Descrição<textarea name="descricao" maxLength={10000}></textarea></label>
                        <button className="button button-primary">Criar rascunho</button>
                    </form><p>O responsável precisa estar vinculado à disciplina. A administração revisa e publica o conteúdo.</p></section>
            )}
            <div className="course-grid">
                {cursos.map((curso) => <article key={curso.id} className="panel course-panel"><span className="eyebrow">{curso.estado}</span><h2>{curso.titulo}</h2><p>{curso.descricao}</p><a className="button button-primary" href={urlFor('cursos.editor', { curso_id: curso.id })}>Abrir curso</a></article>)}
                {cards.map((card) => <article key={card.oferta.id} className="panel course-panel"><span className="eyebrow">{card.turma.nome} · {card.turma.ano_letivo}</span><h2>{card.curso.titulo}</h2><p>{card.curso.descricao}</p><progress value={card.progresso} max="100" aria-label="Progresso do curso"></progress><p>{card.progresso}% concluído</p><a className="button button-primary" href={urlFor('cursos.aprender', { oferta_id: card.oferta.id })}>Continuar aprendendo</a></article>)}
                {!cursos.length && !cards.length && <section className="panel course-panel"><h2>Nenhum curso disponível</h2><p>{role === 'aluno' ? 'Os cursos liberados para suas turmas aparecerão aqui.' : 'Crie o primeiro curso para organizar seu material.'}</p></section>}
            </div>
        </GestaoBase>
    );
}
