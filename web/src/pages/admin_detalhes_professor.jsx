import ShellPagina, { headPainel } from '../components/ShellPagina';
import Token from '../components/Token';
import { useAbas } from '../components/abas';
import { AbasDocumentos, Campo, Foto, H4, ItemArquivo, ItemSolicitacao, Vazio } from '../components/detalhes';
import { urlFor } from '../core/urls';
import { j } from '../core/formatos';

export const head = headPainel('detalhes.css');
export const bodyClass = 'app-page';
export const titulo = () => 'Detalhes do Professor | Educa Fast';

const REGIMES = ['20 horas semanais', '30 horas semanais', '40 horas semanais', 'Dedicação exclusiva'];

export default function AdminDetalhesProfessor({ d }) {
    useAbas();
    const professor = d.professor;
    return (
        <ShellPagina id="admin-detalhes-professor" titulo="Detalhes do professor">
            <header className="flex justify-between items-center mb-10">
                <div>
                    <span className="eyebrow">GESTÃO ESCOLAR</span>
                    <h1 className="text-3xl font-bold">Detalhes do Professor</h1>
                    <p className="text-gray-400">Acompanhe cadastro, disciplinas, documentos e lançamentos.</p>
                </div>
            </header>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <section className="glass-card detalhes-card p-8 rounded-[32px] text-center">
                    <Foto pessoa={professor} />
                    <h2 className="text-2xl font-bold">{j(professor.nome)}</h2>
                    <p className="text-cyan-400">Professor: PROF-{professor.id}</p>
                    <p className="text-gray-400 text-sm mt-2">{j(professor.disciplina)}</p>
                    <p className="text-gray-400 text-sm mt-1">{j(professor.regime)}</p>
                    <p className="text-gray-500 text-xs mt-1">{j(professor.email)}</p>
                    <form action={urlFor('home.admin_editar_professor', { professor_id: professor.id })} method="post" encType="multipart/form-data" className="aluno-edit-form"><Token />
                        <h3>Editar Dados</h3>
                        <Campo rotulo="Foto de Perfil"><input name="foto_perfil" type="file" accept="image/png,image/jpeg" /></Campo>
                        <Campo rotulo="Nome"><input name="nome" type="text" defaultValue={j(professor.nome)} required /></Campo>
                        <Campo rotulo="E-mail"><input name="email" type="email" defaultValue={j(professor.email)} required /></Campo>
                        <div className="aluno-edit-grid">
                            <Campo rotulo="CPF"><input name="cpf" type="text" defaultValue={j(professor.cpf_value)} required /></Campo>
                            <Campo rotulo="Telefone"><input name="telefone" type="text" defaultValue={j(professor.telefone_value)} /></Campo>
                        </div>
                        <Campo rotulo="Disciplina Principal"><input name="disciplina_principal" type="text" defaultValue={j(professor.disciplina_value)} /></Campo>
                        <Campo rotulo="Formação Acadêmica"><input name="formacao_academica" type="text" defaultValue={j(professor.formacao_value)} /></Campo>
                        <div className="aluno-edit-grid">
                            <Campo rotulo="Regime">
                                <select name="regime_trabalho" defaultValue={REGIMES.includes(professor.regime_value) ? professor.regime_value : ''}>
                                    <option value="">Não informado</option>
                                    {REGIMES.map((r) => <option key={r} value={r}>{r}</option>)}
                                </select>
                            </Campo>
                            <Campo rotulo="Admissão"><input name="data_admissao" type="date" defaultValue={j(professor.data_admissao_value)} /></Campo>
                        </div>
                        <button>Salvar Alterações</button>
                    </form>
                </section>
                <div className="lg:col-span-2 space-y-8">
                    <div className="glass-card detalhes-card p-6 rounded-[24px]">
                        <div className="flex gap-4 border-b border-white/10" data-professor-section-tabs>
                            <button type="button" className="professor-section-tab pb-2 border-b-2 border-cyan-400 text-white" data-professor-section-tab="atuacao">Atuação</button>
                            <button type="button" className="professor-section-tab pb-2 text-gray-500" data-professor-section-tab="documentos">Documentos</button>
                        </div>
                    </div>
                    <section className="glass-card detalhes-card p-8 rounded-[32px]" data-professor-section-panel="atuacao">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold">Atuação do Professor</h3>
                            <span className="text-sm text-cyan-400">{j(professor.created_at_label)}</span>
                        </div>
                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                            <div>
                                <H4>Disciplinas associadas</H4>
                                {d.disciplinas.length ? d.disciplinas.map((disciplina, i) => (
                                    <div key={i} className="documento-request-item">
                                        <div>
                                            <span className="block text-white">{j(disciplina.nome)}</span>{' '}
                                            <span className="text-xs text-gray-500">{j(disciplina.codigo)} • {j(disciplina.carga_horaria)}h</span>
                                        </div>
                                        <span className="text-xs text-gray-500">{j(disciplina.data)}</span>
                                    </div>
                                )) : <Vazio>Nenhuma disciplina associada a este professor.</Vazio>}
                            </div>
                            <div>
                                <H4>Últimas notas lançadas</H4>
                                {d.notas.length ? d.notas.map((nota, i) => (
                                    <div key={i} className="documento-request-item">
                                        <div>
                                            <span className="block text-white">{j(nota.aluno)}</span>{' '}
                                            <span className="text-xs text-gray-500">{j(nota.disciplina)} • {j(nota.observacao)}</span>
                                        </div>
                                        <span className="documento-status documento-status-enviado">{j(nota.nota)}</span>
                                    </div>
                                )) : <Vazio>Nenhuma nota lançada por este professor.</Vazio>}
                            </div>
                        </div>
                        <div className="mt-8">
                            <H4>Documentos enviados pelo professor</H4>
                            {d.documentos.length ? d.documentos.map((documento, i) => <ItemArquivo key={i} titulo={documento.titulo} detalhe={`${j(documento.aluno)} • ${j(documento.disciplina)} • ${j(documento.data_envio)}`} arquivo={documento.arquivo} />)
                                : <Vazio>Nenhum documento enviado por este professor.</Vazio>}
                        </div>
                    </section>
                    <section className="hidden glass-card detalhes-card p-8 rounded-[32px]" data-professor-section-panel="documentos">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold">Documentos do Professor</h3>
                            <span className="text-sm text-cyan-400">Solicitações e arquivos</span>
                        </div>
                        <AbasDocumentos />
                        <div data-documento-panel="solicitacoes">
                            <form action={urlFor('home.admin_solicitar_documento_professor', { professor_id: professor.id })} method="post" className="documento-request-form"><Token />
                                <Campo rotulo="Documento solicitado"><input name="titulo" type="text" placeholder="Ex: Certificado atualizado" required /></Campo>
                                <Campo rotulo="Orientação para o professor"><textarea name="mensagem" placeholder="Informe prazo, formato ou observações importantes."></textarea></Campo>
                                <button>Disparar solicitação</button>
                            </form>
                            <form action={urlFor('document.upload_arquivo_professor', { professor_id: professor.id })} method="post" encType="multipart/form-data" className="documento-request-form mt-8"><Token />
                                <input type="hidden" name="redirect_to" value={urlFor('home.admin_detalhes_professor', { professor_id: professor.id })} />
                                <Campo rotulo="Documentos do professor"><input name="titulo" type="text" placeholder="Ex: Contrato, certificado ou aviso" required /></Campo>
                                <Campo rotulo="Arquivo"><input name="arquivo" type="file" required /></Campo>
                                <button>Enviar Arquivo</button>
                            </form>
                            <div className="mt-8">
                                <H4>Solicitações enviadas</H4>
                                {d.solicitacoes_documentos.length ? d.solicitacoes_documentos.map((s, i) => <ItemSolicitacao key={i} s={s} />)
                                    : <Vazio>Nenhuma solicitação enviada para este professor.</Vazio>}
                            </div>
                        </div>
                        <div className="hidden" data-documento-panel="enviados">
                            <H4>Documentos do professor</H4>
                            {d.arquivos_professor.length ? d.arquivos_professor.map((arquivo, i) => <ItemArquivo key={i} titulo={arquivo.titulo} detalhe={j(arquivo.data_envio)} arquivo={arquivo.arquivo} />)
                                : <Vazio>Nenhum arquivo enviado para este professor.</Vazio>}
                        </div>
                    </section>
                </div>
            </div>
        </ShellPagina>
    );
}
