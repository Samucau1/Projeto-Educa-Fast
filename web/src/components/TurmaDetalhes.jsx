import React, { useContext, useEffect, useRef, useState } from 'react';
import { PageDataContext } from './MutationForm';
import { CronogramaTurma } from './CronogramaTurma';
import { GradeSemanal } from './GradeSemanal';
import { api } from '../api';

export function TurmaDetalhes({ turma, data, onClose }) {
    const dialog = useRef(null);
    const selector = useRef(null);
    const { refresh } = useContext(PageDataContext);
    const [tab, setTab] = useState('Alunos');
    const [gerenciando, setGerenciando] = useState(false);
    const [associando, setAssociando] = useState(false);
    const [pending, setPending] = useState(false);
    const [feedback, setFeedback] = useState(null);
    const tipoAluno = tab === 'Alunos';
    const alunos = (data.aluno_vinculos || []).filter(v => v.turma_id === turma.id);
    const professores = (data.professor_vinculos || []).filter(v => v.turma_id === turma.id);
    const associados = tipoAluno ? alunos : professores;
    const disponiveis = (tipoAluno ? data.alunos || [] : data.professores || []).filter(p => !associados.some(v => (tipoAluno ? v.aluno_id : v.professor_id) === p.id));
    useEffect(() => { dialog.current.showModal(); }, []);
    useEffect(() => { if (associando) selector.current?.focus(); }, [associando]);
    async function associar(e) {
        e.preventDefault();
        if (pending) return;
        setPending(true); setFeedback(null);
        try {
            const body = new FormData(e.currentTarget);
            await api('/api/admin/turmas', { method: 'POST', body });
            await refresh(); setAssociando(false);
            setFeedback({ success: true, message: tipoAluno ? 'Aluno associado à turma.' : 'Professor associado à turma.' });
        } catch (e) { setFeedback({ success: false, message: e.message }); }
        finally { setPending(false); }
    }
    return <dialog ref={dialog} className="turma-modal turma-detalhes-modal" aria-labelledby="turma-detalhes-titulo" onClose={onClose} onCancel={e => { if (pending) e.preventDefault(); }}>
        <div className="flex justify-between gap-4 items-start"><div><h2 id="turma-detalhes-titulo" className="text-xl font-bold">{turma.nome}</h2><p className="text-slate-300 text-sm mt-2">{turma.codigo} · {turma.ano_letivo} · {turma.turno}</p></div><button type="button" disabled={pending} aria-label="Fechar detalhes da turma" onClick={() => dialog.current.close()} className="text-2xl leading-none text-slate-300">×</button></div>
        <nav aria-label="Detalhes da turma" className="flex flex-wrap gap-2 my-6">{['Alunos', 'Professores', 'Disciplinas e cronograma'].map(t => <button key={t} disabled={pending} aria-current={tab === t ? 'page' : undefined} className={`px-4 py-3 rounded-xl ${tab === t ? 'bg-cyan-500/15 text-cyan-200 border border-cyan-400/30' : 'bg-white/5 text-slate-300'}`} onClick={() => { setTab(t); setAssociando(false); setFeedback(null); }}>{t}</button>)}</nav>
        {tab === 'Disciplinas e cronograma' ? <>
            <div className="flex flex-wrap justify-between items-center gap-4 mb-5"><h3 className="font-semibold">Horário semanal</h3><button data-ui-action type="button" onClick={() => setGerenciando(true)} className="bg-gradient-to-r from-cyan-500 to-blue-600 rounded-xl px-4 py-3 font-bold">Gerenciar disciplinas e horários</button></div>
            <GradeSemanal disciplinas={data.disciplinas || []} horarios={(data.horarios || []).filter(h => h.turma_id === turma.id)} navegar={false} />
            {gerenciando && <GerenciarCronograma turma={turma} data={data} onClose={() => setGerenciando(false)} />}
        </> : <>
            <div className="flex flex-wrap justify-between gap-3 items-center mb-4"><h3 className="font-semibold">{tab} associados ({associados.length})</h3><button data-ui-action type="button" disabled={pending || associando || !disponiveis.length} onClick={() => { setAssociando(true); setFeedback(null); }} className="bg-gradient-to-r from-cyan-500 to-blue-600 rounded-xl px-4 py-3 font-bold disabled:opacity-50">{tipoAluno ? 'Associar aluno' : 'Associar professor'}</button></div>
            {associados.length ? <ul className="turma-modal-lista">{associados.map(v => <li key={tipoAluno ? v.aluno_id : v.professor_id}><strong>{tipoAluno ? v.aluno : v.professor}</strong><span>{tipoAluno ? v.matricula : v.disciplina}</span></li>)}</ul> : <p className="text-slate-300 py-4">{tipoAluno ? 'Nenhum aluno associado a esta turma.' : 'Nenhum professor associado a esta turma.'}</p>}
            {associando && <form onSubmit={associar} className="mt-5 pt-3 border-t border-white/10" aria-busy={pending}>
                <input type="hidden" name="action" value={tipoAluno ? 'associate_student' : 'associate_teacher'} /><input type="hidden" name="turma_id" value={turma.id} />
                <label className="turma-field"><span>{tipoAluno ? 'Aluno para associar' : 'Professor para associar'}</span><select ref={selector} required name={tipoAluno ? 'aluno_id' : 'professor_id'} defaultValue=""><option value="">Selecione {tipoAluno ? 'um aluno' : 'um professor'}</option>{disponiveis.map(p => <option key={p.id} value={p.id}>{p.nome} · {tipoAluno ? p.matricula : p.disciplinas}</option>)}</select></label>
                {!tipoAluno && <p className="mt-3 text-sm text-slate-300">As disciplinas do professor serão vinculadas à turma automaticamente.</p>}
                <div className="flex justify-end gap-3 mt-4"><button data-ui-action type="button" disabled={pending} onClick={() => setAssociando(false)} className="rounded-xl border border-white/20 px-4 py-3">Cancelar associação</button><button data-ui-action disabled={pending} className="rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-3 font-bold">{pending ? 'Associando…' : 'Confirmar associação'}</button></div>
            </form>}
            {!disponiveis.length && <p className="text-slate-300 mt-4 text-sm">Não há outros {tipoAluno ? 'alunos' : 'professores'} disponíveis para associação.</p>}
            {feedback && <p role={feedback.success ? 'status' : 'alert'} className={`mt-4 ${feedback.success ? 'text-green-200' : 'text-red-200'}`}>{feedback.message}</p>}
        </>}
    </dialog>;
}


function GerenciarCronograma({ turma, data, onClose }) {
    const dialog = useRef(null);
    useEffect(() => { dialog.current.showModal(); }, []);
    return <dialog ref={dialog} className="turma-modal turma-detalhes-modal" aria-labelledby="gerenciar-cronograma-titulo" onClose={e => { e.stopPropagation(); onClose(); }}>
        <div className="flex justify-between items-start gap-4"><div><h2 id="gerenciar-cronograma-titulo" className="text-xl font-bold">Gerenciar disciplinas e horários</h2><p className="text-sm text-slate-300 mt-2">{turma.nome} · {turma.codigo}</p></div><button type="button" aria-label="Fechar gerenciamento do cronograma" onClick={() => dialog.current.close()} className="text-2xl leading-none text-slate-300">×</button></div>
        <CronogramaTurma turmaFixa={turma.id} turmas={[turma]} disciplinas={data.disciplinas || []} horarios={data.horarios || []} mostrarGrade={false} />
    </dialog>;
}
