import GestaoBase, { bodyGestao, tituloGestao } from '../components/GestaoBase';
import Token from '../components/Token';

export const bodyClass = bodyGestao();
export const titulo = tituloGestao('Sair da conta');

export default function Logout({ d }) {
    return (
        <GestaoBase titulo="Sair da conta" error={d.error}>
            <section className="panel" style={{ padding: '2rem' }}><h1>Sair da conta</h1><form method="post"><Token /><button className="button button-primary">Confirmar saída</button></form></section>
        </GestaoBase>
    );
}
