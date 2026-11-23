import React from 'react';

import { ActionDialog } from '../components/ActionDialog';
import { PeopleList } from '../components/PeopleList';
import { AdminSidebar } from '../components/Navigation';
import { MutationForm } from '../components/MutationForm';

export default function AdminCadastroProfessores({ data }) {
    
    return <>

    <AdminSidebar />

    <main className="flex-1 p-10 overflow-y-auto">
        <header className="mb-10 flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
            <div>
                <h1 className="text-3xl font-bold">Cadastro de Professores</h1>
                <p className="text-gray-400">Insira as informações do novo docente no sistema.</p>
            </div>


        <ActionDialog title="Novo professor" label="Novo professor" wide>
            <div className="flex flex-wrap gap-4">
                <button data-ui-action type="reset" form="professor-form" className="inline-flex h-12 items-center rounded-xl border border-white/10 bg-white/5 px-6 font-bold text-white transition hover:bg-white/10">
                    Limpar
                </button>
                <button data-ui-action type="submit" form="professor-form" className="inline-flex h-12 items-center rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-7 font-bold text-white transition hover:brightness-110">
                    Salvar Registro
                </button>
            </div>
            <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_368px]">
                <MutationForm action="/api/cadastro/professor" resetOnSuccess id="professor-form" className="glass-card cadastro-card rounded-[32px] px-6 py-8 md:px-10 lg:px-10" encType="multipart/form-data">
                    <section>
                        <h2 className="text-xl font-extrabold text-white">Informações Gerais</h2>
                        <div className="mt-5 border-t border-white/10 pt-7">
                            <div className="grid gap-8 md:grid-cols-2">
                                <label className="block">
                                    <span className="mb-2 block text-sm font-medium text-slate-300">Nome Completo</span>
                                    <span className="field flex h-14 items-center rounded-2xl px-4">
                                        <input type="text" name="nome" placeholder="Ex: Prof. Mariana Souza" required />
                                    </span>
                                </label>

                                <label className="block">
                                    <span className="mb-2 block text-sm font-medium text-slate-300">Disciplina Principal</span>
                                    <span className="field flex h-14 items-center rounded-2xl px-4">
                                        <input type="text" name="disciplina" placeholder="Ex: Matemática" required />
                                    </span>
                                </label>

                                <label className="block">
                                    <span className="mb-2 block text-sm font-medium text-slate-300">Formação Acadêmica</span>
                                    <span className="field flex h-14 items-center rounded-2xl px-4">
                                        <input type="text" name="formacao" placeholder="Ex: Licenciatura em Matemática" />
                                    </span>
                                </label>

                                <label className="block">
                                    <span className="mb-2 block text-sm font-medium text-slate-300">Telefone / WhatsApp</span>
                                    <span className="field flex h-14 items-center rounded-2xl px-4">
                                        <input type="tel" name="telefone" placeholder="(61) 99999-9999" />
                                    </span>
                                </label>

                                <label className="block">
                                    <span className="mb-2 block text-sm font-medium text-slate-300">CPF</span>
                                    <span className="field flex h-14 items-center rounded-2xl px-4">
                                        <input type="text" name="cpf" placeholder="000.000.000-00" required />
                                    </span>
                                </label>

                                <label className="block">
                                    <span className="mb-2 block text-sm font-medium text-slate-300">E-mail de Acesso</span>
                                    <span className="field flex h-14 items-center rounded-2xl px-4">
                                        <input type="email" name="email" placeholder="professor@email.com" required />
                                    </span>
                                </label>
                            </div>
                        </div>
                    </section>

                    <section className="mt-9">
                        <h2 className="text-xl font-extrabold text-white">Cargo e Horários</h2>
                        <div className="mt-5 border-t border-white/10 pt-7">
                            <div className="grid gap-8 md:grid-cols-2">
                                <label className="block">
                                    <span className="mb-2 block text-sm font-medium text-slate-300">Regime de Trabalho</span>
                                    <span className="field flex h-14 items-center rounded-2xl px-5">
                                        <select name="regime">
                                            <option>20 horas semanais</option>
                                            <option>30 horas semanais</option>
                                            <option>40 horas semanais</option>
                                            <option>Dedicação exclusiva</option>
                                        </select>
                                    </span>
                                </label>

                                <label className="block">
                                    <span className="mb-2 block text-sm font-medium text-slate-300">Data de Admissão</span>
                                    <span className="field flex h-14 items-center rounded-2xl px-5">
                                        <input type="date" name="data_admissao" />
                                    </span>
                                </label>

                                <label className="block">
                                    <span className="mb-2 block text-sm font-medium text-slate-300">Senha Inicial</span>
                                    <span className="field flex h-14 items-center rounded-2xl px-5">
                                        <input type="password" name="senha" placeholder="Defina uma senha" required />
                                    </span>
                                </label>
                            </div>
                        </div>
                    </section>
                    
                </MutationForm>

                <aside className="space-y-8">
                    <section className="glass-card cadastro-card rounded-[32px] px-8 py-9">
                        <h2 className="text-lg font-extrabold text-white">Foto do Professor</h2>
                        <label className="mx-auto mt-7 flex aspect-square w-40 cursor-pointer flex-col items-center justify-center rounded-[22px] border-2 border-dashed border-cyan-400/35 bg-white/5 text-center transition hover:border-cyan-300 hover:bg-white/10">
                            <input type="file" name="foto_perfil" form="professor-form" className="sr-only" accept="image/png,image/jpeg" />
                            <span className="mt-3 text-xs text-slate-400">Carregar Imagem</span>
                        </label>
                        <p className="mt-7 text-center text-[11px] leading-5 text-slate-400">Imagem para o crachá funcional.<br />Tamanho máximo: 2MB.</p>
                    </section>

                    <section className="rounded-[20px] border border-cyan-500/20 bg-cyan-500/10 px-8 py-8 shadow-2xl shadow-black/20">
                        <h2 className="text-lg font-extrabold text-white">Nota Informativa</h2>
                        <p className="mt-5 text-sm leading-6 text-slate-300">Os dados de formação acadêmica são validados automaticamente com o banco de dados do MEC. Certifique-se da grafia correta do nome.</p>
                    </section>
                </aside>
            </div>
        </ActionDialog>
        </header>
        <PeopleList people={data.professores || []} tipo="professor" />
    </main>
    </>;
}
