import React, { useContext, useRef, useState } from 'react';
import { AdminSidebar } from '../components/Navigation';
import { PageDataContext } from '../components/MutationForm';
import { TurmaDetalhes } from '../components/TurmaDetalhes';
import { api } from '../api';

export default function AdminTurmas({ data }) {
    const { turmas = [] } = data;
    const { refresh } = useContext(PageDataContext);
    const dialog = useRef(null);
    const nome = useRef(null);
    const [selected, setSelected] = useState(null);
    const [pending, setPending] = useState(false);
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');
    async function criar(e) {
        e.preventDefault();
        if (pending) return;
        setPending(true); setError('');
        const form = e.currentTarget;
        try {
            await api('/api/admin/turmas', { method: 'POST', body: new FormData(form) });
            form.reset(); dialog.current.close(); setMessage('Turma cadastrada com sucesso.');
            await refresh();
        } catch (e) { setError(e.message); }
        finally { setPending(false); }
    }
    return <>
        <AdminSidebar />
        <main className="flex-1 p-10 overflow-y-auto">
            <header className="flex justify-between items-center mb-8"><div><h1 className="text-3xl font-bold">Turmas</h1><p className="text-slate-300 mt-1">Selecione uma turma para gerenciar seus vínculos e o cronograma semanal.</p></div><button type="button" className="rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-5 py-3 font-bold" onClick={() => { setError(''); setMessage(''); dialog.current.showModal(); nome.current.focus(); }}>Nova turma</button></header>
            {message && <p role="status" className="text-green-200 mb-5">{message}</p>}
            <section className="glass-card turma-card rounded-2xl p-6"><h2 className="text-xl font-bold">Turmas cadastradas</h2><p className="text-sm text-slate-300 mt-1 mb-5">{turmas.length} registros encontrados</p><div className="turma-table-wrapper"><table className="w-full text-left"><thead><tr><th>Nome</th><th>Código</th><th>Ano letivo</th><th>Turno</th></tr></thead><tbody>{turmas.length ? turmas.map(t => <tr key={t.id} className="border-t border-white/10 cursor-pointer" onClick={() => setSelected(t.id)}><td><button type="button" className="text-cyan-200 hover:text-white text-left font-medium" onClick={e => { e.stopPropagation(); setSelected(t.id); }}>{t.nome}</button></td><td>{t.codigo}</td><td>{t.ano_letivo}</td><td>{t.turno}</td></tr>) : <tr><td colSpan={4} className="text-slate-300">Nenhuma turma cadastrada. Clique em “Nova turma” para começar.</td></tr>}</tbody></table></div></section>
        </main>
        {selected !== null && <TurmaDetalhes turma={turmas.find(t => t.id === selected)} data={data} onClose={() => setSelected(null)} />}
        <dialog ref={dialog} className="turma-modal" aria-labelledby="nova-turma-titulo" onCancel={e => { if (pending) e.preventDefault(); }}>
            <div className="flex justify-between gap-4"><div><h2 id="nova-turma-titulo" className="text-xl font-bold">Nova turma</h2><p className="text-sm text-slate-300 mt-2">Informe os dados principais da turma.</p></div><button type="button" disabled={pending} aria-label="Fechar cadastro de turma" className="text-2xl leading-none" onClick={() => dialog.current.close()}>×</button></div>
            <form onSubmit={criar} aria-busy={pending}><input type="hidden" name="action" value="create" />
                <label className="turma-field"><span>Nome</span><input ref={nome} name="nome" required placeholder="Ex: 1º Ano A" /></label>
                <label className="turma-field"><span>Código</span><input name="codigo" required placeholder="Ex: 1A-2026" /></label>
                <label className="turma-field"><span>Ano letivo</span><input name="ano_letivo" type="number" min="2000" step="1" required /></label>
                <label className="turma-field"><span>Turno</span><select name="turno" defaultValue=""><option value="">Selecione o turno</option>{['Matutino', 'Vespertino', 'Noturno', 'Integral'].map(t => <option key={t}>{t}</option>)}</select></label>
                {error && <p role="alert" className="turma-alert">{error}</p>}
                <div className="flex justify-end gap-3 mt-6"><button data-ui-action type="button" disabled={pending} className="rounded-xl border border-white/20 px-4 py-3" onClick={() => dialog.current.close()}>Cancelar</button><button data-ui-action disabled={pending} className="rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-5 py-3 font-bold">{pending ? 'Salvando…' : 'Cadastrar Turma'}</button></div>
            </form>
        </dialog>
    </>;
}
