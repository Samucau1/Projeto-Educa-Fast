import React from 'react';
import { Link } from 'react-router-dom';

const dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'];
export function GradeSemanal({ disciplinas, horarios, navegar = true }) {
    const mapa = new Map(disciplinas.map(d => [d.id, d]));
    const intervalos = [...new Set(horarios.map(h => `${h.inicio}|${h.fim}`))].sort();
    const semHorario = disciplinas.filter(d => !horarios.some(h => h.disciplina_id === d.id));
    const hoje = (new Date().getDay() + 6) % 7;
    return <>
        {horarios.some(h => h.demonstracao) && <p className="grade-aviso">Horários de demonstração · dados fictícios para testes</p>}
        <div className="grade-semanal" role="region" aria-label="Grade semanal de disciplinas" tabIndex={0}>
            <table>
                <caption className="sr-only">Disciplinas por dia da semana e horário</caption>
                <thead><tr><th scope="col">Horário</th>{dias.map((dia, i) => <th key={dia} scope="col" className={i === hoje ? 'grade-hoje' : ''}>{dia}{i === hoje && <small>Hoje</small>}</th>)}</tr></thead>
                <tbody>{intervalos.length ? intervalos.map(intervalo => {
                    const [inicio, fim] = intervalo.split('|');
                    return <tr key={intervalo}><th scope="row"><time>{inicio}</time><span>às</span><time>{fim}</time></th>{dias.map((dia, i) => {
                        const aulas = horarios.filter(h => h.dia_semana === i && h.inicio === inicio && h.fim === fim);
                        return <td key={dia} className={i === hoje ? 'grade-hoje' : ''}>{aulas.length ? aulas.map(h => {
                            const disciplina = mapa.get(h.disciplina_id);
                            const Aula = navegar ? Link : 'div';
                            return <Aula key={h.id} className="grade-aula" {...(navegar ? { to: `/aluno/disciplinas/${h.disciplina_id}` } : {})}><strong>{disciplina?.nome || 'Disciplina'}</strong><span>{h.turma}</span>{disciplina?.professores?.length > 0 && <small>{disciplina.professores.join(', ')}</small>}</Aula>;
                        }) : <span className="grade-vazio" aria-label="Sem aula">—</span>}</td>;
                    })}</tr>;
                }) : <tr><td colSpan={7} className="grade-sem-horarios">Os horários das aulas ainda não foram cadastrados.</td></tr>}</tbody>
            </table>
        </div>
        {navegar && semHorario.length > 0 && <section className="mt-6"><h3 className="font-semibold mb-3">Disciplinas sem horário definido</h3><div className="grade-pendentes">{semHorario.map(d => <Link key={d.id} to={`/aluno/disciplinas/${d.id}`}><strong>{d.nome}</strong><span>{d.codigo} · {d.carga_horaria}h</span></Link>)}</div></section>}
        {!disciplinas.length && <p className="mt-4 text-slate-300">Nenhuma disciplina associada. A secretaria precisa vincular seu cadastro.</p>}
    </>;
}
