import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../components/Auth';
import { LogoutButton } from '../components/Navigation';
import { api } from '../api';

export default function AlterarSenha() {
    const { user, loading } = useAuth();
    const [error, setError] = useState('');
    const [pending, setPending] = useState(false);
    if (loading) return <p>Carregando…</p>;
    if (!user) return <Navigate to="/login" replace />;
    async function submit(event) {
        event.preventDefault(); setError(''); setPending(true);
        const form = new FormData(event.currentTarget);
        try {
            await api('/api/senha', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(Object.fromEntries(form)) });
            window.location.assign('/');
        } catch (e) { setError(e.message); }
        finally { setPending(false); }
    }
    return <main className="gestao-page min-h-screen w-full flex items-center justify-center text-white p-6"><form className="glass-card rounded-3xl p-8 w-full max-w-md space-y-5" onSubmit={submit}><h1 className="text-2xl">Alterar senha</h1><p>{user.exigir_troca ? 'Altere sua senha para continuar usando o sistema.' : 'Defina uma nova senha para sua conta.'}</p><label className="block">Senha atual<input className="w-full bg-white/5 border border-white/10 outline-none focus:ring-2 focus:ring-cyan-500 rounded-lg p-3" type="password" name="senha_atual" autoComplete="current-password" required /></label><label className="block">Nova senha<input className="w-full bg-white/5 border border-white/10 outline-none focus:ring-2 focus:ring-cyan-500 rounded-lg p-3" type="password" name="nova_senha" autoComplete="new-password" minLength={8} required /></label>{error && <p role="alert">{error}</p>}<button disabled={pending} className="bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold rounded-lg p-3">Salvar nova senha</button> <LogoutButton /></form></main>;
}
