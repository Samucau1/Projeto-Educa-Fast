import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from './Auth';

export function LogoutButton({ children = 'Sair do Sistema', className }) {
    const { logout } = useAuth();
    const navigate = useNavigate();
    const [pending, setPending] = useState(false);
    const [error, setError] = useState('');
    async function exit() {
        setPending(true);
        setError('');
        try {
            await logout();
            navigate('/login', { replace: true });
        } catch (error) {
            setError(error.message);
        } finally {
            setPending(false);
        }
    }
    return <>
        <button type="button" className={className} onClick={exit} disabled={pending}>{pending ? 'Saindo…' : children}</button>
        {error && <p role="alert" className="text-red-300">{error}</p>}
    </>;
}

const groups = [
    ['PRINCIPAL', [['/admin/dashboard', 'Painel Geral']]],
    ['ADMINISTRAÇÃO', [
        ['/admin/cadastro-alunos', 'Alunos'],
        ['/admin/cadastro-professores', 'Professores'],
        ['/admin/banco-de-dados', 'Banco de Dados'],
    ]],
    ['PEDAGÓGICO', [
        ['/admin/disciplinas', 'Disciplinas'], ['/admin/turmas', 'Turmas'], ['/admin/comunicados', 'Comunicados'],
    ]],
];

export function AdminSidebar() {
    return <aside className="w-72 glass-sidebar h-screen sticky top-0 flex flex-col p-6">
        <div className="mb-10 text-center">
            <h2 className="text-xl font-bold tracking-tighter text-cyan-400">SECRETARIA DF</h2>
            <p className="text-[10px] text-gray-500 uppercase tracking-widest">Secretaria Escolar</p>
        </div>
        <nav className="flex-1 space-y-2" aria-label="Secretaria Escolar">
            {groups.map(([title, links]) => <React.Fragment key={title}>
                <div className="text-[10px] font-bold text-gray-500 pt-4 mb-2 ml-4">{title}</div>
                {links.map(([to, label]) => <NavLink key={to} to={to} className={({ isActive }) =>
                    `flex items-center px-4 py-3 rounded-xl transition-all ${isActive ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' : 'hover:bg-white/5 text-gray-300 hover:text-white'}`
                }>{label}</NavLink>)}
            </React.Fragment>)}
        </nav>
        <div className="mt-auto pt-6 border-t border-white/10">
            <LogoutButton className="flex items-center px-4 py-3 rounded-xl text-red-400 hover:bg-red-500/10 transition-all" />
        </div>
    </aside>;
}


export function GestaoSidebar({ active, onSelect }) {
    return <aside className="w-72 shrink-0 glass-sidebar h-screen sticky top-0 flex flex-col p-6 overflow-y-auto">
        <div className="mb-10 text-center">
            <h2 className="text-xl font-bold tracking-tighter text-cyan-400">SECRETARIA DF</h2>
            <p className="text-[10px] text-slate-300 uppercase tracking-widest">Administração geral</p>
        </div>
        <nav className="flex-1 space-y-2" aria-label="Administração geral">
            <div className="text-[10px] font-bold text-slate-300 pt-4 mb-2 ml-4">GESTÃO DO SISTEMA</div>
            {['Contas', 'Configurações', 'Auditoria', 'Relatórios', 'Backup'].map(name =>
                <button key={name} type="button" aria-current={active === name ? 'page' : undefined}
                    onClick={() => onSelect(name)}
                    className={`w-full text-left flex items-center px-4 py-3 rounded-xl transition-all ${active === name ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' : 'hover:bg-white/5 text-gray-300 hover:text-white'}`}>
                    {name}
                </button>
            )}
        </nav>
        <div className="mt-auto pt-6 border-t border-white/10 space-y-2">
            <NavLink to="/alterar-senha" className="block px-4 py-3 rounded-xl text-gray-300 hover:bg-white/5 hover:text-white">Alterar senha</NavLink>
            <LogoutButton className="flex items-center px-4 py-3 rounded-xl text-red-400 hover:bg-red-500/10 transition-all" />
        </div>
    </aside>;
}
