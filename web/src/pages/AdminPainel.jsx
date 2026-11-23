import React, { Fragment } from 'react';
import { Link } from 'react-router-dom';
import { AdminSidebar } from '../components/Navigation';


export default function AdminPainel({ data }) {
    const { matriculas_hoje = 0, matriculas_pendentes = 0, registros_recentes = [], total_alunos = 0, total_professores = 0, user = {} } = data;
    return <>

        <AdminSidebar />

        <main className="flex-1 p-10 overflow-y-auto">
            <header className="flex justify-between items-center mb-10">
                <div>
                    <h1 className="text-3xl font-bold">Olá, {(user.email || "Secretaria Escolar")}!</h1>
                    <p className="text-slate-300">Bem-vindo ao centro de controle da sua escola.</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="text-right">
                        <p className="text-sm font-bold">Admin Secretaria</p>
                        <p className="text-[10px] text-cyan-300">Online agora</p>
                    </div>
                    <div className="w-12 h-12 rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 border-2 border-white/20"></div>
                </div>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
                <div className="glass-card p-6 rounded-3xl">
                    <p className="text-slate-300 text-sm">Total de Alunos</p>
                    <h2 className="text-4xl font-bold mt-2">{total_alunos}</h2>
                    <div className="mt-4 text-xs text-emerald-300">Registros cadastrados</div>
                </div>
                <div className="glass-card p-6 rounded-3xl">
                    <p className="text-slate-300 text-sm">Professores Cadastrados</p>
                    <h2 className="text-4xl font-bold mt-2">{total_professores}</h2>
                    <div className="mt-4 text-xs text-cyan-300">Todos os departamentos</div>
                </div>
                <div className="glass-card p-6 rounded-3xl">
                    <p className="text-slate-300 text-sm">Matrículas Pendentes</p>
                    <h2 className="text-4xl font-bold mt-2">{matriculas_pendentes}</h2>
                    <div className="mt-4 text-xs text-violet-300">{matriculas_hoje} criadas hoje</div>
                </div>
            </div>

            <div className="glass-card p-8 rounded-[32px]">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-bold">Últimos Registros</h3>
                    <button className="text-sm text-cyan-300 hover:underline">Ver todos</button>
                </div>
                <table className="w-full text-left">
                    <thead>
                        <tr className="text-slate-400 text-xs uppercase tracking-wider">
                            <th className="pb-4 font-medium">Nome</th>
                            <th className="pb-4 font-medium">Tipo</th>
                            <th className="pb-4 font-medium">Data</th>
                            <th className="pb-4 font-medium text-right">Ação</th>
                        </tr>
                    </thead>
                    <tbody className="text-sm">
                        {registros_recentes.length ? <>{registros_recentes.map((registro, index15) => <Fragment key={registro?.id ?? index15}>
                        <tr className="border-t border-white/5">
                            <td className="py-4 font-medium text-white">{registro.nome}</td>
                            <td className="py-4 text-slate-300">{registro.tipo}</td>
                            <td className="py-4 text-slate-300">{registro.created_at_label}</td>
                            <td className="py-4 text-right">
                                <Link data-ui-action to={`/admin/${registro.aluno_id ? 'alunos' : 'professores'}/${encodeURIComponent(registro.aluno_id || registro.professor_id)}`} className="ui-button">Ver detalhes</Link>
                            </td>
                        </tr>
                        </Fragment>)}</> : <>
                        <tr className="border-t border-white/5">
                            <td className="py-6 text-slate-300" colSpan="4">Nenhum registro encontrado.</td>
                        </tr>
                        </>}
                    </tbody>
                </table>
            </div>
        </main>
    
    </>;
}
