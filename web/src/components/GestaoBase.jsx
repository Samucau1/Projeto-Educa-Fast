import WorkspaceSidebar from './WorkspaceSidebar';
import WorkspaceTopbar from './WorkspaceTopbar';
import { useRotulosTabelas } from './tabelas';
import { useApp } from '../core/contexto';

// Layout padrão das telas de gestão (antes: gestao_base.html).
export default function GestaoBase({ titulo, error, children }) {
    const app = useApp();
    // ADM Supremo não é usuário de escola, mas usa o mesmo layout.
    const logado = Boolean(app.global.sessao.user_id || app.global.sessao.operador);
    useRotulosTabelas(app.chave);
    return (
        <>
            <a className="skip-link" href="#main-content">Pular para o conteúdo</a>
            {logado && <WorkspaceSidebar />}
            <div className={`workspace-main ${logado ? '' : 'public-workspace'}`}>
                {logado && <WorkspaceTopbar titulo={titulo} />}
                <main id="main-content" className="app-content">
                    {error && <div className="notice notice-error" role="alert">{error}</div>}
                    {app.mensagens.map(([categoria, mensagem], i) => categoria === 'error'
                        ? <div key={i} className="notice notice-error" role="alert">{mensagem}</div>
                        : <div key={i} className="notice notice-success" role="status">{mensagem}</div>)}
                    {children}
                </main>
            </div>
        </>
    );
}

// Título da aba do navegador: "{página} | {escola}".
export function tituloGestao(pagina) {
    return (_d, g) => `${pagina ?? 'Gestão'} | ${g.escola?.nome ?? 'Educa Fast'}`;
}

export function bodyGestao(extra = '') {
    return `app-page native-page ${extra}`;
}
