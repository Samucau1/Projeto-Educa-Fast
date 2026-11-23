import React from 'react';

import { ActionDialog } from '../components/ActionDialog';
import { PeopleList } from '../components/PeopleList';
import { AdminSidebar } from '../components/Navigation';
import { MutationForm } from '../components/MutationForm';

export default function AdminCadastroAluno({ data }) {
    
    return <>

    <AdminSidebar />

    <main className="flex-1 p-10 overflow-y-auto">
        <header className="mb-10 flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
            <div>
                <h1 className="text-3xl font-bold">Cadastro de Alunos</h1>
                <p className="text-gray-400">Consulte os alunos cadastrados e abra um novo cadastro quando necessário.</p>
            </div>


        <ActionDialog title="Novo aluno" label="Novo aluno" wide>
            <div className="flex flex-wrap gap-4">
                <button data-ui-action type="reset" form="aluno-form" className="inline-flex h-12 items-center rounded-xl border border-white/10 bg-white/5 px-6 font-bold text-white transition hover:bg-white/10">
                    Limpar
                </button>
                <button data-ui-action type="submit" form="aluno-form" className="inline-flex h-12 items-center rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-7 font-bold text-white transition hover:brightness-110">
                    Salvar Registro
                </button>
            </div>
            <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_368px]">
                <MutationForm action="/api/cadastro/aluno" resetOnSuccess id="aluno-form" className="glass-card cadastro-card rounded-[32px] px-6 py-8 md:px-10 lg:px-10" encType="multipart/form-data">
                    <section>
                        <h2 className="text-xl font-extrabold text-white">Informações Pessoais</h2>
                        <div className="mt-5 border-t border-white/10 pt-7">
                            <div className="grid gap-8 md:grid-cols-2">
                                <label className="block">
                                    <span className="mb-2 block text-sm font-medium text-slate-300">Nome Completo</span>
                                    <span className="field flex h-14 items-center rounded-2xl px-4">
                                        <input type="text" name="nome" placeholder="Ex: João da Silva" required />
                                    </span>
                                </label>

                                <label className="block">
                                    <span className="mb-2 block text-sm font-medium text-slate-300">Número de Matrícula</span>
                                    <span className="field flex h-14 items-center rounded-2xl px-4">
                                        <input type="text" name="matricula" placeholder="Ex: 20240001" required />
                                    </span>
                                </label>

                                <label className="block">
                                    <span className="mb-2 block text-sm font-medium text-slate-300">Curso / Série</span>
                                    <span className="field flex h-14 items-center rounded-2xl px-4">
                                        <select name="curso">
                                            <option value="">Selecione um curso</option>
                                            <option>Ensino Fundamental</option>
                                            <option>Ensino Médio</option>
                                            <option>Educação de Jovens e Adultos</option>
                                        </select>
                                    </span>
                                </label>

                                <label className="block">
                                    <span className="mb-2 block text-sm font-medium text-slate-300">Status da Matrícula</span>
                                    <span className="field flex h-14 items-center rounded-2xl px-4">
                                        <select name="status">
                                            <option>Ativo</option>
                                            <option>Pendente</option>
                                            <option>Inativo</option>
                                        </select>
                                    </span>
                                </label>

                                <label className="block">
                                    <span className="mb-2 block text-sm font-medium text-slate-300">E-mail de Acesso</span>
                                    <span className="field flex h-14 items-center rounded-2xl px-4">
                                        <input type="email" name="email" placeholder="aluno@email.com" required />
                                    </span>
                                </label>

                                <label className="block">
                                    <span className="mb-2 block text-sm font-medium text-slate-300">Senha Inicial</span>
                                    <span className="field flex h-14 items-center rounded-2xl px-4">
                                        <input type="password" name="senha" placeholder="Defina uma senha" required />
                                    </span>
                                </label>
                            </div>
                        </div>
                    </section>

                    <section className="mt-9">
                        <h2 className="text-xl font-extrabold text-white">Documentação</h2>
                        <div className="mt-5 border-t border-white/10 pt-7">
                            <div className="grid gap-8 md:grid-cols-2">
                                <label className="block">
                                    <span className="mb-2 block text-sm font-medium text-slate-300">CPF</span>
                                    <span className="field flex h-14 items-center rounded-2xl px-5">
                                        <input type="text" name="cpf" placeholder="000.000.000-00" />
                                    </span>
                                </label>

                                <label className="block">
                                    <span className="mb-2 block text-sm font-medium text-slate-300">Data de Nascimento</span>
                                    <span className="field flex h-14 items-center rounded-2xl px-5">
                                        <input type="date" name="data_nascimento" />
                                    </span>
                                </label>
                            </div>
                        </div>
                    </section>
                    
                </MutationForm>

                <aside className="space-y-8">
                    <section className="glass-card cadastro-card rounded-[32px] px-8 py-9">
                        <h2 className="text-lg font-extrabold text-white">Foto do Aluno</h2>
                        <label className="mx-auto mt-7 flex aspect-square w-40 cursor-pointer flex-col items-center justify-center rounded-[22px] border-2 border-dashed border-cyan-400/35 bg-white/5 text-center transition hover:border-cyan-300 hover:bg-white/10">
                            <input type="file" name="foto_perfil" form="aluno-form" className="sr-only" accept="image/png,image/jpeg" />
                            <span className="mt-3 text-xs text-slate-400">Carregar Imagem</span>
                        </label>
                        <p className="mt-7 text-center text-[11px] leading-5 text-slate-400">Formatos aceitos: JPG, PNG.<br />Tamanho máximo: 2MB.</p>
                    </section>

                    <section className="rounded-[20px] border border-cyan-500/20 bg-cyan-500/10 px-8 py-8 shadow-2xl shadow-black/20">
                        <h2 className="text-lg font-extrabold text-white">Dica de Gestão</h2>
                        <p className="mt-5 text-sm leading-6 text-slate-300">Certifique-se de que todos os documentos originais foram digitalizados antes de finalizar o cadastro. Os dados salvos ficam disponíveis no cadastro do aluno.</p>
                    </section>
                </aside>
            </div>
        </ActionDialog>
        </header>
        <PeopleList people={data.alunos || []} tipo="aluno" />
    </main>
    </>;
}
