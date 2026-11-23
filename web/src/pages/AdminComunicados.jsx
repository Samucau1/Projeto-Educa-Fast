import React, { useEffect, useState } from 'react';
import { AdminSidebar } from '../components/Navigation';
import { ActionDialog } from '../components/ActionDialog';
import { MutationForm } from '../components/MutationForm';
import { Pagination } from '../components/Pagination';
import { api } from '../api';

export default function AdminComunicados({ data }) {
    const [records, setRecords] = useState(data);
    const [page, setPage] = useState(1);
    const [size, setSize] = useState(20);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    useEffect(() => { setPage(1); }, [data]);
    useEffect(() => {
        const controller = new AbortController();
        setBusy(true); setError('');
        api(`/api/admin/comunicados?page=${page}&page_size=${size}`, { signal: controller.signal })
            .then(setRecords).catch(e => { if (e.name !== 'AbortError') setError(e.message); })
            .finally(() => { if (!controller.signal.aborted) setBusy(false); });
        return () => controller.abort();
    }, [page, size, data]);
    const { comunicados = [] } = records;
    return <><AdminSidebar /><main className="flex-1 p-10 overflow-y-auto">
        <header className="flex flex-wrap justify-between items-center gap-4 mb-8"><div><h1 className="text-3xl font-bold">Comunicados</h1><p className="text-slate-300 mt-1">Consulte os comunicados enviados pela escola.</p></div>
        <ActionDialog title="Novo comunicado" label="Novo comunicado">
            <MutationForm action="/api/admin/comunicados" resetOnSuccess className="space-y-5">
                <label className="block"><span className="block mb-2">Título do Recado</span><input name="titulo" required className="comunicado-field" /></label>
                <label className="block"><span className="block mb-2">Mensagem</span><textarea name="mensagem" rows={4} required className="comunicado-field" /></label>
                <button data-ui-action className="ui-button">Disparar Comunicado</button>
            </MutationForm>
        </ActionDialog></header>
        <section className="glass-card rounded-2xl p-6" aria-busy={busy}>
            <div className="mb-5"><h2 className="text-xl font-bold">Recados enviados</h2><p className="text-sm text-slate-300 mt-1">{records.pagination?.total ?? comunicados.length} registros encontrados</p></div>
            {error && <p role="alert">{error}</p>}
            <div className="comunicados-list space-y-6" tabIndex={0} aria-label="Comunicados enviados">{comunicados.map(c => <article key={c.id} className="border-b border-white/10 pb-6">
                <h3 className="text-lg font-semibold">{c.titulo}</h3>
                <p className="text-xs text-slate-300 mt-1">{c.destinatario} · {c.created_at_label}</p>
                <p className="text-sm text-slate-200 mt-3 whitespace-pre-wrap break-words">{c.mensagem}</p>
            </article>)}{!comunicados.length && <p className="text-slate-300">Nenhum comunicado enviado.</p>}</div>
            <Pagination label="Paginação de comunicados" pagination={records.pagination} busy={busy} onPage={setPage} onSize={n => { setSize(n); setPage(1); }} />
        </section>
    </main></>;
}
