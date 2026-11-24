import ShellPagina, { headPainel } from '../components/ShellPagina';
import Token from '../components/Token';
import { TabelaRolagem } from '../components/tabelas';
import { urlFor } from '../core/urls';
import { j } from '../core/formatos';

export const head = headPainel('admin_turmas.css');
export const bodyClass = 'app-page';
export const titulo = () => 'Turmas | Educa Fast';

function Campo({ rotulo, children }) {
    return (
        <label className="turma-field">
            <span>{rotulo}</span>{' '}
            {children}
        </label>
    );
}

function ListaVinculos({ titulo, itens, vazio, campos }) {
    return (
        <div className="glass-card turma-card rounded-[32px] p-8">
            <h2 className="text-xl font-bold">{titulo}</h2>
            <div className="turma-link-list">
                {itens.length ? itens.map((vinculo, i) => (
                    <article key={i} className="turma-link-item">
                        <div>
                            <h3>{j(vinculo[campos[0]])}</h3>
                            <p>{j(vinculo[campos[1]])}</p>
                        </div>
                        <div className="text-right">
                            <strong>{j(vinculo.turma)}</strong>{' '}
                            <span>{j(vinculo.codigo)}</span>
                        </div>
                    </article>
                )) : <div className="turma-empty">{vazio}</div>}
            </div>
        </div>
    );
}

function SelectTurma({ turmas }) {
    return (
        <Campo rotulo="Turma">
            <select name="turma_id" required>
                <option value="">Selecione uma turma</option>
                {turmas.map((turma) => <option key={turma.id} value={turma.id}>{turma.nome} - {turma.codigo}</option>)}
            </select>
        </Campo>
    );
}

export default function AdminTurmas({ d }) {
    const acao = urlFor('home.admin_turmas');
    return (
        <ShellPagina id="admin-turmas" titulo="Turmas">
            <header className="flex justify-between items-center mb-10">
                <div>
                    <span className="eyebrow">GESTÃO ESCOLAR</span>
                    <h1 className="text-3xl font-bold">Turmas</h1>
                    <p className="text-gray-400">Cadastre turmas e associe alunos e professores.</p>
                </div>
            </header>
            <div className="grid grid-cols-1 xl:grid-cols-[380px_minmax(0,1fr)] gap-8">
                <form action={acao} method="post" className="glass-card turma-card rounded-[32px] p-8"><Token />
                    <input type="hidden" name="action" value="create" />
                    <h2 className="text-xl font-bold">Nova Turma</h2>
                    <p className="mt-1 text-sm text-gray-400">Informe os dados principais da turma.</p>
                    {d.error && <div className="turma-alert">{d.error}</div>}
                    <Campo rotulo="Nome"><input name="nome" type="text" placeholder="Ex: 1º Ano A" required /></Campo>
                    <Campo rotulo="Código"><input name="codigo" type="text" placeholder="Ex: 1A-2026" required /></Campo>
                    <Campo rotulo="Ano letivo"><input name="ano_letivo" type="number" min="2000" step="1" placeholder="Ex: 2026" required /></Campo>
                    <Campo rotulo="Turno">
                        <select name="turno">
                            <option value="">Selecione o turno</option>
                            <option value="Matutino">Matutino</option>
                            <option value="Vespertino">Vespertino</option>
                            <option value="Noturno">Noturno</option>
                            <option value="Integral">Integral</option>
                        </select>
                    </Campo>
                    <button className="turma-submit">Cadastrar Turma</button>
                </form>
                <section className="glass-card turma-card rounded-[32px] p-8">
                    <div className="flex justify-between items-center mb-6">
                        <div>
                            <h2 className="text-xl font-bold">Turmas Cadastradas</h2>
                            <p className="text-sm text-gray-400">{d.turmas.length} registros encontrados</p>
                        </div>
                    </div>
                    <div className="turma-table-wrapper">
                        <TabelaRolagem>
                            <table className="w-full text-left">
                                <thead>
                                    <tr className="text-gray-500 text-xs uppercase tracking-wider">
                                        <th className="pb-4 font-medium">Nome</th>
                                        <th className="pb-4 font-medium">Código</th>
                                        <th className="pb-4 font-medium">Ano</th>
                                        <th className="pb-4 font-medium text-right">Turno</th>
                                    </tr>
                                </thead>
                                <tbody className="text-sm">
                                    {d.turmas.length ? d.turmas.map((turma) => (
                                        <tr key={turma.id} className="border-t border-white/5">
                                            <td className="py-4 font-medium text-white">{j(turma.nome)}</td>
                                            <td className="py-4 text-cyan-400">{j(turma.codigo)}</td>
                                            <td className="py-4 text-gray-400">{j(turma.ano_letivo)}</td>
                                            <td className="py-4 text-right text-gray-400">{j(turma.turno)}</td>
                                        </tr>
                                    )) : (
                                        <tr className="border-t border-white/5">
                                            <td className="py-6 text-gray-400" colSpan={4}>Nenhuma turma cadastrada.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </TabelaRolagem>
                    </div>
                </section>
            </div>
            <section className="grid grid-cols-1 xl:grid-cols-2 gap-8 mt-8">
                <form action={acao} method="post" className="glass-card turma-card rounded-[32px] p-8"><Token />
                    <input type="hidden" name="action" value="associate_student" />
                    <h2 className="text-xl font-bold">Associar Aluno</h2>
                    <p className="mt-1 text-sm text-gray-400">Vincule um aluno a uma turma cadastrada.</p>
                    <Campo rotulo="Aluno">
                        <select name="aluno_id" required>
                            <option value="">Selecione um aluno</option>
                            {d.alunos.map((aluno) => <option key={aluno.id} value={aluno.id}>{aluno.nome} - {aluno.matricula}</option>)}
                        </select>
                    </Campo>
                    <SelectTurma turmas={d.turmas} />
                    <button className="turma-submit">Associar Aluno</button>
                </form>
                <form action={acao} method="post" className="glass-card turma-card rounded-[32px] p-8"><Token />
                    <input type="hidden" name="action" value="associate_teacher" />
                    <h2 className="text-xl font-bold">Associar Professor</h2>
                    <p className="mt-1 text-sm text-gray-400">As disciplinas do professor serão vinculadas à turma automaticamente.</p>
                    <Campo rotulo="Professor">
                        <select name="professor_id" required>
                            <option value="">Selecione um professor</option>
                            {d.professores.map((professor) => <option key={professor.id} value={professor.id}>{professor.nome} - {j(professor.disciplinas)}</option>)}
                        </select>
                    </Campo>
                    <SelectTurma turmas={d.turmas} />
                    <button className="turma-submit">Associar Professor</button>
                </form>
            </section>
            <section className="grid grid-cols-1 xl:grid-cols-2 gap-8 mt-8">
                <ListaVinculos titulo="Alunos por Turma" itens={d.aluno_vinculos} vazio="Nenhum aluno associado ainda." campos={['aluno', 'matricula']} />
                <ListaVinculos titulo="Professores por Turma" itens={d.professor_vinculos} vazio="Nenhum professor associado ainda." campos={['professor', 'disciplina']} />
            </section>
            <section className="mt-8">
                <ListaVinculos titulo="Disciplinas puxadas dos Professores" itens={d.disciplina_vinculos} vazio="Nenhuma disciplina associada ainda." campos={['disciplina', 'disciplina_codigo']} />
            </section>
        </ShellPagina>
    );
}
