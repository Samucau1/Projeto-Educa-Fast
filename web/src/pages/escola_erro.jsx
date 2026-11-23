import GestaoBase, { bodyGestao, tituloGestao } from '../components/GestaoBase';
import { urlFor } from '../core/urls';

export const bodyClass = bodyGestao();
export const titulo = tituloGestao('Revisar configuração');

export default function EscolaErro({ d }) {
    return (
        <GestaoBase titulo="Revisar configuração" error={d.error}>
            <section className="panel course-panel"><h1>Confira a configuração da escola</h1><p>Os dados anteriores foram preservados. Recarregue os formulários antes de tentar novamente.</p><a className="button button-primary" href={urlFor('escola.configurar')}>Voltar às configurações</a></section>
        </GestaoBase>
    );
}
