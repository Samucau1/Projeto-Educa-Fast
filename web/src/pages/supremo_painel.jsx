import { useState } from 'react';
import GestaoBase, { bodyGestao } from '../components/GestaoBase';
import Icon from '../components/Icon';
import Token from '../components/Token';
import { TabelaRolagem } from '../components/tabelas';
import { dataBR } from '../core/formatos';
import { urlFor } from '../core/urls';
import { css as folha } from '../core/head';

export const bodyClass = bodyGestao();
// Utilitários de espaçamento já compilados do projeto (mesma folha das telas de painel).
export const css = [folha('utilities.css')];
export const titulo = () => 'Painel Supremo | Educa Fast';

// Código da escola: minúsculas, números e hífen (o mesmo formato validado no servidor).
function sugerirCodigo(nome) {
    return nome.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
        .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40);
}

function Situacao({ escola }) {
    return escola.ativa
        ? <span className="role-badge role-superadmin"><span></span>Ativa</span>
        : <span className="role-badge role-professor"><span></span>Desativada</span>;
}

function AlternarSituacao({ escola }) {
    if (escola.padrao) return <span className="role-badge role-admin"><span></span>Escola padrão</span>;
    return (
        <form method="post" action={urlFor('supremo.alterar_situacao', { escola_id: escola.id })}><Token />
            <input type="hidden" name="ativa" value={escola.ativa ? '0' : '1'} />
            {/* input em vez de button: ação secundária não deve ter o destaque dos botões de envio */}
            <input type="submit" className="button button-secondary" value={escola.ativa ? 'Desativar acesso' : 'Reativar acesso'} />
        </form>
    );
}

export default function SupremoPainel({ d }) {
    const [nome, setNome] = useState('');
    const [codigo, setCodigo] = useState('');
    const [codigoEditado, setCodigoEditado] = useState(false);
    const totais = d.totais;
    const cartoes = [
        ['Escolas na plataforma', totais.escolas, 'grid', 'cyan'],
        ['Escolas ativas', totais.ativas, 'check', 'green'],
        ['Alunos em todas as escolas', totais.alunos, 'cap', 'violet'],
        ['Professores em todas as escolas', totais.professores, 'book', 'amber'],
    ];

    return (
        <GestaoBase titulo="Escolas da plataforma">
            <section className="page-heading">
                <div><span className="eyebrow">PAINEL SUPREMO</span><h1>Todas as escolas, um só servidor<span>.</span></h1><p>Cada escola usa a própria área do banco de dados e só enxerga os próprios dados.</p></div>
                <span className="access-label"><Icon name="shield" /> {d.operador}</span>
            </section>

            <div className="stats-grid">
                {cartoes.map(([rotulo, valor, icone, cor]) => <article key={rotulo} className="stat-card"><span className={`stat-icon ${cor}`}><Icon name={icone} /></span><div><span>{rotulo}</span><strong>{valor}</strong></div></article>)}
            </div>

            <section className="panel mb-8" aria-labelledby="titulo-escolas">
                <div className="settings-card"><h2 id="titulo-escolas">Escolas cadastradas</h2><p>Desativar bloqueia o acesso da escola na hora, sem apagar nenhum dado. Reativar devolve o acesso.</p></div>
                <TabelaRolagem>
                    <table>
                        <thead><tr><th>Escola</th><th>Código</th><th>Superadmin</th><th>Usuários</th><th>Alunos</th><th>Professores</th><th>Turmas</th><th>Criada em</th><th>Situação</th><th>Acesso</th></tr></thead>
                        <tbody>
                            {d.escolas.map((escola) => (
                                <tr key={escola.id}>
                                    <td><strong>{escola.nome}</strong></td>
                                    <td>{escola.slug}</td>
                                    <td>{escola.erro ? escola.erro : (escola.superadmins.length ? escola.superadmins.join(', ') : 'Nenhum')}</td>
                                    <td>{escola.usuarios ?? '-'}</td>
                                    <td>{escola.alunos ?? '-'}</td>
                                    <td>{escola.professores ?? '-'}</td>
                                    <td>{escola.turmas ?? '-'}</td>
                                    <td>{dataBR(escola.criada_em)}</td>
                                    <td><Situacao escola={escola} /></td>
                                    <td><AlternarSituacao escola={escola} /></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </TabelaRolagem>
            </section>

            <form method="post" action={urlFor('supremo.criar')} className="panel settings-card" aria-labelledby="titulo-nova-escola"><Token />
                <h2 id="titulo-nova-escola">Nova escola</h2>
                <p>Cria a área da escola no banco e o superadmin dela. Depois disso, a direção da escola entra com o e-mail e a senha abaixo e cadastra o resto.</p>
                <div className="form-grid">
                    <label className="field" htmlFor="escola-nome">Nome da escola
                        <input id="escola-nome" name="nome" maxLength={120} required value={nome}
                            onChange={(e) => { setNome(e.target.value); if (!codigoEditado) setCodigo(sugerirCodigo(e.target.value)); }} />
                    </label>
                    <label className="field" htmlFor="escola-codigo">Código da escola (letras minúsculas, números e hífen)
                        <input id="escola-codigo" name="slug" minLength={3} maxLength={40} pattern="[a-z0-9][a-z0-9-]{1,38}[a-z0-9]" required value={codigo}
                            onChange={(e) => { setCodigo(e.target.value); setCodigoEditado(true); }} />
                    </label>
                    <label className="field" htmlFor="escola-admin-email">E-mail do superadmin da escola
                        <input id="escola-admin-email" name="admin_email" type="email" maxLength={120} autoComplete="off" required />
                    </label>
                    <label className="field" htmlFor="escola-admin-senha">Senha inicial do superadmin (mínimo 8 caracteres)
                        <input id="escola-admin-senha" name="admin_senha" type="password" minLength={8} autoComplete="new-password" required />
                    </label>
                </div>
                <footer className="settings-footer"><button type="submit" className="button button-primary"><Icon name="plus" /> Criar escola</button></footer>
            </form>
        </GestaoBase>
    );
}
