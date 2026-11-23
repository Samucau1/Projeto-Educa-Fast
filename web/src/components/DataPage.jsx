import React, { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from './Auth';
import { TabsProvider } from './Tabs';
import { PageDataContext } from './MutationForm';

export function PageError({ error, retry }) {
    return <main className="p-10" role="alert">
        <h1 className="text-2xl font-bold">{error.status === 404 ? 'Página ou registro não encontrado' : error.status === 403 ? 'Acesso não permitido' : 'Não foi possível carregar a página'}</h1>
        <p className="my-4">{error.message}</p>
        {retry && <button className="mr-6 text-cyan-300" onClick={retry}>Tentar novamente</button>}
        <Link to="/">Voltar ao início</Link>
    </main>;
}

export function DataPage({ endpoint, component: Component }) {
    const params = useParams();
    const url = endpoint?.replace(/:([a-z_]+)/g, (_, key) => encodeURIComponent(params[key]));
    const { user } = useAuth();
    const [state, setState] = useState({ url: null, data: null, error: null });
    const [revision, setRevision] = useState(0);
    const refresh = useCallback(() => setRevision((previous) => previous + 1), []);

    useEffect(() => {
        if (!url) return;
        const controller = new AbortController();
        api(url, { signal: controller.signal })
            .then((data) => setState({ url, data, error: null }))
            .catch((error) => {
                if (error.name !== 'AbortError') setState({ url, data: null, error });
            });
        return () => controller.abort();
    }, [url, revision]);

    if (url && state.url === url && state.error) return <PageError error={state.error} retry={refresh} />;
    if (url && (state.url !== url || !state.data)) return <p className="p-10" role="status">Carregando dados…</p>;
    return <PageDataContext.Provider value={{ refresh }}>
        <TabsProvider key={url || "static"}>
            <div className="app-layout flex w-full"><Component data={{ ...(state.data || {}), user }} /></div>
        </TabsProvider>
    </PageDataContext.Provider>;
}
