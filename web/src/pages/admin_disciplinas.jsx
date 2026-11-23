import ShellPagina, { headPainel } from '../components/ShellPagina';
import Token from '../components/Token';
import { TabelaRolagem } from '../components/tabelas';
import { urlFor } from '../core/urls';

export const head = headPainel('admin_disciplinas.css');
export const bodyClass = 'app-page';
export const titulo = () => 'Disciplinas | Educa Fast';

export default function AdminDisciplinas({ d }) {
    return (
        <ShellPagina id="admin-disciplinas" titulo="Disciplinas">
            <header className="flex justify-between items-center mb-10">
                <div>
                    <span className="eyebrow">GESTÃO ESCOLAR</span>
                    <h1 className="text-3xl font-bold">Disciplinas</h1>
                    <p className="text-gray-400">Cadastre e acompanhe as disciplinas usadas em notas e documentos.</p>
                </div>
            </header>
            <div className="grid grid-cols-1 xl:grid-cols-[380px_minmax(0,1fr)] gap-8">
                <form action={urlFor('home.admin_disciplinas')} method="post" className="glass-card discipline-card rounded-[32px] p-8"><Token />
                    <input type="hidden" name="action" value="create" />
                    <h2 className="text-xl font-bold">Nova Disciplina</h2>
                    <p className="mt-1 text-sm text-gray-400">Informe os dados principais da disciplina.</p>
                    {d.error && <div className="discipline-alert">{d.error}</div>}
                    <label className="discipline-field">
                        <span>Nome</span>{' '}
                        <input name="nome" type="text" placeholder="Ex: Matemática" required />
                    </label>
                    <label className="discipline-field">
                        <span>Código</span>{' '}
                        <input name="codigo" type="text" placeholder="Ex: MAT" required />
                    </label>
                    <label className="discipline-field">
                        <span>Carga horária</span>{' '}
                        <input name="carga_horaria" type="number" min="0" step="1" placeholder="Ex: 80" required />
                    </label>
                    <button className="discipline-submit">Cadastrar Disciplina</button>
                </form>
                <section className="glass-card discipline-card rounded-[32px] p-8">
                    <div className="flex justify-between items-center mb-6">
                        <div>
                            <h2 className="text-xl font-bold">Disciplinas Cadastradas</h2>
                            <p className="text-sm text-gray-400">{d.disciplinas.length} registros encontrados</p>
                        </div>
                    </div>
                    <div className="discipline-table-wrapper">
                        <TabelaRolagem>
                            <table className="w-full text-left">
                                <thead>
                                    <tr className="text-gray-500 text-xs uppercase tracking-wider">
                                        <th className="pb-4 font-medium">Nome</th>
                                        <th className="pb-4 font-medium">Código</th>
                                        <th className="pb-4 font-medium text-right">Carga Horária</th>
                                    </tr>
                                </thead>
                                <tbody className="text-sm">
                                    {d.disciplinas.length ? d.disciplinas.map((disciplina) => (
                                        <tr key={disciplina.id} className="border-t border-white/5">
                                            <td className="py-4 font-medium text-white">{disciplina.nome}</td>
                                            <td className="py-4 text-cyan-400">{disciplina.codigo}</td>
                                            <td className="py-4 text-right text-gray-400">{disciplina.carga_horaria}h</td>
                                        </tr>
                                    )) : (
                                        <tr className="border-t border-white/5">
                                            <td className="py-6 text-gray-400" colSpan={3}>Nenhuma disciplina cadastrada.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </TabelaRolagem>
                    </div>
                </section>
            </div>
            <section className="grid grid-cols-1 xl:grid-cols-[380px_minmax(0,1fr)] gap-8 mt-8">
                <form action={urlFor('home.admin_disciplinas')} method="post" className="glass-card discipline-card rounded-[32px] p-8"><Token />
                    <input type="hidden" name="action" value="associate_teacher" />
                    <h2 className="text-xl font-bold">Associar Professor</h2>
                    <p className="mt-1 text-sm text-gray-400">Vincule um professor responsável à disciplina.</p>
                    <label className="discipline-field">
                        <span>Professor</span>{' '}
                        <select name="professor_id" required>
                            <option value="">Selecione um professor</option>
                            {d.professores.map((professor) => <option key={professor.id} value={professor.id}>{professor.nome} - {professor.disciplina}</option>)}
                        </select>
                    </label>
                    <label className="discipline-field">
                        <span>Disciplina</span>{' '}
                        <select name="disciplina_id" required>
                            <option value="">Selecione uma disciplina</option>
                            {d.disciplinas.map((disciplina) => <option key={disciplina.id} value={disciplina.id}>{disciplina.nome} - {disciplina.codigo}</option>)}
                        </select>
                    </label>
                    <button className="discipline-submit">Associar Professor</button>
                </form>
                <div className="glass-card discipline-card rounded-[32px] p-8">
                    <h2 className="text-xl font-bold">Professores por Disciplina</h2>
                    <div className="discipline-link-list">
                        {d.professor_vinculos.length ? d.professor_vinculos.map((vinculo, i) => (
                            <article key={i} className="discipline-link-item">
                                <div>
                                    <h3>{vinculo.professor}</h3>
                                    <p>{vinculo.data}</p>
                                </div>
                                <div className="text-right">
                                    <strong>{vinculo.disciplina}</strong>{' '}
                                    <span>{vinculo.codigo}</span>
                                </div>
                            </article>
                        )) : <div className="discipline-empty">Nenhum professor associado ainda.</div>}
                    </div>
                </div>
            </section>
        </ShellPagina>
    );
}
