import React, { Fragment } from 'react';
import { Link } from 'react-router-dom';
import { LogoutButton } from '../components/Navigation';
import { MutationForm } from '../components/MutationForm';
import { TabButton, TabPanel } from '../components/Tabs';
import { AlunoComunicados } from '../components/AlunoComunicados';
import { GradeSemanal } from '../components/GradeSemanal';
import { truthy } from '../utils';

export default function AlunoPainel({ data }) {
    const { aluno = {}, disciplinas = [], horarios = [], documentos = [], notas = [], solicitacoes_documentos = [] } = data;
    return <>

    <aside className="w-72 glass-sidebar h-screen sticky top-0 flex flex-col p-6">
        <div className="mb-10 text-center">
            <h2 className="text-xl font-bold tracking-tighter text-cyan-400">SECRETARIA DF</h2>
            <p className="text-[10px] text-gray-500 uppercase tracking-widest">Portal do Aluno</p>
        </div>

        <nav className="flex-1 space-y-2">
            <div className="text-[10px] font-bold text-gray-500 mb-2 ml-4">MINHA ÁREA</div>
            <TabButton type="button" group="aluno" value="disciplinas" as="button" className="aluno-nav-link w-full flex items-center px-4 py-3 rounded-xl">
                Disciplinas
            </TabButton>
            <TabButton type="button" group="aluno" value="notas" as="button" className="aluno-nav-link w-full flex items-center px-4 py-3 rounded-xl hover:bg-white/5 transition-all hover:text-white">
                Notas
            </TabButton>
            <TabButton type="button" group="aluno" value="documentos" as="button" className="aluno-nav-link w-full flex items-center px-4 py-3 rounded-xl hover:bg-white/5 transition-all hover:text-white">
                Documentos
            </TabButton>
            <TabButton group="aluno" value="comunicados" className="aluno-nav-link w-full flex items-center px-4 py-3 rounded-xl">Comunicados</TabButton>
        </nav>

        <div className="mt-auto pt-6 border-t border-white/10">
            <LogoutButton  className="flex items-center px-4 py-3 rounded-xl text-red-400 hover:bg-red-500/10 transition-all">
                Sair do Sistema
            </LogoutButton>
        </div>
    </aside>

    <main className="flex-1 p-10 overflow-y-auto">
        <header className="flex justify-between items-center mb-10">
            <div>
                <h1 className="text-3xl font-bold">Olá, {aluno.nome}!</h1>
                <p className="text-gray-400">Matrícula {aluno.matricula} · {aluno.curso}</p>
            </div>
            <div className="flex items-center gap-4">
                <div className="text-right">
                    <p className="text-sm font-bold">{aluno.email}</p>
                    <p className="text-[10px] text-cyan-400">{aluno.status}</p>
                </div>
                {truthy(aluno.foto_perfil) ? <> 
                <img src={`/arquivos/perfil/${encodeURIComponent(aluno.foto_perfil)}`} alt={`Foto de ${aluno.nome}`} className="w-12 h-12 rounded-full border-2 border-white/20 object-cover" />
                 </> : <> 
                <div className="w-12 h-12 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 border-2 border-white/20"></div>
                 </>}
            </div>
        </header>

        <TabPanel id="disciplinas" group="aluno" value="disciplinas" as="section" className="mb-10">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold">Disciplinas</h2>
                <span className="text-sm text-gray-400">Grade semanal · segunda a sábado</span>
            </div>
            <GradeSemanal disciplinas={disciplinas} horarios={horarios} />
        </TabPanel>

        <TabPanel group="aluno" value="comunicados" as="section"><AlunoComunicados /></TabPanel>

        <TabPanel id="notas" group="aluno" value="notas" as="section" className="glass-card aluno-card rounded-[32px] p-8 mb-10">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold">Notas</h2>
                <span className="text-sm text-gray-400">Lançamentos disponíveis</span>
            </div>

            <div className="aluno-table-wrapper">
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
                        {notas.length ? <>{notas.map((nota, index27) => <Fragment key={nota?.id ?? index27}>
                        <tr className="border-t border-white/5">
                            <td className="py-4 font-medium text-white">{nota.disciplina}</td>
                            <td className="py-4 text-cyan-400 font-bold">{nota.nota}</td>
                            <td className="py-4 text-gray-400">{nota.observacao}</td>
                            <td className="py-4 text-gray-400">{nota.data}</td>
                        </tr>
                        </Fragment>)}</> : <>
                        <tr className="border-t border-white/5">
                            <td className="py-6 text-gray-400" colSpan="4">Nenhuma nota lançada até o momento.</td>
                        </tr>
                        </>}
                    </tbody>
                </table>
            </div>
        </TabPanel>

        <TabPanel id="documentos" group="aluno" value="documentos" as="section" className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_380px]">
            <div className="glass-card aluno-card rounded-[32px] p-8">
                <h2 className="text-xl font-bold">Documentos Solicitados</h2>
                <p className="mt-1 text-sm text-gray-400">Envie apenas os arquivos pedidos pela secretaria.</p>

                <div className="aluno-document-list mt-6 space-y-4">
                    {solicitacoes_documentos.length ? <>{solicitacoes_documentos.map((solicitacao, index28) => <Fragment key={solicitacao?.id ?? index28}>
                    <article className="aluno-request-item">
                        <div>
                            <h3>{solicitacao.titulo}</h3>
                            <p>{solicitacao.mensagem}</p>
                            <span>{solicitacao.data}</span>
                        </div>
                        <strong className={`aluno-request-status aluno-request-status-${solicitacao.status}`}>{solicitacao.status_label}</strong>
                        {truthy(solicitacao.status !== "enviado") ? <> 
                        <MutationForm modalTitle="Enviar documento solicitado" modalLabel="Enviar documento" action={"/api/aluno/documentos/upload"} method="post" encType="multipart/form-data" className="aluno-request-upload">
                            <input type="hidden" name="solicitacao_id" value={solicitacao.id} />
                            <input name="arquivo" type="file" required className="aluno-file" />
                            <button data-ui-action className="aluno-submit compact">Enviar</button>
                        </MutationForm>
                         </> : <>  </>}
                    </article>
                    </Fragment>)}</> : <>
                    <div className="aluno-doc-item">
                        <div>
                            <h3>Nenhum documento solicitado</h3>
                            <p>Quando a secretaria pedir um documento, ele aparecerá aqui.</p>
                        </div>
                    </div>
                    </>}
                </div>
            </div>

            <div className="glass-card aluno-card rounded-[32px] p-8">
                <h2 className="text-xl font-bold">Arquivos Enviados</h2>
                <p className="mt-1 text-sm text-gray-400">Histórico dos documentos encaminhados.</p>

                <div className="aluno-document-list mt-6 space-y-4">
                    {documentos.length ? <>{documentos.map((documento, index29) => <Fragment key={documento?.id ?? index29}>
                    <article className="aluno-doc-item">
                        <div>
                            <h3>{documento.titulo}</h3>
                            <p>{documento.data}</p>
                        </div>
                        <a data-ui-action href={`/arquivos/download/${encodeURIComponent(documento.arquivo)}`}>Baixar</a>
                    </article>
                    </Fragment>)}</> : <>
                    <div className="aluno-doc-item">
                        <div>
                            <h3>Nenhum documento enviado</h3>
                            <p>Os arquivos enviados aparecerão aqui.</p>
                        </div>
                    </div>
                    </>}
                </div>
            </div>
        </TabPanel>
    </main>
    </>;
}
