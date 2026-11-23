import React, { Fragment, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { Pagination } from '../components/Pagination';
import { AdminSidebar } from '../components/Navigation';

export default function AdminBancoDados({ data }) {
    const [records, setRecords] = useState(data);
    const { alunos = [], professores = [], matriculas_hoje = 0, matriculas_pendentes = 0, total_alunos = 0, total_professores = 0 } = records;
    const [search, setSearch] = useState('');
    const [type, setType] = useState('todos');
    const [page, setPage] = useState(1);
    const [size, setSize] = useState(20);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const query = new URLSearchParams({ search, type, page, page_size: size }).toString();
    useEffect(() => {
        const controller = new AbortController();
        setBusy(true); setError('');
        const timer = setTimeout(() => {
            api(`/api/admin/registros?${query}`, { signal: controller.signal })
                .then(setRecords).catch(e => { if (e.name !== 'AbortError') setError(e.message); })
                .finally(() => { if (!controller.signal.aborted) setBusy(false); });
        }, 250);
        return () => { clearTimeout(timer); controller.abort(); };
    }, [query]);

    async function exportCsv() {
        let result;
        try { result = await api(`/api/admin/registros?${query}&export=1`); }
        catch (e) { setError(e.message); return; }
        const rows = [
            ['Identificação', 'Nome', 'E-mail', 'Tipo', 'Detalhe', 'Status'],
            ...result.alunos.map((aluno) => [aluno.matricula, aluno.nome, aluno.email, 'Aluno', aluno.curso, aluno.status]),
            ...result.professores.map((professor) => [`PROF-${professor.id}`, professor.nome, professor.email, 'Professor', professor.disciplina, 'Ativo']),
        ];
        const cell = (value) => {
            const text = String(value ?? '');
            return '"' + (/^[=+@\-]/.test(text) ? "'" : '') + text.replaceAll('"', '""') + '"';
        };
        const csv = rows.map((row) => row.map(cell).join(';')).join('\r\n');
        const url = URL.createObjectURL(new Blob(['\ufeff', csv], { type: 'text/csv;charset=utf-8' }));
        const link = document.createElement('a');
        link.href = url;
        link.download = 'registros-academicos.csv';
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
    return <>

    <AdminSidebar />

    <main className="flex-1 p-10 overflow-y-auto">
        <header className="flex flex-col gap-5 mb-10 lg:flex-row lg:items-center lg:justify-between">
            <div>
                <h1 className="text-3xl font-bold">Banco de Dados</h1>
                <p className="text-gray-400">Consulta e gerenciamento dos registros acadêmicos.</p>
            </div>
            <div className="flex flex-wrap items-center gap-4">
                <button data-ui-action type="button" onClick={exportCsv} className="banco-action-button">

                    Exportar CSV
                </button>
                <div className="flex items-center gap-4">
                    <div className="text-right">
                        <p className="text-sm font-bold">Admin Secretaria</p>
                        <p className="text-[10px] text-cyan-400">Online agora</p>
                    </div>
                    <div className="w-12 h-12 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 border-2 border-white/20"></div>
                </div>
            </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
            <div className="glass-card p-6 rounded-3xl">
                <p className="text-gray-400 text-sm">Registros de Alunos</p>
                <h2 className="text-4xl font-bold mt-2">{total_alunos}</h2>
                <div className="mt-4 text-xs text-green-400">Base acadêmica ativa</div>
            </div>
            <div className="glass-card p-6 rounded-3xl">
                <p className="text-gray-400 text-sm">Registros de Professores</p>
                <h2 className="text-4xl font-bold mt-2">{total_professores}</h2>
                <div className="mt-4 text-xs text-cyan-400">Equipe docente</div>
            </div>
            <div className="glass-card p-6 rounded-3xl">
                <p className="text-gray-400 text-sm">Pendências</p>
                <h2 className="text-4xl font-bold mt-2">{matriculas_pendentes}</h2>
                <div className="mt-4 text-xs text-yellow-400">Documentos e validações</div>
            </div>
            <div className="glass-card p-6 rounded-3xl">
                <p className="text-gray-400 text-sm">Atualizações Hoje</p>
                <h2 className="text-4xl font-bold mt-2">{matriculas_hoje}</h2>
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
                        <input id="banco-search-input" aria-label="Pesquisar registros" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} type="search" placeholder="Pesquisar por nome ou ID..." />
                    </label>
                    <select id="banco-type-select" value={type} onChange={(event) => { setType(event.target.value); setPage(1); }} className="banco-select" aria-label="Tipo de registro">
                        <option value="todos">Todos os Tipos</option>
                        <option value="aluno">Alunos</option>
                        <option value="professor">Professores</option>
                    </select>
                </div>
            </div>

            {error && <p role="alert">{error}</p>}
            <div className="banco-table-wrapper" aria-busy={busy}>
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
                        {alunos.map((aluno, index1) => <Fragment key={aluno?.id ?? index1}>
                        <tr className="border-t border-white/5 banco-row" data-type="aluno" data-search={`${aluno.matricula} ${aluno.nome} ${aluno.email} ${aluno.curso} ${aluno.status}`}>
                            <td className="py-4 font-medium text-white">{aluno.matricula}</td>
                            <td className="py-4">
                                <span className="block font-medium text-white">{aluno.nome}</span>
                                <span className="text-xs text-gray-500">{aluno.email}</span>
                            </td>
                            <td className="py-4"><span className="type-pill tipo-aluno">Aluno</span></td>
                            <td className="py-4 text-gray-400">{aluno.curso}</td>
                            <td className="py-4"><span className={`status-pill ${aluno.status_class}`}>{aluno.status}</span></td>
                            <td className="py-4 text-right">
                                <Link data-ui-action to={`/admin/alunos/${encodeURIComponent(aluno.id)}`} className="ui-button">Ver detalhes</Link>
                            </td>
                        </tr>
                        </Fragment>)}

                        {professores.map((professor, index2) => <Fragment key={professor?.id ?? index2}>
                        <tr className="border-t border-white/5 banco-row" data-type="professor" data-search={`${professor.id} ${professor.nome} ${professor.email} ${professor.cpf} ${professor.disciplina}`}>
                            <td className="py-4 font-medium text-white">PROF-{professor.id}</td>
                            <td className="py-4">
                                <span className="block font-medium text-white">{professor.nome}</span>
                                <span className="text-xs text-gray-500">{professor.email}</span>
                            </td>
                            <td className="py-4"><span className="type-pill tipo-professor">Professor</span></td>
                            <td className="py-4 text-gray-400">{professor.disciplina}</td>
                            <td className="py-4"><span className="status-pill status-active">Ativo</span></td>
                            <td className="py-4 text-right">
                                <Link data-ui-action to={`/admin/professores/${encodeURIComponent(professor.id)}`} className="ui-button">Ver detalhes</Link>
                            </td>
                        </tr>
                        </Fragment>)}

                        {!alunos.length && !professores.length && <tr id="banco-empty-row" className="border-t border-white/5">
                            <td className="py-6 text-gray-400" colSpan="6">Nenhum registro encontrado para o filtro selecionado.</td>
                        </tr>}

</tbody>
                </table>
            </div>
            <Pagination pagination={records.pagination} busy={busy} onPage={setPage} onSize={n => { setSize(n); setPage(1); }} />
        </section>
    </main>
    </>;
}
