import Icon from './Icon';
import { ROLE_LABELS } from './WorkspaceSidebar';
import { useApp } from '../core/contexto';
import { urlFor } from '../core/urls';

// Barra superior com trilha e perfil (antes: partials/workspace_topbar.html).
export default function WorkspaceTopbar({ titulo }) {
    const role = useApp().global.sessao.user_role;
    return (
        <header className="topbar">
            <div className="breadcrumb">{role === 'supremo' ? 'Plataforma' : role === 'superadmin' || role === 'admin' ? 'Administração' : 'Minha escola'} <Icon name="chevron" /> <span>{titulo ?? 'Educa Fast'}</span></div>
            <div className="topbar-actions"><span className="access-label"><Icon name="shield" /> {ROLE_LABELS[role] || 'Usuário'}</span><a className="icon-button" href={urlFor('auth.logout')} title="Sair do sistema" aria-label="Sair do sistema"><Icon name="logout" /></a></div>
        </header>
    );
}
