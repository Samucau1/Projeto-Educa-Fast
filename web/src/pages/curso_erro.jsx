import GestaoBase, { bodyGestao, tituloGestao } from '../components/GestaoBase';
import { urlFor } from '../core/urls';

export const bodyClass = bodyGestao();
export const titulo = tituloGestao('Operação indisponível');

export default function CursoErro({ d }) {
    return (
        <GestaoBase titulo="Operação indisponível" error={d.error}>
            <section className="panel" style={{ padding: '24px' }}><h1>Não foi possível concluir a operação</h1><p>Confira suas permissões e os dados informados.</p><a className="button button-primary" href={urlFor('cursos.biblioteca')}>Voltar aos cursos</a></section>
        </GestaoBase>
    );
}
