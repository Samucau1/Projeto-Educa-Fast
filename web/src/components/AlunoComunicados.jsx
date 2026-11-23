import React, { useEffect, useRef, useState } from 'react';
import { useAuth } from './Auth';
import { api } from '../api';

export function AlunoComunicados() {
    const { user } = useAuth();
    const role = user?.role;
    const allowed = ['aluno', 'professor'].includes(role);
    const endpoint = `/api/${role}/comunicados`;
    const [items, setItems] = useState([]);
    const [cursor, setCursor] = useState(null);
    const [more, setMore] = useState(false);
    const [busy, setBusy] = useState(true);
    const [error, setError] = useState('');
    const requesting = useRef(false);
    useEffect(() => {
        if (!allowed) return;
        const controller = new AbortController();
        api(endpoint, { signal: controller.signal }).then(result => {
            setItems(result.comunicados); setCursor(result.next_cursor); setMore(result.has_more);
        }).catch(e => { if (e.name !== 'AbortError') setError(e.message); })
            .finally(() => { if (!controller.signal.aborted) setBusy(false); });
        return () => controller.abort();
    }, [endpoint, allowed]);
    async function loadMore() {
        if (requesting.current || busy) return;
        requesting.current = true; setBusy(true); setError('');
        try {
            const result = await api(`${endpoint}${cursor ? `?before=${cursor}` : ''}`);
            setItems(previous => [...previous, ...result.comunicados]);
            setCursor(result.next_cursor); setMore(result.has_more);
        } catch (e) { setError(e.message); }
        finally { requesting.current = false; setBusy(false); }
    }
    if (!allowed) return null;
    return <div className="glass-card rounded-2xl p-6">
        <h2 className="text-xl font-bold mb-5">Comunicados</h2>
        <div className="comunicados-list space-y-6" tabIndex={0} aria-label="Comunicados da escola" aria-busy={busy}>
            {items.map(c => <article key={c.id} className="border-b border-white/10 pb-5">
                <h3 className="font-semibold text-lg">{c.titulo}</h3><p className="text-xs text-slate-300 mt-1">{c.data}</p>
                <p className="text-sm text-slate-200 mt-3 whitespace-pre-wrap break-words">{c.mensagem}</p>
            </article>)}
            {!items.length && !busy && !error && <p>Nenhum comunicado disponível.</p>}
            {busy && <p role="status">Carregando comunicados…</p>}
            {error && <p role="alert">{error}</p>}
            {(more || error) && <button className="ui-button" disabled={busy} onClick={loadMore}>{error ? 'Tentar novamente' : 'Carregar mais'}</button>}
        </div>
    </div>;
}
