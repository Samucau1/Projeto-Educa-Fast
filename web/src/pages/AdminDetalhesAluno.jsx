import React, { Fragment } from 'react';

import { AdminSidebar } from '../components/Navigation';
import { MutationForm } from '../components/MutationForm';
import { TabButton, TabPanel } from '../components/Tabs';
import { truthy } from '../utils';

export default function AdminDetalhesAluno({ data }) {
    const { aluno = {}, documentos = [], solicitacoes_documentos = [] } = data;
    return <>

    <AdminSidebar />

    <main className="flex-1 p-10 overflow-y-auto">
        <header className="flex justify-between items-center mb-10">
            <div>
                <h1 className="text-3xl font-bold">Detalhes do Aluno</h1>
                <p className="text-gray-400">Acompanhe documentos, histórico e evolução acadêmica.</p>
            </div>
            <div className="flex items-center gap-4">
                <div className="text-right">
                    <p className="text-sm font-bold">Admin Secretaria</p>
                    <p className="text-[10px] text-cyan-400">Online agora</p>
                </div>
                <div className="w-12 h-12 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 border-2 border-white/20"></div>
            </div>
        </header>

        <div className="grid grid-cols-1 xl:grid-cols-[minmax(300px,0.9fr)_minmax(0,1.6fr)] gap-6">
            <section className="glass-card detalhes-card p-8 rounded-[32px] text-center">
                {truthy(aluno.foto_perfil) ? <> 
                <img src={`/arquivos/perfil/${encodeURIComponent(aluno.foto_perfil)}`} alt={`Foto de ${aluno.nome}`} className="w-32 h-32 rounded-full mx-auto mb-4 border-4 border-white/10 object-cover" />
                 </> : <> 
                <div className="w-32 h-32 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full mx-auto mb-4 border-4 border-white/10"></div>
                 </>}
                <h2 className="text-2xl font-bold">{aluno.nome}</h2>
                <p className="text-cyan-400">Matrícula: {aluno.matricula}</p>
                <p className="text-gray-400 text-sm mt-2">Nasc: {aluno.data_nascimento}</p>
                <p className="text-gray-400 text-sm mt-1">{aluno.curso}</p>
                <p className="text-gray-500 text-xs mt-1">{aluno.email}</p>

                <MutationForm modalTitle="Editar cadastro" modalLabel="Editar dados" action={`/api/admin/alunos/${encodeURIComponent(aluno.id)}/editar`} method="post" encType="multipart/form-data" className="aluno-edit-form">
                    <h3>Editar Dados</h3>
                    <label>
                        <span>Foto de Perfil</span>
                        <input name="foto_perfil" type="file" accept="image/png,image/jpeg" />
                    </label>
                    <label>
                        <span>Nome</span>
                        <input name="nome" type="text" defaultValue={aluno.nome} required />
                    </label>
                    <label>
                        <span>E-mail</span>
                        <input name="email" type="email" defaultValue={aluno.email} required />
                    </label>
                    <div className="aluno-edit-grid">
                        <label>
                            <span>CPF</span>
                            <input name="cpf" type="text" defaultValue={aluno.cpf_value} />
                        </label>
                        <label>
                            <span>Matrícula</span>
                            <input name="matricula" type="text" defaultValue={aluno.matricula} required />
                        </label>
                    </div>
                    <label>
                        <span>Curso/Série</span>
                        <input name="curso_serie" type="text" defaultValue={aluno.curso_value} />
                    </label>
                    <div className="aluno-edit-grid">
                        <label>
                            <span>Status</span>
                            <select name="status_matricula" defaultValue={aluno.status_value}>
                                <option value="">Não informado</option>
                                <option value="Ativo">Ativo</option>
                                <option value="Pendente">Pendente</option>
                                <option value="Inativo">Inativo</option>
                            </select>
                        </label>
                        <label>
                            <span>Nascimento</span>
                            <input name="data_nascimento" type="date" defaultValue={aluno.data_nascimento_value} />
                        </label>
                    </div>
                    <button data-ui-action className="ui-button">Salvar Alterações</button>
                </MutationForm>
            </section>

            <section className="glass-card detalhes-card p-8 rounded-[32px]">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-bold">Documentos do Aluno</h3>
                    <span className="text-sm text-cyan-400">Solicitações e arquivos</span>
                </div>

                <div className="flex gap-4 border-b border-white/10 mb-6">
                    <TabButton type="button" className="documento-tab pb-2" group="documento" value="solicitacoes" as="button">Solicitações</TabButton>
                    <TabButton type="button" className="documento-tab pb-2" group="documento" value="enviados" as="button">Enviados</TabButton>
                </div>

                <TabPanel group="documento" value="solicitacoes" as="div">
                    <div className="button-actions detalhes-document-actions flex flex-wrap items-center gap-4">
                    <MutationForm modalTitle="Solicitar documento" modalLabel="Solicitar documento" action={`/api/admin/alunos/${encodeURIComponent(aluno.id)}/documentos/solicitar`} method="post" className="documento-request-form">
                        <label>
                            <span>Documento solicitado</span>
                            <input name="titulo" type="text" placeholder="Ex: Comprovante de residência" required />
                        </label>
                        <label>
                            <span>Orientação para o aluno</span>
                            <textarea name="mensagem" placeholder="Informe prazo, formato ou observações importantes."></textarea>
                        </label>
                        <button data-ui-action className="ui-button">Disparar solicitação</button>
                    </MutationForm>

                    <MutationForm modalTitle="Enviar arquivo" modalLabel="Enviar arquivo" action={"/api/arquivos/upload"} method="post" encType="multipart/form-data" className="documento-request-form mt-8">
                        <input type="hidden" name="aluno_id" value={aluno.id} />
                        <input type="hidden" name="redirect_to" value={`/admin/alunos/${encodeURIComponent(aluno.id)}`} />
                        <label>
                            <span>Documentos do aluno</span>
                            <input name="titulo" type="text" placeholder="Ex: Histórico escolar" required />
                        </label>
                        <label>
                            <span>Arquivo</span>
                            <input name="arquivo" type="file" required />
                        </label>
                        <button data-ui-action className="ui-button">Enviar Arquivo</button>
                    </MutationForm>
                    </div>

                    <div className="mt-8">
                        <h4 className="mb-4 text-sm font-bold uppercase tracking-wider text-gray-400">Solicitações enviadas</h4>
                        {solicitacoes_documentos.length ? <>{solicitacoes_documentos.map((solicitacao, index4) => <Fragment key={solicitacao?.id ?? index4}>
                        <div className="documento-request-item">
                            <div>
                                <span className="block text-white">{solicitacao.titulo}</span>
                                <span className="text-xs text-gray-500">{solicitacao.mensagem}</span>
                            </div>
                            <div className="text-right">
                                <span className={`documento-status documento-status-${solicitacao.status}`}>{solicitacao.status_label}</span>
                                <span className="block text-xs text-gray-500 mt-2">{solicitacao.data}</span>
                            </div>
                        </div>
                        </Fragment>)}</> : <>
                        <div className="bg-white/5 p-4 rounded-xl mb-4 border border-white/5 text-gray-400">
                            Nenhuma solicitação enviada para este aluno.
                        </div>
                        </>}
                    </div>
                </TabPanel>

                <TabPanel className="" group="documento" value="enviados" as="div">
                    <h4 className="mb-4 text-sm font-bold uppercase tracking-wider text-gray-400">Documentos do aluno</h4>
                    {documentos.length ? <>{documentos.map((documento, index5) => <Fragment key={documento?.id ?? index5}>
                        <div className="bg-white/5 p-4 rounded-xl mb-4 flex justify-between border border-white/5">
                            <div>
                                <span className="block text-white">{documento.titulo}</span>
                                <span className="text-xs text-gray-500">{documento.data_envio}</span>
                            </div>
                            <a data-ui-action href={`/arquivos/download/${encodeURIComponent(documento.arquivo)}`} className="ui-button">Baixar</a>
                        </div>
                    </Fragment>)}</> : <>
                        <div className="bg-white/5 p-4 rounded-xl mb-4 border border-white/5 text-gray-400">
                            Nenhum documento enviado para este aluno.
                        </div>
                    </>}
                </TabPanel>
            </section>
        </div>
    </main>
    </>;
}
