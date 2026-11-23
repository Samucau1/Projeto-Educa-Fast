import React, { useContext, useEffect, useRef, useState } from 'react';
import { PageDataContext } from './MutationForm';
import { api } from '../api';

export function DisciplinaProfessores({ disciplina, professores, vinculos, onClose }) {
    const dialog = useRef(null);
    const select = useRef(null);
    const submitting = useRef(false);
    const { refresh } = useContext(PageDataContext);
    const [associando, setAssociando] = useState(false);
    const [pending, setPending] = useState(false);
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');
    const associados = vinculos.filter(v => v.disciplina_id === disciplina.id);
    const disponiveis = professores.filter(p => !associados.some(v => v.professor_id === p.id));
    useEffect(() => { dialog.current.showModal(); }, []);
    useEffect(() => { if (associando) select.current?.focus(); }, [associando]);
    async function associar(event) {
        event.preventDefault();
        if (submitting.current) return;
        submitting.current = true; setPending(true); setError(''); setMessage('');
        try {
            await api('/api/admin/disciplinas', { method: 'POST', body: new FormData(event.currentTarget) });
            await refresh();
            setAssociando(false);
            setMessage('Professor associado à disciplina com sucesso.');
        } catch (e) { setError(e.message); }
        finally { submitting.current = false; setPending(false); }
    }
    return <dialog ref={dialog} className="disciplina-modal disciplina-professores-modal" aria-labelledby="disciplina-professores-titulo" onClose={onClose} onCancel={e => { if (pending) e.preventDefault(); }} onClick={e => {
        if (e.target === e.currentTarget && !pending) {
            const r = e.currentTarget.getBoundingClientRect();
            if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) e.currentTarget.close();
        }
    }}>
        <div className="flex justify-between items-start gap-4"><div><h2 id="disciplina-professores-titulo" className="text-xl font-bold">{disciplina.nome}</h2><p className="text-slate-300 mt-2 text-sm">{disciplina.codigo} · {disciplina.carga_horaria}h</p></div><button type="button" aria-label="Fechar detalhes da disciplina" disabled={pending} onClick={() => dialog.current.close()} className="text-2xl text-slate-300 hover:text-white leading-none">×</button></div>
        <div className="flex flex-wrap items-center justify-between gap-4 mt-7 mb-4"><h3 className="font-semibold">Professores associados ({associados.length})</h3><button data-ui-action type="button" disabled={pending || associando || !disponiveis.length} onClick={() => { setAssociando(true); setError(''); setMessage(''); }} className="px-4 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 font-bold disabled:opacity-50">Associar professor</button></div>
        {message && <p role="status" className="text-green-200 my-4">{message}</p>}
        {associados.length ? <ul className="disciplina-professores-lista">{associados.map(v => <li key={v.professor_id}><strong>{v.professor}</strong><span>Associado em {v.data}</span></li>)}</ul> : <p className="text-slate-300 py-5">Nenhum professor associado a esta disciplina.</p>}
        {associando && <form onSubmit={associar} aria-busy={pending} className="border-t border-white/10 mt-5 pt-2">
            <input type="hidden" name="action" value="associate_teacher" /><input type="hidden" name="disciplina_id" value={disciplina.id} />
            <label className="discipline-field"><span>Professor para associar</span><select name="professor_id" required defaultValue="" ref={select}><option value="">Selecione um professor</option>{disponiveis.map(p => <option key={p.id} value={p.id}>{p.nome} · {p.disciplina}</option>)}</select></label>
            {error && <p role="alert" className="discipline-alert">{error}</p>}
            <div className="flex justify-end gap-3 mt-5"><button data-ui-action type="button" disabled={pending} onClick={() => { setAssociando(false); setError(''); }} className="px-4 py-3 rounded-xl border border-white/20">Cancelar associação</button><button data-ui-action type="submit" disabled={pending} className="px-4 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 font-bold disabled:opacity-50">{pending ? 'Associando…' : 'Confirmar associação'}</button></div>
        </form>}
        {!disponiveis.length && <p className="mt-4 text-sm text-slate-300">{professores.length ? 'Todos os professores cadastrados já estão associados.' : 'Cadastre um professor antes de criar uma associação.'}</p>}
    </dialog>;
}
