import WorkspaceSidebar from './WorkspaceSidebar';
import WorkspaceTopbar from './WorkspaceTopbar';
import { useRotulosTabelas } from './tabelas';
import { useApp } from '../core/contexto';
import { css, headWorkspace } from '../core/head';

// Estrutura das telas de painel (admin, professor e aluno): mesma marcação do shell original,
// com barra lateral, barra superior e conteúdo em main.app-content.
export default function ShellPagina({ id, titulo, children }) {
    const app = useApp();
    useRotulosTabelas(app.chave);
    return (
        <>
            <a className="skip-link" href="#main-content">Pular para o conteúdo</a>
            <div id={`${id}-root`} className="flex w-full" data-react-shell data-react-template={`${id}-template`}>
                <div className="react-shell flex w-full">
                    <WorkspaceSidebar />
                    <div className="workspace-main">
                        <WorkspaceTopbar titulo={titulo} />
                        <main id="main-content" className="app-content">
                            {children}
                        </main>
                    </div>
                </div>
            </div>
        </>
    );
}

// <head> das telas de painel: utilitários, painel, CSS da página e depois o workspace.
export function headPainel(...extras) {
    return (g) => [css('utilities.css'), css('painel.css'), ...extras.map(css), ...headWorkspace(g)];
}
