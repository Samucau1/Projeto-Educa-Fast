import { urlFor } from '../core/urls';

// Logotipo com sigla, nome e subtítulo da escola configurada.
export default function Marca({ escola }) {
    const nome = escola.nome ?? 'EducaFast';
    return (
        <a className="brand" href={urlFor('home.home')}>
            <span className="brand-mark">{escola.sigla ?? 'ef'}<span>↗</span></span>
            <span>{nome === 'EducaFast' ? <>educa<span className="brand-light">fast</span></> : nome}<small>{escola.subtitulo ?? 'GESTÃO ESCOLAR'}</small></span>
        </a>
    );
}
