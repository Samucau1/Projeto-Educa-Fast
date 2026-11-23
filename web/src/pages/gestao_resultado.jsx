import GestaoBase, { bodyGestao, tituloGestao } from '../components/GestaoBase';
import { urlFor } from '../core/urls';

export const bodyClass = bodyGestao();
export const titulo = tituloGestao('Gestão de acesso');

export default function GestaoResultado({ d }) {
    return (
        <GestaoBase titulo="Gestão de acesso" error={d.error}>
            <section className="panel result-card"><span className="eyebrow">GESTÃO DE ACESSO</span><h1>Confira os dados informados.</h1><p>Volte à lista de usuários para revisar o cadastro e tentar novamente.</p><a className="button button-primary" href={urlFor('gestao.usuarios')}>Voltar para usuários</a></section>
        </GestaoBase>
    );
}
