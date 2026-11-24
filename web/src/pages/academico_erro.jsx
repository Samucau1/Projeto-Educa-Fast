import GestaoBase, { bodyGestao, tituloGestao } from '../components/GestaoBase';
import { urlFor } from '../core/urls';

export const bodyClass = bodyGestao();
export const titulo = tituloGestao('Revisar operação acadêmica');

export default function AcademicoErro({ d }) {
    return (
        <GestaoBase titulo="Revisar operação acadêmica" error={d.error}>
            <section className="panel" style={{ padding: '24px' }}><h1>Confira os dados e as permissões</h1><p>Volte à página, recarregue os dados e tente novamente.</p><a className="button button-primary" href={urlFor('academico.painel')}>Voltar à área acadêmica</a></section>
        </GestaoBase>
    );
}
