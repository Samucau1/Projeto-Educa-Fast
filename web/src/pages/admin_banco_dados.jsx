import { useState } from 'react';
import ShellPagina, { headPainel } from '../components/ShellPagina';
import { TabelaRolagem } from '../components/tabelas';
import { urlFor } from '../core/urls';

export const head = headPainel('admin_banco_dados.css');
export const bodyClass = 'app-page';
export const titulo = () => 'Registros acadêmicos | Educa Fast';

export default function AdminBancoDados({ d }) {
    const [busca, setBusca] = useState('');
    const [tipo, setTipo] = useState('todos');
    const termo = busca.trim().toLowerCase();
    const visivel = (rowTipo, texto) => (tipo === 'todos' || rowTipo === tipo) && (!termo || texto.toLowerCase().includes(termo));
    const linhas = [
        ...d.alunos.map((aluno) => ({ chave: `a${aluno.id}`, tipo: 'aluno', busca: `${aluno.matricula} ${aluno.nome} ${aluno.email} ${aluno.curso} ${aluno.status}`, item: aluno })),
        ...d.professores.map((professor) => ({ chave: `p${professor.id}`, tipo: 'professor', busca: `${professor.id} ${professor.nome} ${professor.email} ${professor.cpf} ${professor.disciplina}`, item: professor })),
    ];
    const filtrou = busca !== '' || tipo !== 'todos';
    const visiveis = linhas.filter((l) => visivel(l.tipo, l.busca)).length;
    const classeLinha = (l) => `border-t border-white/5 banco-row${filtrou && !visivel(l.tipo, l.busca) ? ' hidden' : ''}`;
    return (
        <ShellPagina id="admin-banco-dados" titulo="Registros acadêmicos">
            <header className="flex flex-col gap-5 mb-10 lg:flex-row lg:items-center lg:justify-between">
                <div>
                    <span className="eyebrow">GESTÃO ESCOLAR</span>
                    <h1 className="text-3xl font-bold">Registros acadêmicos</h1>
                    <p className="text-gray-400">Consulta e gerenciamento dos registros acadêmicos.</p>
                </div>
                <div className="flex flex-wrap items-center gap-4">
                    <button className="banco-action-button">
                        Exportar CSV
                    </button>
                </div>
            </header>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
                <div className="glass-card p-6 rounded-3xl">
                    <p className="text-gray-400 text-sm">Registros de Alunos</p>
                    <h2 className="text-4xl font-bold mt-2">{d.total_alunos}</h2>
                    <div className="mt-4 text-xs text-green-400">Base acadêmica ativa</div>
                </div>
                <div className="glass-card p-6 rounded-3xl">
                    <p className="text-gray-400 text-sm">Registros de Professores</p>
                    <h2 className="text-4xl font-bold mt-2">{d.total_professores}</h2>
                    <div className="mt-4 text-xs text-cyan-400">Equipe docente</div>
                </div>
                <div className="glass-card p-6 rounded-3xl">
                    <p className="text-gray-400 text-sm">Pendências</p>
                    <h2 className="text-4xl font-bold mt-2">{d.matriculas_pendentes}</h2>
                    <div className="mt-4 text-xs text-yellow-400">Documentos e validações</div>
                </div>
                <div className="glass-card p-6 rounded-3xl">
                    <p className="text-gray-400 text-sm">Atualizações Hoje</p>
                    <h2 className="text-4xl font-bold mt-2">{d.matriculas_hoje}</h2>
                    <div className="mt-4 text-xs text-cyan-400">Cadastros e edições</div>
                </div>
            </div>
            <section className="glass-card p-8 rounded-[32px] banco-card">
                <div className="flex flex-col gap-4 mb-6 xl:flex-row xl:items-center xl:justify-between">
                    <div>
                        <h3 className="text-xl font-bold">Registros Acadêmicos</h3>
                        <p className="text-sm text-gray-400">Filtre por nome, e-mail, matrícula, CPF ou tipo.</p>
                    </div>
                    <div className="flex flex-col gap-3 sm:flex-row">
                        <label className="banco-search">
                            <input id="banco-search-input" type="search" placeholder="Pesquisar por nome ou ID..." value={busca} onChange={(e) => setBusca(e.target.value)} />
                        </label>
                        <select id="banco-type-select" className="banco-select" aria-label="Tipo de registro" value={tipo} onChange={(e) => setTipo(e.target.value)}>
                            <option value="todos">Todos os Tipos</option>
                            <option value="aluno">Alunos</option>
                            <option value="professor">Professores</option>
                        </select>
                    </div>
                </div>
                <div className="banco-table-wrapper">
                    <TabelaRolagem>
                        <table className="w-full text-left">
                            <thead>
                                <tr className="text-gray-500 text-xs uppercase tracking-wider">
                                    <th className="pb-4 font-medium">Identificação</th>
                                    <th className="pb-4 font-medium">Nome</th>
                                    <th className="pb-4 font-medium">Tipo</th>
                                    <th className="pb-4 font-medium">Detalhe</th>
                                    <th className="pb-4 font-medium">Status</th>
                                    <th className="pb-4 font-medium text-right">Ação</th>
                                </tr>
                            </thead>
                            <tbody className="text-sm">
                                {linhas.map((l) => l.tipo === 'aluno' ? (
                                    <tr key={l.chave} className={classeLinha(l)} data-type="aluno" data-search={l.busca}>
                                        <td className="py-4 font-medium text-white">{l.item.matricula}</td>
                                        <td className="py-4">
                                            <span className="block font-medium text-white">{l.item.nome}</span>{' '}
                                            <span className="text-xs text-gray-500">{l.item.email}</span>
                                        </td>
                                        <td className="py-4"><span className="type-pill tipo-aluno">Aluno</span></td>
                                        <td className="py-4 text-gray-400">{l.item.curso}</td>
                                        <td className="py-4"><span className={`status-pill ${l.item.status_class}`}>{l.item.status}</span></td>
                                        <td className="py-4 text-right">
                                            <a href={urlFor('home.admin_detalhes_aluno', { aluno_id: l.item.id })} className="banco-row-button">Gerenciar</a>
                                        </td>
                                    </tr>
                                ) : (
                                    <tr key={l.chave} className={classeLinha(l)} data-type="professor" data-search={l.busca}>
                                        <td className="py-4 font-medium text-white">PROF-{l.item.id}</td>
                                        <td className="py-4">
                                            <span className="block font-medium text-white">{l.item.nome}</span>{' '}
                                            <span className="text-xs text-gray-500">{l.item.email}</span>
                                        </td>
                                        <td className="py-4"><span className="type-pill tipo-professor">Professor</span></td>
                                        <td className="py-4 text-gray-400">{l.item.disciplina}</td>
                                        <td className="py-4"><span className="status-pill status-active">Ativo</span></td>
                                        <td className="py-4 text-right">
                                            <a href={urlFor('home.admin_detalhes_professor', { professor_id: l.item.id })} className="banco-row-button">Gerenciar</a>
                                        </td>
                                    </tr>
                                ))}
                                <tr id="banco-empty-row" className={`${filtrou && visiveis === 0 ? '' : 'hidden '}border-t border-white/5`}>
                                    <td className="py-6 text-gray-400" colSpan={6}>Nenhum registro encontrado para o filtro selecionado.</td>
                                </tr>
                                {!d.alunos.length && !d.professores.length && (
                                    <tr className="border-t border-white/5">
                                        <td className="py-6 text-gray-400" colSpan={6}>Nenhum registro cadastrado.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </TabelaRolagem>
                </div>
            </section>
        </ShellPagina>
    );
}
