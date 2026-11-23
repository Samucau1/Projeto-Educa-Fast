import React, { useContext, useRef, useState } from 'react';
import { AdminSidebar } from '../components/Navigation';
import { PageDataContext } from '../components/MutationForm';
import { DisciplinaProfessores } from '../components/DisciplinaProfessores';
import { api } from '../api';

export default function AdminDisciplinas({ data }) {
    const { disciplinas = [], professores = [], professor_vinculos = [] } = data;
    const [disciplinaId, setDisciplinaId] = useState(null);
    const { refresh } = useContext(PageDataContext);
    const dialog = useRef(null);
    const nomeInput = useRef(null);
    const submitting = useRef(false);
    const [pending, setPending] = useState(false);
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');

    function abrir() {
        setError(''); setMessage('');
        dialog.current.showModal();
        nomeInput.current.focus();
    }
    async function salvar(event) {
        event.preventDefault();
        if (submitting.current) return;
        submitting.current = true; setPending(true); setError('');
        const form = event.currentTarget;
        try {
            await api('/api/admin/disciplinas', { method: 'POST', body: new FormData(form) });
            form.reset();
            dialog.current.close();
            setMessage('Disciplina cadastrada com sucesso.');
            await refresh();
        } catch (e) { setError(e.message); }
        finally { submitting.current = false; setPending(false); }
    }
    return <>
        <AdminSidebar />
        <main className="flex-1 p-10 overflow-y-auto">
            <header className="flex justify-between items-center mb-8">
                <div><h1 className="text-3xl font-bold">Disciplinas</h1><p className="text-slate-300 mt-1">Consulte as disciplinas cadastradas na escola.</p></div>
                <button type="button" onClick={abrir} className="bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold px-5 py-3 rounded-xl">Nova disciplina</button>
            </header>
            {message && <p role="status" className="text-green-200 mb-5">{message}</p>}
            <section className="glass-card discipline-card p-6 rounded-2xl">
                <div className="mb-5"><h2 className="text-xl font-bold">Disciplinas cadastradas</h2><p className="text-sm text-slate-300 mt-1">{disciplinas.length} registros encontrados</p></div>
                <div className="discipline-table-wrapper"><table className="w-full text-left"><thead><tr><th scope="col">Nome</th><th scope="col">Código</th><th scope="col" className="text-right">Carga horária</th></tr></thead><tbody>{disciplinas.length ? disciplinas.map(d => <tr key={d.id} onClick={() => setDisciplinaId(d.id)} className="border-t border-white/10 cursor-pointer"><td className="font-medium"><button type="button" onClick={e => { e.stopPropagation(); setDisciplinaId(d.id); }} className="text-left text-cyan-200 hover:text-white focus-visible:outline focus-visible:outline-cyan-300 rounded">{d.nome}</button></td><td className="text-cyan-300">{d.codigo}</td><td className="text-right text-slate-300">{d.carga_horaria}h</td></tr>) : <tr><td colSpan={3} className="text-slate-300">Nenhuma disciplina cadastrada. Clique em “Nova disciplina” para começar.</td></tr>}</tbody></table></div>
            </section>
        </main>
        {disciplinaId !== null && <DisciplinaProfessores disciplina={disciplinas.find(d => d.id === disciplinaId)} professores={professores} vinculos={professor_vinculos} onClose={() => setDisciplinaId(null)} />}
        <dialog ref={dialog} className="disciplina-modal" aria-labelledby="nova-disciplina-titulo" aria-describedby="nova-disciplina-descricao" onCancel={e => { if (pending) e.preventDefault(); }} onClick={e => {
            if (e.target === e.currentTarget && !pending) {
                const rect = e.currentTarget.getBoundingClientRect();
                if (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom) e.currentTarget.close();
            }
        }}>
            <div className="flex items-start justify-between gap-4"><div><h2 id="nova-disciplina-titulo" className="text-xl font-bold">Nova disciplina</h2><p id="nova-disciplina-descricao" className="text-sm text-slate-300 mt-2">Informe os dados da disciplina para adicioná-la à escola.</p></div><button type="button" disabled={pending} aria-label="Fechar janela" onClick={() => dialog.current.close()} className="text-slate-300 hover:text-white text-2xl leading-none">×</button></div>
            <form onSubmit={salvar} aria-busy={pending}>
                <input type="hidden" name="action" value="create" />
                <label className="discipline-field"><span>Nome</span><input name="nome" type="text" placeholder="Ex: Matemática" required ref={nomeInput} /></label>
                <label className="discipline-field"><span>Código</span><input name="codigo" type="text" placeholder="Ex: MAT" required /></label>
                <label className="discipline-field"><span>Carga horária</span><input name="carga_horaria" type="number" min="0" step="1" placeholder="Ex: 80" required /></label>
                {error && <p role="alert" className="discipline-alert">{error}</p>}
                <div className="flex justify-end gap-3 mt-7"><button data-ui-action type="button" disabled={pending} onClick={() => dialog.current.close()} className="px-4 py-3 rounded-xl border border-white/20 text-slate-200">Cancelar</button><button data-ui-action type="submit" disabled={pending} className="px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold disabled:opacity-60">{pending ? 'Salvando…' : 'Cadastrar Disciplina'}</button></div>
            </form>
        </dialog>
    </>;
}
