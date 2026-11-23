import ShellPagina, { headPainel } from '../components/ShellPagina';
import { TabelaRolagem } from '../components/tabelas';
import { urlFor } from '../core/urls';

export const head = headPainel();
export const bodyClass = 'app-page';
export const titulo = () => 'Dashboard | Educa Fast';

export default function AdminPainel({ d, g }) {
    return (
        <ShellPagina id="admin-painel" titulo="Visão geral">
            <header className="flex justify-between items-center mb-10">
                <div>
                    <span className="eyebrow">GESTÃO ESCOLAR</span>
                    <h1 className="text-3xl font-bold">Olá, {g.sessao.user_email ?? 'Administrador'}!</h1>
                    <p className="text-slate-300">Bem-vindo ao centro de controle da sua escola.</p>
                </div>
            </header>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
                <div className="glass-card p-6 rounded-3xl">
                    <p className="text-slate-300 text-sm">Total de Alunos</p>
                    <h2 className="text-4xl font-bold mt-2">{d.total_alunos}</h2>
                    <div className="mt-4 text-xs text-emerald-300">Registros cadastrados</div>
                </div>
                <div className="glass-card p-6 rounded-3xl">
                    <p className="text-slate-300 text-sm">Professores Cadastrados</p>
                    <h2 className="text-4xl font-bold mt-2">{d.total_professores}</h2>
                    <div className="mt-4 text-xs text-cyan-300">Todos os departamentos</div>
                </div>
                <div className="glass-card p-6 rounded-3xl">
                    <p className="text-slate-300 text-sm">Matrículas Pendentes</p>
                    <h2 className="text-4xl font-bold mt-2">{d.matriculas_pendentes}</h2>
                    <div className="mt-4 text-xs text-violet-300">{d.matriculas_hoje} criadas hoje</div>
                </div>
            </div>
            <div className="glass-card p-8 rounded-[32px]">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-bold">Últimos Registros</h3>
                    <a href={urlFor('home.admin_banco_dados')} className="text-sm text-cyan-300 hover:underline">Ver todos</a>
                </div>
                <TabelaRolagem>
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
                            {d.registros_recentes.length ? d.registros_recentes.map((registro, i) => (
                                <tr key={i} className="border-t border-white/5">
                                    <td className="py-4 font-medium text-white">{registro.nome}</td>
                                    <td className="py-4 text-slate-300">{registro.tipo}</td>
                                    <td className="py-4 text-slate-300">{registro.created_at_label}</td>
                                    <td className="py-4 text-right">
                                        {registro.aluno_id
                                            ? <a href={urlFor('home.admin_detalhes_aluno', { aluno_id: registro.aluno_id })} className="bg-white/10 px-3 py-1 rounded-lg hover:bg-white/20">Gerenciar</a>
                                            : <button className="bg-white/10 px-3 py-1 rounded-lg opacity-60">Gerenciar</button>}
                                    </td>
                                </tr>
                            )) : (
                                <tr className="border-t border-white/5">
                                    <td className="py-6 text-slate-300" colSpan={4}>Nenhum registro encontrado.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </TabelaRolagem>
            </div>
        </ShellPagina>
    );
}
