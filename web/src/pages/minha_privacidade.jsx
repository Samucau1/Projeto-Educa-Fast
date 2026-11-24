import GestaoBase, { bodyGestao } from '../components/GestaoBase';
import Token from '../components/Token';
import { urlFor } from '../core/urls';
import { dataBR } from '../core/formatos';

export const bodyClass = bodyGestao();
export const titulo = (d, g) => `${d.administracao ? 'Atendimento de privacidade' : 'Meus dados e privacidade'} | ${g.escola?.nome ?? 'Educa Fast'}`;

export default function MinhaPrivacidade({ d }) {
    const pageTitle = d.administracao ? 'Atendimento de privacidade' : 'Meus dados e privacidade';
    return (
        <GestaoBase titulo={pageTitle} error={d.error}>
            <section className="page-heading"><div><span className="eyebrow">PROTEÇÃO DE DADOS</span><h1>{pageTitle}<span>.</span></h1><p>Pedidos com protocolo e respostas registradas.</p></div><a className="button" href={urlFor('privacidade.aviso')}>Aviso de privacidade</a></section>
            {!d.administracao && (
                <section className="panel" style={{ padding: '2rem' }}><h2>Acesse seus dados</h2><p>Baixe uma cópia dos dados estruturados da sua conta. Documentos continuam disponíveis nas áreas de origem. O contato da instituição pode fornecer explicação e atendimento completo.</p>
                    <form method="post" action={urlFor('privacidade.exportar')}><Token /><button className="button button-primary">Baixar meus dados (JSON)</button></form>
                    <h2>Nova solicitação</h2><form method="post"><Token /><label>Direito solicitado <select name="tipo" required>{Object.entries(d.tipos).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label><p><label>Descreva o pedido sem documentos de identidade ou dados sensíveis<br /><textarea name="detalhe" maxLength={2000} rows={4} style={{ width: '100%' }}></textarea></label></p><button className="button button-primary">Registrar solicitação</button></form></section>
            )}
            <section className="panel" style={{ padding: '2rem', marginTop: '24px' }}><h2>{d.administracao ? 'Fila de atendimento' : 'Meus protocolos'}</h2>
                {d.pedidos.length ? d.pedidos.map((p) => (
                    <article key={p.id} className="message-card"><div className="message-content"><h3>Protocolo {p.id} · {d.tipos[p.tipo] ?? p.tipo}</h3><p>{dataBR(p.criado_em)} · {p.status}{d.administracao && <> · Conta {p.usuario_id}</>}</p><p style={{ whiteSpace: 'pre-wrap' }}>{p.detalhe}</p>{p.resposta && <p style={{ whiteSpace: 'pre-wrap' }}><strong>Resposta:</strong> {p.resposta}</p>}
                        {d.administracao && !['concluido', 'indeferido'].includes(p.status) && <form method="post" action={urlFor('privacidade.responder', { pedido_id: p.id })}><Token /><select name="status"><option value="em_analise">Em análise</option><option value="concluido">Concluído</option><option value="indeferido">Indeferido</option></select><p><label>Resposta e justificativa<br /><textarea name="resposta" required maxLength={2000} rows={3} style={{ width: '100%' }}></textarea></label></p><button className="button button-primary">Registrar resposta</button></form>}</div></article>
                )) : <p>Nenhum pedido registrado.</p>}
            </section>
            {d.administracao && <nav aria-label="Páginas de pedidos">{d.pagina > 1 && <a className="button" href={urlFor('privacidade.administrar', { pagina: d.pagina - 1 })}>Anterior</a>}<span>Página {d.pagina}</span>{d.proxima && <a className="button" href={urlFor('privacidade.administrar', { pagina: d.pagina + 1 })}>Próxima</a>}</nav>}
        </GestaoBase>
    );
}
