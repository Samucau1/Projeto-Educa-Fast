import GestaoBase, { bodyGestao } from '../components/GestaoBase';
import Token from '../components/Token';
import { urlFor } from '../core/urls';

export const bodyClass = bodyGestao();
export const titulo = (d, g) => `${d.curso.titulo} | ${g.escola?.nome ?? 'Educa Fast'}`;

const MOVER = [['subir', '↑ Subir'], ['descer', '↓ Descer'], ['remover', 'Remover']];

function Controles({ curso, tipo, row }) {
    const acao = urlFor('cursos.editar_estrutura', { curso_id: curso.id });
    return <>
        <div className="course-actions">{MOVER.map(([op, rotulo]) => <form key={op} method="post" action={acao}><Token /><input type="hidden" name="tipo" value={tipo} /><input type="hidden" name="id" value={row.id} /><input type="hidden" name="acao" value={op} /><button className="button" aria-label={`${rotulo} ${row.titulo}`}>{rotulo}</button></form>)}</div>
        <details><summary>Editar {tipo}</summary><form className="course-form" method="post" action={acao}><Token /><input type="hidden" name="tipo" value={tipo} /><input type="hidden" name="id" value={row.id} /><input type="hidden" name="acao" value="editar" /><label>Título<input name="titulo" defaultValue={row.titulo} maxLength={150} required /></label>{tipo === 'aula' && <><label>Vídeo do YouTube<input name="video" defaultValue={row.video_id} required /></label><label>Descrição<textarea name="descricao" maxLength={10000} defaultValue={row.descricao}></textarea></label></>}<button className="button">Salvar</button></form></details>
    </>;
}

function Adicionar({ curso, tipo, paiId }) {
    return (
        <details className="course-outline"><summary>Adicionar {tipo}</summary><form className="course-form" method="post" action={urlFor('cursos.editar_estrutura', { curso_id: curso.id })}><Token /><input type="hidden" name="acao" value="adicionar" /><input type="hidden" name="tipo" value={tipo} />{paiId ? <input type="hidden" name="pai_id" value={paiId} /> : null}<label>Título<input name="titulo" maxLength={150} required /></label>{tipo === 'aula' && <><label>Vídeo do YouTube<input name="video" placeholder="https://www.youtube.com/watch?v=…" required /></label><label>Descrição<textarea name="descricao" maxLength={10000}></textarea></label></>}<button className="button button-primary">Adicionar</button></form></details>
    );
}

export default function CursoEditor({ d, g }) {
    const curso = d.curso;
    const rascunho = curso.estado === 'rascunho';
    const admin = ['admin', 'superadmin'].includes(g.sessao.user_role);
    return (
        <GestaoBase titulo={curso.titulo} error={d.error}>
            <a href={urlFor('cursos.biblioteca')}>← Biblioteca de cursos</a>
            <section className="page-heading"><div><span className="eyebrow">{curso.estado} · CURSO #{curso.id}</span><h1>{curso.titulo}</h1><p>{curso.descricao}</p></div></section>
            <section className="panel course-panel"><h2>Material que acompanha sua trajetória</h2><p>Libere este mesmo curso em várias turmas e anos. Após a publicação, o conteúdo é preservado. Duplique para preparar uma nova edição sem alterar as turmas anteriores.</p>
                <div className="course-actions"><form method="post" action={urlFor('cursos.duplicar', { curso_id: curso.id })}><Token /><button className="button button-primary">Duplicar para nova edição</button></form>
                    {admin && <>{rascunho && <form method="post" action={urlFor('cursos.estado', { curso_id: curso.id })}><Token /><input type="hidden" name="estado" value="publicado" /><button className="button button-primary">Revisar e publicar</button></form>}{curso.estado !== 'arquivado' && <form method="post" action={urlFor('cursos.estado', { curso_id: curso.id })}><Token /><input type="hidden" name="estado" value="arquivado" /><button className="button">Arquivar e suspender acessos</button></form>}</>}</div>
                {rascunho && <details><summary>Editar apresentação</summary><form method="post" className="course-form" action={urlFor('cursos.editar_estrutura', { curso_id: curso.id })}><Token /><input type="hidden" name="acao" value="curso" /><label>Título<input name="titulo" defaultValue={curso.titulo} maxLength={150} required /></label><label>Descrição<textarea name="descricao" maxLength={10000} defaultValue={curso.descricao}></textarea></label><button className="button">Salvar apresentação</button></form></details>}
            </section>
            <section className="panel course-panel"><h2>Capítulos, temas e videoaulas</h2>
                {d.estrutura.length ? d.estrutura.map((item) => (
                    <section key={item.capitulo.id} className="course-outline"><h3>{item.capitulo.posicao}. {item.capitulo.titulo}</h3>{rascunho && <Controles curso={curso} tipo="capitulo" row={item.capitulo} />}
                        {item.temas.map((grupo) => (
                            <section key={grupo.tema.id} className="course-outline"><h3>{grupo.tema.titulo}</h3>{rascunho && <Controles curso={curso} tipo="tema" row={grupo.tema} />}
                                {grupo.aulas.map((aula) => <details key={aula.id} className="course-outline"><summary>{aula.titulo}</summary><p className="course-description">{aula.descricao}</p><iframe className="course-player" src={`https://www.youtube-nocookie.com/embed/${aula.video_id}`} title={`Prévia: ${aula.titulo}`} loading="lazy" allowFullScreen referrerPolicy="strict-origin-when-cross-origin"></iframe>{rascunho && <Controles curso={curso} tipo="aula" row={aula} />}</details>)}
                                {rascunho && <Adicionar curso={curso} tipo="aula" paiId={grupo.tema.id} />}
                            </section>
                        ))}
                        {rascunho && <Adicionar curso={curso} tipo="tema" paiId={item.capitulo.id} />}
                    </section>
                )) : <p>Nenhum capítulo ainda. Comece organizando o primeiro tema.</p>}
                {rascunho && <Adicionar curso={curso} tipo="capitulo" />}
            </section>
            <section className="panel course-panel"><h2>Turmas e anos que utilizam este curso</h2>
                {d.ofertas.length ? d.ofertas.map(([oferta, turma]) => <div key={oferta.id} className="course-actions"><span>{turma.nome} · {turma.ano_letivo} · {oferta.ativa ? 'Liberado' : 'Suspenso'}</span>{oferta.ativa && admin && <form method="post" action={urlFor('cursos.revogar_oferta', { oferta_id: oferta.id })}><Token /><button className="button">Suspender acesso</button></form>}</div>) : <p>Nenhuma turma vinculada.</p>}
                {admin && curso.estado === 'publicado' && <><form className="course-form" method="post" action={urlFor('cursos.ofertar', { curso_id: curso.id })}><Token /><label>Reutilizar na turma<select name="turma_id" required><option value="">Selecione</option>{d.turmas.map((turma) => <option key={turma.id} value={turma.id}>{turma.nome} · {turma.ano_letivo}</option>)}</select></label><button className="button button-primary">Liberar para a turma</button></form><p>A disciplina do curso precisa estar atribuída à turma.</p></>}
            </section>
        </GestaoBase>
    );
}
