import { Fragment } from 'react';
import GestaoBase, { bodyGestao } from '../components/GestaoBase';
import Token from '../components/Token';
import { urlFor } from '../core/urls';

export const bodyClass = bodyGestao();
export const titulo = (d, g) => `${d.curso.titulo} | ${g.escola?.nome ?? 'Educa Fast'}`;

export default function CursoAprender({ d }) {
    const { curso, oferta, atual, anterior, proxima, concluidas } = d;
    const feita = (id) => concluidas.includes(id);
    return (
        <GestaoBase titulo={curso.titulo} error={d.error}>
            <a href={urlFor('cursos.biblioteca')}>← Meus cursos</a>
            <section className="page-heading"><div><span className="eyebrow">SEU APRENDIZADO</span><h1>{curso.titulo}</h1><p>{concluidas.length} de {d.total} aulas concluídas · {d.progresso}%</p><progress value={d.progresso} max="100" aria-label="Progresso do curso"></progress></div></section>
            <div className="course-layout"><aside className="panel course-panel" aria-label="Conteúdo do curso">
                {d.estrutura.map((item) => <details key={item.capitulo.id} className="course-outline" open><summary>{item.capitulo.titulo}</summary>{item.temas.map((grupo) => <Fragment key={grupo.tema.id}><h3>{grupo.tema.titulo}</h3>{grupo.aulas.map((aula) => <a key={aula.id} href={urlFor('cursos.aprender', { oferta_id: oferta.id, aula: aula.id })} aria-current={atual && aula.id === atual.id ? 'page' : undefined}>{feita(aula.id) ? '✓ ' : ''}{aula.titulo}{feita(aula.id) && <span className="course-meta"> — Concluída</span>}</a>)}</Fragment>)}</details>)}</aside>
                <section className="panel course-panel">{atual ? <><h2>{atual.titulo}</h2><iframe className="course-player" src={`https://www.youtube-nocookie.com/embed/${atual.video_id}`} title={`Videoaula: ${atual.titulo}`} allowFullScreen referrerPolicy="strict-origin-when-cross-origin"></iframe><p className="course-description">{atual.descricao}</p><p className="course-meta">O vídeo é fornecido pelo YouTube. A conclusão é uma confirmação sua de que terminou a aula.</p><form method="post" action={urlFor('cursos.concluir', { oferta_id: oferta.id, aula_id: atual.id })}><Token /><button className="button button-primary">{feita(atual.id) ? 'Aula concluída ✓' : 'Marcar aula como concluída'}</button></form><nav className="course-actions" aria-label="Navegação entre aulas">{anterior && <a className="button" href={urlFor('cursos.aprender', { oferta_id: oferta.id, aula: anterior.id })}>← Aula anterior</a>}{proxima && <a className="button" href={urlFor('cursos.aprender', { oferta_id: oferta.id, aula: proxima.id })}>Próxima aula →</a>}</nav></> : <p>Nenhuma aula disponível.</p>}</section></div>
        </GestaoBase>
    );
}
