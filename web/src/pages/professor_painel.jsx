import ShellPagina, { headPainel } from '../components/ShellPagina';
import Token from '../components/Token';
import { useAbas } from '../components/abas';
import { TabelaRolagem } from '../components/tabelas';
import { urlFor } from '../core/urls';
import { j } from '../core/formatos';

export const head = headPainel('professor_painel.css');
export const bodyClass = 'app-page';
export const titulo = () => 'Área do Professor | Educa Fast';

const TH = ({ children }) => <th className="pb-4 font-medium">{children}</th>;

function Aluno({ aluno }) {
    return (
        <td className="py-4">
            <span className="block font-bold text-white">{j(aluno.nome)}</span>{' '}
            <span className="text-xs text-gray-500">{j(aluno.matricula)}</span>
        </td>
    );
}

function FormNota({ turma, aluno }) {
    return (
        <form action={urlFor('professor.salvar_nota')} method="post" className="professor-grade-form"><Token />
            <input type="hidden" name="turma_id" value={turma.id} />
            <input type="hidden" name="aluno_id" value={aluno.id} />
            <select name="disciplina_id" required>
                {turma.disciplinas.map((disciplina) => <option key={disciplina.id} value={disciplina.id}>{disciplina.nome}</option>)}
            </select>{' '}
            <input name="nota" type="number" min="0" max="10" step="0.01" placeholder="0-10" required />{' '}
            <input name="observacao" type="text" placeholder="Observação" />{' '}
            <button>Salvar nota</button>
        </form>
    );
}

function CabecalhoTurma({ turma, children }) {
    return (
        <div className={`flex flex-wrap items-start justify-between gap-4 ${children ? 'mb-5' : 'mb-4'}`}>
            <div>
                {children || <h3>{j(turma.nome)}</h3>}
                <p className="text-sm text-gray-400">{j(turma.codigo)} · {j(turma.ano_letivo)} · {j(turma.turno)}</p>
            </div>
            <span className="professor-pill">{turma.alunos.length} alunos</span>
        </div>
    );
}

export default function ProfessorPainel({ d }) {
    useAbas();
    const professor = d.professor;
    const diario = <a className="button button-primary" href={urlFor('academico.painel')}>Abrir diário por período</a>;
    return (
        <ShellPagina id="professor-painel" titulo="Área do professor">
            <header className="flex justify-between items-center mb-10">
                <div>
                    <span className="eyebrow">MINHA ESCOLA</span>
                    <h1 className="text-3xl font-bold">Olá, Prof. {j(professor.nome)}!</h1>
                    <p className="text-gray-400">{j(professor.disciplina)} · {j(professor.regime)}</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="text-right">
                        <p className="text-sm font-bold">{j(professor.email)}</p>
                        <p className="text-[10px] text-cyan-400">PROF-{professor.id}</p>
                    </div>
                    {professor.foto_perfil
                        ? <img src={urlFor('document.perfil_arquivo', { filename: professor.foto_perfil })} alt={`Foto de ${professor.nome}`} className="w-12 h-12 rounded-full border-2 border-white/20 object-cover" />
                        : <div className="w-12 h-12 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 border-2 border-white/20"></div>}
                </div>
            </header>

            <section data-professor-panel="turmas" className="space-y-6">
                <div className="flex justify-between items-center">
                    <h2 className="text-xl font-bold">Turmas</h2>
                    <span className="text-sm text-gray-400">Turmas associadas ao seu cadastro</span>
                </div>
                {d.turmas.length ? d.turmas.map((turma) => (
                    <article key={turma.id} className="glass-card professor-card rounded-[28px] p-6">
                        <CabecalhoTurma turma={turma}><h3 className="text-lg font-bold text-cyan-400">{j(turma.nome)}</h3></CabecalhoTurma>
                        <div className="mb-5">
                            <p className="text-xs uppercase tracking-wider text-gray-500 mb-2">Disciplinas nesta turma</p>
                            <div className="flex flex-wrap gap-2">
                                {turma.disciplinas.length ? turma.disciplinas.map((disciplina) => <span key={disciplina.id} className="professor-chip">{disciplina.nome}</span>)
                                    : <span className="text-sm text-gray-400">Nenhuma disciplina associada ao professor nesta turma.</span>}
                            </div>
                        </div>
                        <div className="professor-activity-panel">
                            <div>
                                <h4>Lançar atividade</h4>
                                <p>Publique uma atividade para esta turma.</p>
                            </div>
                            {turma.disciplinas.length ? (
                                <form action={urlFor('professor.lancar_atividade')} method="post" encType="multipart/form-data" className="professor-activity-form"><Token />
                                    <input type="hidden" name="turma_id" value={turma.id} />
                                    <select name="disciplina_id" required>
                                        {turma.disciplinas.map((disciplina) => <option key={disciplina.id} value={disciplina.id}>{disciplina.nome}</option>)}
                                    </select>{' '}
                                    <input name="titulo" type="text" placeholder="Título da atividade" required />{' '}
                                    <input name="data_entrega" type="date" />{' '}
                                    <input name="arquivo" type="file" />{' '}
                                    <textarea name="descricao" placeholder="Descrição da atividade"></textarea>{' '}
                                    <button>Lançar atividade</button>
                                </form>
                            ) : <p className="text-sm text-gray-400">Associe uma disciplina ao professor e à turma para lançar atividade.</p>}
                            <div className="professor-activity-list">
                                {turma.atividades.length ? turma.atividades.map((atividade, i) => (
                                    <article key={i}>
                                        <div>
                                            <strong>{j(atividade.titulo)}</strong>{' '}
                                            <span>{j(atividade.disciplina)} · Entrega: {j(atividade.data_entrega)}</span>
                                            <p>{j(atividade.descricao)}</p>
                                            {atividade.arquivo && <a href={urlFor('document.download_arquivo', { filename: atividade.arquivo })}>Baixar anexo</a>}
                                        </div>
                                        <small>{j(atividade.data)}</small>
                                    </article>
                                )) : <div className="professor-empty-line">Nenhuma atividade lançada para esta turma.</div>}
                            </div>
                        </div>
                        <div className="professor-table-wrapper">
                            <TabelaRolagem>
                                <table className="w-full text-left">
                                    <thead>
                                        <tr className="text-gray-500 text-xs uppercase tracking-wider">
                                            <TH>Aluno</TH><TH>Disciplina</TH><TH>Nota</TH><TH>Observação</TH><TH></TH>
                                        </tr>
                                    </thead>
                                    <tbody className="text-sm">
                                        {turma.alunos.length ? turma.alunos.map((aluno) => (
                                            <tr key={aluno.id} className="border-t border-white/5">
                                                <Aluno aluno={aluno} />
                                                <td className="py-4" colSpan={4}>
                                                    {turma.gerida ? diario
                                                        : turma.disciplinas.length ? <FormNota turma={turma} aluno={aluno} />
                                                            : <span className="text-gray-500">Associe uma disciplina ao professor e à turma para lançar nota.</span>}
                                                </td>
                                            </tr>
                                        )) : (
                                            <tr className="border-t border-white/5">
                                                <td className="py-6 text-gray-400" colSpan={5}>Nenhum aluno associado a esta turma.</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </TabelaRolagem>
                        </div>
                    </article>
                )) : (
                    <div className="glass-card professor-card rounded-[28px] p-6 text-gray-400">
                        Nenhuma turma associada ao seu cadastro.
                    </div>
                )}
            </section>

            <section data-professor-panel="notas" className="professor-panel-hidden">
                <div className="glass-card professor-card rounded-[32px] p-8 mb-8">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-xl font-bold">Lançar Notas</h2>
                        <a className="button button-primary" href={urlFor('academico.painel')}>Diário por turma, ano e período</a>
                        <span className="text-sm text-gray-400">Por turma, aluno e disciplina</span>
                    </div>
                    <div className="space-y-5">
                        {d.turmas.length ? d.turmas.map((turma) => (
                            <article key={turma.id} className="professor-doc-block">
                                <CabecalhoTurma turma={turma} />
                                {turma.alunos.length && turma.disciplinas.length ? (
                                    <div className="professor-table-wrapper">
                                        <TabelaRolagem>
                                            <table className="w-full text-left">
                                                <thead>
                                                    <tr className="text-gray-500 text-xs uppercase tracking-wider">
                                                        <TH>Aluno</TH><TH>Nota</TH>
                                                    </tr>
                                                </thead>
                                                <tbody className="text-sm">
                                                    {turma.alunos.map((aluno) => (
                                                        <tr key={aluno.id} className="border-t border-white/5">
                                                            <Aluno aluno={aluno} />
                                                            <td className="py-4">
                                                                {turma.gerida ? diario : <FormNota turma={turma} aluno={aluno} />}
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </TabelaRolagem>
                                    </div>
                                ) : <p className="text-sm text-gray-400">Esta turma precisa ter alunos e disciplinas para lançar notas.</p>}
                            </article>
                        )) : (
                            <div className="professor-doc-block">
                                <h3>Nenhuma turma disponível</h3>
                                <p className="text-sm text-gray-400">Quando a administração associar turmas ao seu cadastro, o lançamento de notas aparecerá aqui.</p>
                            </div>
                        )}
                    </div>
                </div>
                <div className="glass-card professor-card rounded-[32px] p-8">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-xl font-bold">Notas Lançadas</h2>
                        <span className="text-sm text-gray-400">Histórico recente</span>
                    </div>
                    <div className="professor-table-wrapper">
                        <TabelaRolagem>
                            <table className="w-full text-left">
                                <thead>
                                    <tr className="text-gray-500 text-xs uppercase tracking-wider">
                                        <TH>Aluno</TH><TH>Turma</TH><TH>Disciplina</TH><TH>Nota</TH><TH>Observação</TH><TH>Data</TH>
                                    </tr>
                                </thead>
                                <tbody className="text-sm">
                                    {d.notas.length ? d.notas.map((nota, i) => (
                                        <tr key={i} className="border-t border-white/5">
                                            <td className="py-4 font-medium text-white">{j(nota.aluno)}</td>
                                            <td className="py-4 text-gray-400">{j(nota.turma)}</td>
                                            <td className="py-4 text-gray-400">{j(nota.disciplina)}</td>
                                            <td className="py-4 text-cyan-400 font-bold">{j(nota.nota)}</td>
                                            <td className="py-4 text-gray-400">{j(nota.observacao)}</td>
                                            <td className="py-4 text-gray-400">{j(nota.data)}</td>
                                        </tr>
                                    )) : (
                                        <tr className="border-t border-white/5">
                                            <td className="py-6 text-gray-400" colSpan={6}>Nenhuma nota lançada até o momento.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </TabelaRolagem>
                    </div>
                </div>
            </section>

            <section data-professor-panel="documentos" className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_420px] professor-panel-hidden">
                <div className="glass-card professor-card rounded-[32px] p-8">
                    <h2 className="text-xl font-bold">Solicitações da Secretaria</h2>
                    <p className="mt-1 text-sm text-gray-400">Anexe aqui os documentos pedidos pela secretaria.</p>
                    {d.solicitacoes_documentos.length ? d.solicitacoes_documentos.map((solicitacao) => (
                        <article key={solicitacao.id} className="professor-doc-block">
                            <div className="flex flex-wrap items-start justify-between gap-3">
                                <div>
                                    <h3>{j(solicitacao.titulo)}</h3>
                                    <p className="text-sm text-gray-400">{j(solicitacao.mensagem)}</p>
                                    <span className="text-xs text-gray-500">{j(solicitacao.data)}</span>
                                </div>
                                <strong className={`professor-request-status professor-request-status-${solicitacao.status}`}>{j(solicitacao.status_label)}</strong>
                            </div>
                            {solicitacao.status !== 'enviado' && (
                                <form action={urlFor('professor.upload_documento_professor')} method="post" encType="multipart/form-data" className="professor-doc-form mt-4"><Token />
                                    <input type="hidden" name="solicitacao_id" value={solicitacao.id} />
                                    <label>
                                        <span>Arquivo</span>{' '}
                                        <input name="arquivo" type="file" required />
                                    </label>{' '}
                                    <button>Enviar documento</button>
                                </form>
                            )}
                        </article>
                    )) : (
                        <div className="professor-doc-block">
                            <h3>Nenhuma solicitação</h3>
                            <p className="text-sm text-gray-400">Quando a secretaria solicitar um documento, ele aparecerá aqui.</p>
                        </div>
                    )}
                </div>
                <div className="glass-card professor-card rounded-[32px] p-8">
                    <h2 className="text-xl font-bold">Documentos Enviados</h2>
                    <p className="mt-1 text-sm text-gray-400">Histórico dos arquivos respondidos à secretaria.</p>
                    <div className="mt-6 space-y-4">
                        {d.documentos.length ? d.documentos.map((documento, i) => (
                            <article key={i} className="professor-doc-item">
                                <div>
                                    <h3>{j(documento.titulo)}</h3>
                                    <p>{j(documento.disciplina)}</p>
                                    <span>{j(documento.data)}</span>
                                </div>
                                <a href={urlFor('document.download_arquivo', { filename: documento.arquivo })}>Baixar</a>
                            </article>
                        )) : (
                            <div className="professor-doc-item">
                                <div>
                                    <h3>Nenhum documento enviado</h3>
                                    <p>Os documentos enviados aparecerão aqui.</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </section>
        </ShellPagina>
    );
}
