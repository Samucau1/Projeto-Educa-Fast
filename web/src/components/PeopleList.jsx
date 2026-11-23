import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ActionDialog } from './ActionDialog';

export function PeopleList({ people, tipo }) {
    const [busca, setBusca] = useState('');
    const lista = people.filter(p => `${p.nome} ${p.email} ${p.matricula || ''}`.toLocaleLowerCase('pt-BR').includes(busca.toLocaleLowerCase('pt-BR')));
    return <section className="glass-card rounded-2xl p-6 mt-6"><label className="block text-sm text-slate-300 mb-5">Pesquisar {tipo === 'aluno' ? 'alunos' : 'professores'}<input type="search" className="block w-full max-w-md bg-white/5 border border-white/10 rounded-xl p-3 mt-2 text-white" value={busca} onChange={e => setBusca(e.target.value)} /></label><div className="banco-table-wrapper overflow-auto"><table className="w-full text-left"><thead><tr><th>Nome</th><th>E-mail</th><th>{tipo === 'aluno' ? 'Matrícula' : 'Disciplina'}</th><th>Detalhes</th></tr></thead><tbody>{lista.map(p => <tr key={p.id} className="border-t border-white/10"><td>{p.nome}</td><td>{p.email}</td><td>{tipo === 'aluno' ? p.matricula : p.disciplina}</td><td><ActionDialog title={p.nome} label="Ver detalhes"><dl className="space-y-3"><div><dt className="text-slate-300">E-mail</dt><dd>{p.email}</dd></div><div><dt className="text-slate-300">{tipo === 'aluno' ? 'Matrícula' : 'Disciplina'}</dt><dd>{p.matricula || p.disciplina}</dd></div></dl><Link data-ui-action className="action-dialog-trigger mt-6" to={`/admin/${tipo === 'aluno' ? 'alunos' : 'professores'}/${p.id}`}>Abrir cadastro completo</Link></ActionDialog></td></tr>)}{!lista.length && <tr><td colSpan={4}>Nenhum registro encontrado.</td></tr>}</tbody></table></div></section>;
}
