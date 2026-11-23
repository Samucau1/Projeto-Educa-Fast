import React, { createContext, useContext, useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { api } from '../api';
import { homeForRole } from '../utils';

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
    const [state, setState] = useState({ loading: true, user: null, error: null });
    useEffect(() => {
        const controller = new AbortController();
        api('/api/session', { signal: controller.signal })
            .then(({ user }) => setState({ loading: false, user, error: null }))
            .catch((error) => {
                if (error.name !== 'AbortError') setState({ loading: false, user: null, error });
            });
        const expired = () => setState({ loading: false, user: null, error: null });
        window.addEventListener('session:expired', expired);
        return () => {
            controller.abort();
            window.removeEventListener('session:expired', expired);
        };
    }, []);

    async function login(email, senha) {
        await api('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, senha }),
        });
        const { user } = await api('/api/session');
        setState({ loading: false, user, error: null });
        return user;
    }

    async function logout() {
        await api('/api/logout', { method: 'POST' });
        setState({ loading: false, user: null, error: null });
    }

    return <AuthContext.Provider value={{ ...state, login, logout }}>{children}</AuthContext.Provider>;
}

export function RequireRole({ role, children }) {
    const { loading, user, error } = useAuth();
    const location = useLocation();
    if (loading) return <p className="p-10" role="status">Carregando sessão…</p>;
    if (error) return <div className="p-10" role="alert">Não foi possível carregar a sessão. <button onClick={() => window.location.reload()}>Tentar novamente</button></div>;
    if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
    if (user.exigir_troca) return <Navigate to="/alterar-senha" replace />;
    if (user.role !== role) return <Navigate to={homeForRole(user.role)} replace />;
    return children;
}

export function HomeRedirect() {
    const { loading, user, error } = useAuth();
    if (loading) return <p className="p-10" role="status">Carregando sessão…</p>;
    if (error) return <p className="p-10" role="alert">Não foi possível carregar a sessão. Recarregue a página.</p>;
    return <Navigate to={user?.exigir_troca ? '/alterar-senha' : homeForRole(user?.role)} replace />;
}
