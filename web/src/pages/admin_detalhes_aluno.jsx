import ShellPagina, { headPainel } from '../components/ShellPagina';
import Token from '../components/Token';
import { useAbas } from '../components/abas';
import { AbasDocumentos, Campo, Foto, H4, ItemArquivo, ItemSolicitacao, Vazio } from '../components/detalhes';
import { urlFor } from '../core/urls';
import { j } from '../core/formatos';

export const head = headPainel('detalhes.css');
export const bodyClass = 'app-page';
export const titulo = () => 'Detalhes do Aluno | Educa Fast';

export default function AdminDetalhesAluno({ d }) {
    useAbas();
    const aluno = d.aluno;
    return (
        <ShellPagina id="admin-detalhes-aluno" titulo="Detalhes do aluno">
            <header className="flex justify-between items-center mb-10">
                <div>
                    <span className="eyebrow">GESTÃO ESCOLAR</span>
                    <h1 className="text-3xl font-bold">Detalhes do Aluno</h1>
                    <p className="text-gray-400">Acompanhe documentos, histórico e evolução acadêmica.</p>
                </div>
            </header>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <section className="glass-card detalhes-card p-8 rounded-[32px] text-center">
                    <Foto pessoa={aluno} />
                    <h2 className="text-2xl font-bold">{j(aluno.nome)}</h2>
                    <p className="text-cyan-400">Matrícula: {j(aluno.matricula)}</p>
                    <p className="text-gray-400 text-sm mt-2">Nasc: {j(aluno.data_nascimento)}</p>
                    <p className="text-gray-400 text-sm mt-1">{j(aluno.curso)}</p>
                    <p className="text-gray-500 text-xs mt-1">{j(aluno.email)}</p>
                    <form action={urlFor('home.admin_editar_aluno', { aluno_id: aluno.id })} method="post" encType="multipart/form-data" className="aluno-edit-form"><Token />
                        <h3>Editar Dados</h3>
                        <Campo rotulo="Foto de Perfil"><input name="foto_perfil" type="file" accept="image/png,image/jpeg" /></Campo>
                        <Campo rotulo="Nome"><input name="nome" type="text" defaultValue={j(aluno.nome)} required /></Campo>
                        <Campo rotulo="E-mail"><input name="email" type="email" defaultValue={j(aluno.email)} required /></Campo>
                        <div className="aluno-edit-grid">
                            <Campo rotulo="CPF"><input name="cpf" type="text" defaultValue={j(aluno.cpf_value)} /></Campo>
                            <Campo rotulo="Matrícula"><input name="matricula" type="text" defaultValue={j(aluno.matricula)} required /></Campo>
                        </div>
                        <Campo rotulo="Curso/Série"><input name="curso_serie" type="text" defaultValue={j(aluno.curso_value)} /></Campo>
                        <div className="aluno-edit-grid">
                            <Campo rotulo="Status">
                                <select name="status_matricula" defaultValue={['Ativo', 'Pendente', 'Inativo'].includes(aluno.status_value) ? aluno.status_value : ''}>
                                    <option value="">Não informado</option>
                                    <option value="Ativo">Ativo</option>
                                    <option value="Pendente">Pendente</option>
                                    <option value="Inativo">Inativo</option>
                                </select>
                            </Campo>
                            <Campo rotulo="Nascimento"><input name="data_nascimento" type="date" defaultValue={j(aluno.data_nascimento_value)} /></Campo>
                        </div>
                        <button>Salvar Alterações</button>
                    </form>
                </section>
                <section className="lg:col-span-2 glass-card detalhes-card p-8 rounded-[32px]">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-xl font-bold">Documentos do Aluno</h3>
                        <span className="text-sm text-cyan-400">Solicitações e arquivos</span>
                    </div>
                    <AbasDocumentos />
                    <div data-documento-panel="solicitacoes">
                        <form action={urlFor('home.admin_solicitar_documento_aluno', { aluno_id: aluno.id })} method="post" className="documento-request-form"><Token />
                            <Campo rotulo="Documento solicitado"><input name="titulo" type="text" placeholder="Ex: Comprovante de residência" required /></Campo>
                            <Campo rotulo="Orientação para o aluno"><textarea name="mensagem" placeholder="Informe prazo, formato ou observações importantes."></textarea></Campo>
                            <button>Disparar solicitação</button>
                        </form>
                        <form action={urlFor('document.upload_arquivo')} method="post" encType="multipart/form-data" className="documento-request-form mt-8"><Token />
                            <input type="hidden" name="aluno_id" value={aluno.id} />
                            <input type="hidden" name="redirect_to" value={urlFor('home.admin_detalhes_aluno', { aluno_id: aluno.id })} />
                            <Campo rotulo="Documentos do aluno"><input name="titulo" type="text" placeholder="Ex: Histórico escolar" required /></Campo>
                            <Campo rotulo="Arquivo"><input name="arquivo" type="file" required /></Campo>
                            <button>Enviar Arquivo</button>
                        </form>
                        <div className="mt-8">
                            <H4>Solicitações enviadas</H4>
                            {d.solicitacoes_documentos.length ? d.solicitacoes_documentos.map((s, i) => <ItemSolicitacao key={i} s={s} />)
                                : <Vazio>Nenhuma solicitação enviada para este aluno.</Vazio>}
                        </div>
                    </div>
                    <div className="hidden" data-documento-panel="enviados">
                        <H4>Documentos do aluno</H4>
                        {d.documentos.length ? d.documentos.map((documento, i) => <ItemArquivo key={i} titulo={documento.titulo} detalhe={j(documento.data_envio)} arquivo={documento.arquivo} />)
                            : <Vazio>Nenhum documento enviado para este aluno.</Vazio>}
                    </div>
                </section>
            </div>
        </ShellPagina>
    );
}
