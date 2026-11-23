import React, { useContext, useState } from 'react';
import { api } from '../api';
import { PageDataContext } from './MutationForm';
import { GradeSemanal } from './GradeSemanal';

const dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'];
const vazio = { disciplina_id: '', dias: [], inicio: '', fim: '', horario_id: '' };
export function CronogramaTurma({ turmas, disciplinas, horarios, turmaFixa, mostrarGrade = true }) {
    const { refresh } = useContext(PageDataContext);
    const [turma, setTurma] = useState(turmaFixa ? String(turmaFixa) : '');
    const [form, setForm] = useState(vazio);
    const [feedback, setFeedback] = useState(null);
    const [pending, setPending] = useState(false);
    const grade = horarios.filter(h => h.turma_id === Number(turma));
    async function enviar(data) {
        setPending(true); setFeedback(null);
        try {
            const response = await api('/api/admin/turmas', { method: 'POST', body: data });
            await refresh(); setForm(vazio); setFeedback({ success: true, message: response.mensagem });
        } catch (e) { setFeedback({ success: false, message: e.message }); }
        finally { setPending(false); }
    }
    function salvar(e) {
        e.preventDefault();
        const data = new FormData(e.currentTarget);
        data.set('action', 'schedule'); data.set('turma_id', turma);
        enviar(data);
    }
    function remover(id) {
        const data = new FormData(); data.set('action', 'remove_schedule'); data.set('horario_id', id);
        enviar(data);
    }
    return <section className="glass-card turma-card rounded-2xl p-6 mt-8" aria-label="Cronograma semanal da turma">
        <h2 className="text-xl font-bold">Disciplinas e cronograma semanal</h2>
        <p className="text-sm text-slate-300 mt-1">Associe uma disciplina à turma e defina os dias e horários das aulas.</p>
        {!turmaFixa && <label className="turma-field max-w-md"><span>Turma do cronograma</span><select value={turma} onChange={e => { setTurma(e.target.value); setForm(vazio); setFeedback(null); }}><option value="">Selecione uma turma</option>{turmas.map(t => <option key={t.id} value={t.id}>{t.nome} · {t.codigo}</option>)}</select></label>}
        {turma && <>
            <form onSubmit={salvar} className="mt-5 space-y-4" aria-busy={pending}>
                <input type="hidden" name="horario_id" value={form.horario_id} />
                <div className="grid md:grid-cols-3 gap-4">
                    <label className="turma-field"><span>Disciplina do cronograma</span><select name="disciplina_id" required value={form.disciplina_id} onChange={e => setForm({ ...form, disciplina_id: e.target.value })}><option value="">Selecione uma disciplina</option>{disciplinas.map(d => <option key={d.id} value={d.id}>{d.nome}</option>)}</select></label>
                    <label className="turma-field"><span>Início da aula</span><input name="inicio" type="time" required value={form.inicio} onChange={e => setForm({ ...form, inicio: e.target.value })} /></label>
                    <label className="turma-field"><span>Fim da aula</span><input name="fim" type="time" required value={form.fim} onChange={e => setForm({ ...form, fim: e.target.value })} /></label>
                </div>
                <fieldset><legend className="text-sm text-slate-300 mb-2">Dias da semana</legend><div className="flex flex-wrap gap-4">{dias.map((dia, i) => <label key={dia} className="flex gap-2 items-center"><input type={form.horario_id ? 'radio' : 'checkbox'} name="dias" value={i} checked={form.dias.includes(i)} onChange={e => setForm({ ...form, dias: form.horario_id ? [i] : e.target.checked ? [...form.dias, i] : form.dias.filter(d => d !== i) })} />{dia}</label>)}</div></fieldset>
                <div className="flex gap-4 items-center"><button data-ui-action disabled={pending} className="bg-gradient-to-r from-cyan-500 to-blue-600 rounded-xl px-5 py-3 font-bold">{form.horario_id ? 'Salvar alteração do horário' : 'Associar disciplina e salvar horários'}</button>{form.horario_id && <button data-ui-action type="button" onClick={() => setForm(vazio)}>Cancelar edição</button>}</div>
            </form>
            {feedback && <p className={`my-4 ${feedback.success ? 'text-green-200' : 'text-red-200'}`} role={feedback.success ? 'status' : 'alert'}>{feedback.message}</p>}
            {mostrarGrade && <div className="mt-6"><GradeSemanal disciplinas={disciplinas} horarios={grade} navegar={false} /></div>}
            {grade.length > 0 && <div className="turma-table-wrapper mt-5"><table className="w-full text-left"><caption className="sr-only">Horários cadastrados nesta turma</caption><thead><tr><th>Disciplina</th><th>Dia</th><th>Horário</th><th>Ações</th></tr></thead><tbody>{grade.map(h => <tr key={h.id} className="border-t border-white/10"><td>{disciplinas.find(d => d.id === h.disciplina_id)?.nome}</td><td>{dias[h.dia_semana]}</td><td>{h.inicio} – {h.fim}</td><td><div className="flex gap-4"><button data-ui-action disabled={pending} className="text-cyan-300" onClick={() => { setForm({ disciplina_id: h.disciplina_id, dias: [h.dia_semana], inicio: h.inicio, fim: h.fim, horario_id: h.id }); setFeedback(null); }}>Editar horário</button><button data-ui-action disabled={pending} className="text-red-300" onClick={() => remover(h.id)}>Remover horário</button></div></td></tr>)}</tbody></table></div>}
        </>}
    </section>;
}
