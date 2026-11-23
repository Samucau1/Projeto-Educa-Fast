import React, { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../components/Auth';
import { homeForRole } from '../utils';

export default function Login() {
    const { user, loading, login } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [error, setError] = useState('');
    const [pending, setPending] = useState(false);
    function destination(user) {
        if (user.exigir_troca) return '/alterar-senha';
        const previous = location.state?.from;
        const prefix = { admin: '/gestao', secretaria: '/admin/', aluno: '/aluno', professor: '/professor' }[user.role];
        return prefix && previous?.startsWith(prefix) ? previous : homeForRole(user.role);
    }
    if (loading) return <p role="status">Carregando sessão…</p>;
    if (user) return <Navigate to={destination(user)} replace />;

    async function submit(event) {
        event.preventDefault();
        if (pending) return;
        const data = new FormData(event.currentTarget);
        setError('');
        setPending(true);
        try {
            const user = await login(data.get('email'), data.get('senha'));
            navigate(destination(user), { replace: true });
        } catch (error) {
            setError(error.message);
        } finally {
            setPending(false);
        }
    }

    return <div className="login-layout flex items-center justify-center min-h-screen w-full p-6">
        <div className="glass p-10 rounded-[32px] w-full max-w-md shadow-2xl mx-auto">
            <h1 className="text-white text-3xl font-bold text-center mb-8">Secretaria DF</h1>
            <form onSubmit={submit} className="space-y-6" aria-busy={pending}>
                <input name="email" type="email" aria-label="E-mail Institucional" autoComplete="username" required placeholder="E-mail Institucional" className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-cyan-500" />
                <input name="senha" type="password" aria-label="Senha" autoComplete="current-password" required placeholder="Senha" className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-cyan-500" />
                {error && <p role="alert" className="text-sm text-red-300">{error}</p>}
                <button type="submit" disabled={pending} className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold py-4 rounded-xl disabled:opacity-70">{pending ? 'Entrando…' : 'Acessar Sistema'}</button>
            </form>
        </div>
    </div>;
}
