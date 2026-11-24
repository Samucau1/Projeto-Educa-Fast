import ShellPagina, { headPainel } from '../components/ShellPagina';
import { urlFor } from '../core/urls';
import { j } from '../core/formatos';

export const head = headPainel('aluno_painel.css');
export const bodyClass = 'app-page';
export const titulo = (d) => `${d.disciplina.nome} | Área do Aluno`;

export default function AlunoDisciplina({ d }) {
    const { aluno, disciplina } = d;
    return (
        <ShellPagina id="aluno-disciplina" titulo="Detalhes da disciplina">
            <header className="flex justify-between items-center mb-10">
                <div>
                    <p className="text-sm text-cyan-400 font-bold">Disciplina</p>
                    <h1 className="text-3xl font-bold">{j(disciplina.nome)}</h1>
                    <p className="text-gray-400">Código {j(disciplina.codigo)} · {j(disciplina.carga_horaria)}h</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="text-right">
                        <p className="text-sm font-bold">{j(aluno.nome)}</p>
                        <p className="text-[10px] text-cyan-400">Matrícula {j(aluno.matricula)}</p>
                    </div>
                    {aluno.foto_perfil
                        ? <img src={urlFor('document.perfil_arquivo', { filename: aluno.foto_perfil })} alt={`Foto de ${aluno.nome}`} className="w-12 h-12 rounded-full border-2 border-white/20 object-cover" />
                        : <div className="w-12 h-12 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 border-2 border-white/20"></div>}
                </div>
            </header>
            <section className="glass-card aluno-card rounded-[32px] p-8 mb-8">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-bold">Professores</h2>
                    <span className="text-sm text-gray-400">Vinculados à sua turma</span>
                </div>
                <div className="flex flex-wrap gap-2">
                    {disciplina.professores.length ? disciplina.professores.map((professor, i) => <span key={i} className="aluno-chip">{professor}</span>)
                        : <span className="text-sm text-gray-400">Nenhum professor associado.</span>}
                </div>
            </section>
            <section className="glass-card aluno-card rounded-[32px] p-8">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-bold">Atividades e Arquivos</h2>
                    <span className="text-sm text-gray-400">Materiais enviados pelo professor</span>
                </div>
                <div className="aluno-exclusive-activities">
                    {d.atividades.length ? d.atividades.map((atividade, i) => (
                        <article key={i} className="aluno-exclusive-activity">
                            <div>
                                <strong>{j(atividade.titulo)}</strong>{' '}
                                <span>{j(atividade.professor)} · Entrega: {j(atividade.data_entrega)}</span>
                                <p>{j(atividade.descricao)}</p>
                                <small>{j(atividade.data)}</small>
                            </div>
                            {atividade.arquivo && <a href={urlFor('document.download_arquivo', { filename: atividade.arquivo })}>Baixar arquivo</a>}
                        </article>
                    )) : <div className="aluno-activity-empty">Nenhuma atividade lançada nesta disciplina.</div>}
                </div>
            </section>
        </ShellPagina>
    );
}
