import GestaoBase, { bodyGestao } from '../components/GestaoBase';
import Icon from '../components/Icon';
import { urlFor } from '../core/urls';

export const bodyClass = bodyGestao();
export const titulo = (d, g) => `${d.titulo} | ${g.escola?.nome ?? 'Educa Fast'}`;

export default function Erro({ d, g }) {
    const logado = Boolean(g.sessao.user_id);
    return (
        <GestaoBase titulo={d.titulo} error={d.error}>
            <section className="error-page panel">
                <span className="error-code">{d.codigo}</span><span className="error-symbol"><Icon name={d.codigo === 403 ? 'lock' : 'search'} /></span>
                <span className="eyebrow">VAMOS ENCONTRAR O CAMINHO</span><h1>{d.titulo}<span>.</span></h1><p>{d.mensagem}</p>
                <div className="error-actions"><a className="button button-primary" href={urlFor('home.home')}><Icon name="grid" /> {logado ? 'Voltar ao meu painel' : 'Ir para o login'}</a>{logado && <a className="button button-secondary" href={urlFor('gestao.mensagens')}>Ver mensagens</a>}</div>
            </section>
        </GestaoBase>
    );
}
