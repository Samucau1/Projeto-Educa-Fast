import ShellPagina, { headPainel } from '../components/ShellPagina';
import Token from '../components/Token';
import { useAbas } from '../components/abas';
import { TabelaRolagem } from '../components/tabelas';
import { urlFor } from '../core/urls';
import { j } from '../core/formatos';

export const head = headPainel('aluno_painel.css');
export const bodyClass = 'app-page';
export const titulo = () => 'Área do Aluno | Educa Fast';

export default function AlunoPainel({ d }) {
    useAbas();
    const aluno = d.aluno;
    return (
        <ShellPagina id="aluno-painel" titulo="Área do aluno">
            <header className="flex justify-between items-center mb-10">
                <div>
                    <span className="eyebrow">MINHA ESCOLA</span>
                    <h1 className="text-3xl font-bold">Olá, {j(aluno.nome)}!</h1>
                    <p className="text-gray-400">Matrícula {j(aluno.matricula)} · {j(aluno.curso)}</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="text-right">
                        <p className="text-sm font-bold">{j(aluno.email)}</p>
                        <p className="text-[10px] text-cyan-400">{j(aluno.status)}</p>
                    </div>
                    {aluno.foto_perfil
                        ? <img src={urlFor('document.perfil_arquivo', { filename: aluno.foto_perfil })} alt={`Foto de ${aluno.nome}`} className="w-12 h-12 rounded-full border-2 border-white/20 object-cover" />
                        : <div className="w-12 h-12 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 border-2 border-white/20"></div>}
                </div>
            </header>
            <section id="disciplinas" data-aluno-panel="disciplinas" className="mb-10">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-bold">Disciplinas</h2>
                    <span className="text-sm text-gray-400">Vínculos cadastrados</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {d.disciplinas.length ? d.disciplinas.map((disciplina) => (
                        <article key={disciplina.id} className="glass-card aluno-card aluno-discipline-card rounded-3xl p-5">
                            <a href={urlFor('aluno.disciplina_detail', { disciplina_id: disciplina.id })} className="aluno-discipline-toggle">
                                <span>
                                    <strong>{j(disciplina.nome)}</strong>{' '}
                                    <small>Código: {j(disciplina.codigo)} · {j(disciplina.carga_horaria)}h</small>
                                </span>
                            </a>
                            <p className="mt-3 text-xs uppercase tracking-wider text-gray-500">Professor</p>
                            <p className="mt-1 text-sm text-gray-300">
                                {disciplina.professores && disciplina.professores.length ? disciplina.professores.join(', ') : 'Nenhum professor associado.'}
                            </p>
                        </article>
                    )) : (
                        <div className="glass-card aluno-card rounded-3xl p-5 md:col-span-2 xl:col-span-3">
                            <h3 className="font-bold text-cyan-400">Nenhuma disciplina associada</h3>
                            <p className="mt-3 text-sm leading-6 text-gray-300">As disciplinas aparecerão quando a administração vincular seu cadastro.</p>
                        </div>
                    )}
                </div>
            </section>
            <section id="notas" data-aluno-panel="notas" className="glass-card aluno-card rounded-[32px] p-8 mb-10 aluno-panel-hidden">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-bold">Notas</h2>
                    <a className="button button-primary" href={urlFor('academico.meu_boletim')}>Abrir boletim por turma e período</a>
                    <span className="text-sm text-gray-400">Lançamentos disponíveis</span>
                </div>
                <div className="aluno-table-wrapper">
                    <TabelaRolagem>
                        <table className="w-full text-left">
                            <thead>
                                <tr className="text-gray-500 text-xs uppercase tracking-wider">
                                    <th className="pb-4 font-medium">Disciplina</th>
                                    <th className="pb-4 font-medium">Nota</th>
                                    <th className="pb-4 font-medium">Observação</th>
                                    <th className="pb-4 font-medium">Data</th>
                                </tr>
                            </thead>
                            <tbody className="text-sm">
                                {d.notas.length ? d.notas.map((nota, i) => (
                                    <tr key={i} className="border-t border-white/5">
                                        <td className="py-4 font-medium text-white">{j(nota.disciplina)}</td>
                                        <td className="py-4 text-cyan-400 font-bold">{j(nota.nota)}</td>
                                        <td className="py-4 text-gray-400">{j(nota.observacao)}</td>
                                        <td className="py-4 text-gray-400">{j(nota.data)}</td>
                                    </tr>
                                )) : (
                                    <tr className="border-t border-white/5">
                                        <td className="py-6 text-gray-400" colSpan={4}>Nenhuma nota lançada até o momento.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </TabelaRolagem>
                </div>
            </section>
            <section id="documentos" data-aluno-panel="documentos" className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_380px] aluno-panel-hidden">
                <div className="glass-card aluno-card rounded-[32px] p-8">
                    <h2 className="text-xl font-bold">Documentos Solicitados</h2>
                    <p className="mt-1 text-sm text-gray-400">Envie apenas os arquivos pedidos pela secretaria.</p>
                    <div className="mt-6 space-y-4">
                        {d.solicitacoes_documentos.length ? d.solicitacoes_documentos.map((solicitacao) => (
                            <article key={solicitacao.id} className="aluno-request-item">
                                <div>
                                    <h3>{j(solicitacao.titulo)}</h3>
                                    <p>{j(solicitacao.mensagem)}</p>
                                    <span>{j(solicitacao.data)}</span>
                                </div>
                                <strong className={`aluno-request-status aluno-request-status-${solicitacao.status}`}>{j(solicitacao.status_label)}</strong>
                                {solicitacao.status !== 'enviado' && (
                                    <form action={urlFor('aluno.upload_documento_aluno')} method="post" encType="multipart/form-data" className="aluno-request-upload"><Token />
                                        <input type="hidden" name="solicitacao_id" value={solicitacao.id} />
                                        <input name="arquivo" type="file" required className="aluno-file" />{' '}
                                        <button className="aluno-submit compact">Enviar</button>
                                    </form>
                                )}
                            </article>
                        )) : (
                            <div className="aluno-doc-item">
                                <div>
                                    <h3>Nenhum documento solicitado</h3>
                                    <p>Quando a secretaria pedir um documento, ele aparecerá aqui.</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
                <div className="glass-card aluno-card rounded-[32px] p-8">
                    <h2 className="text-xl font-bold">Arquivos Enviados</h2>
                    <p className="mt-1 text-sm text-gray-400">Histórico dos documentos encaminhados.</p>
                    <div className="mt-6 space-y-4">
                        {d.documentos.length ? d.documentos.map((documento, i) => (
                            <article key={i} className="aluno-doc-item">
                                <div>
                                    <h3>{j(documento.titulo)}</h3>
                                    <p>{j(documento.data)}</p>
                                </div>
                                <a href={urlFor('document.download_arquivo', { filename: documento.arquivo })}>Baixar</a>
                            </article>
                        )) : (
                            <div className="aluno-doc-item">
                                <div>
                                    <h3>Nenhum documento enviado</h3>
                                    <p>Os arquivos enviados aparecerão aqui.</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </section>
        </ShellPagina>
    );
}
