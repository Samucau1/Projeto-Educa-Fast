import { useState } from 'react';
import GestaoBase, { bodyGestao, tituloGestao } from '../components/GestaoBase';
import Icon from '../components/Icon';
import { urlFor } from '../core/urls';

export const bodyClass = bodyGestao('messages-page');
export const titulo = tituloGestao('Mensagens');

const normalizar = (texto) => texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

export default function Mensagens({ d, g }) {
    const comunicados = d.comunicados;
    const [termo, setTermo] = useState(null);
    const role = g.sessao.user_role;
    // Busca: compara com todo o texto do cartão, sem acentos.
    const textoCartao = (c) => `Comunicado da escola${c.created_at_label}${c.titulo}${c.mensagem} Toda a comunidade`;
    const visiveis = termo === null ? comunicados : comunicados.filter((c) => normalizar(textoCartao(c)).includes(termo));
    const contador = termo === null ? `${comunicados.length} mensagens` : `${visiveis.length}${visiveis.length === 1 ? ' mensagem' : ' mensagens'}`;
    return (
        <GestaoBase titulo="Mensagens" error={d.error}>
            <section className="page-heading"><div><span className="eyebrow">CONEXÃO COM A COMUNIDADE</span><h1>O que acontece na escola<span>.</span></h1><p>Avisos, novidades e informações importantes para todos.</p></div>{(role === 'superadmin' || role === 'admin') && <a className="button button-primary" href={urlFor('home.admin_comunicados')}><Icon name="plus" /> Novo comunicado</a>}</section>
            <section className="panel">
                <div className="messages-toolbar"><span className="messages-counter"><Icon name="mail" /><span id="messages-count" role="status" aria-live="polite">{contador}</span></span><label className="search-field"><Icon name="search" /><input id="messages-search" type="search" placeholder="Buscar nas mensagens" aria-label="Buscar nas mensagens" onInput={(e) => setTermo(normalizar(e.currentTarget.value.trim()))} /></label></div>
                <div className="message-list">
                    {comunicados.length ? comunicados.map((comunicado) => (
                        <article key={comunicado.id} className="message-card" data-message hidden={!visiveis.includes(comunicado)}><span className="message-symbol"><Icon name="mail" /></span><div className="message-content"><div className="message-meta"><span>Comunicado da escola</span><span>{comunicado.created_at_label}</span></div><h2>{comunicado.titulo}</h2><p className="message-text">{comunicado.mensagem}</p><span className="message-audience"><Icon name="users" /> Toda a comunidade</span></div></article>
                    )) : <div className="empty-state"><Icon name="mail" /><h3>As novidades chegam por aqui</h3><p>Nenhuma mensagem publicada. Os próximos comunicados da escola aparecerão neste espaço.</p></div>}
                    <div className="empty-state" id="messages-no-results" hidden={termo === null || visiveis.length !== 0}><Icon name="search" /><h3>Nenhuma mensagem encontrada</h3><p>Tente outra palavra na busca.</p></div>
                </div>
            </section>
            <p className="page-footnote"><Icon name="info" /> Exibindo até 100 mensagens recentes. Comunicados publicados pela administração.</p>
        </GestaoBase>
    );
}
