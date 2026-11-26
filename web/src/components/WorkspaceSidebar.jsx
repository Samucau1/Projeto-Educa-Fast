import Icon from './Icon';
import Marca from './Marca';
import { useApp } from '../core/contexto';
import { urlFor } from '../core/urls';

export const ROLE_LABELS = { supremo: 'ADM Supremo', superadmin: 'Superperfil', admin: 'Administrador', professor: 'Professor', aluno: 'Aluno' };

function NavLink({ endpoint, text, symbol, related = [] }) {
    const atual = useApp().global.endpoint;
    const active = atual === endpoint || related.includes(atual);
    return (
        <a href={urlFor(endpoint)} className={active ? 'active' : undefined} aria-current={active ? 'page' : undefined}>
            <Icon name={symbol} /> {text}{active && <span className="active-dot"></span>}
        </a>
    );
}

// ADM Supremo: dono da plataforma, enxerga as escolas e não os dados internos delas.
function SidebarSupremo({ g }) {
    return (
        <aside className="workspace-sidebar">
            <Marca escola={g.escola} />
            <div className="workspace-label">ESPAÇO DE TRABALHO <span>PLATAFORMA</span></div>
            <nav className="sidebar-nav" aria-label="Navegação principal">
                <span className="nav-section">PLATAFORMA</span>
                <NavLink endpoint="supremo.painel" text="Escolas" symbol="grid" />
            </nav>
            <div className="sidebar-bottom">
                <div className="account"><span className="avatar avatar-superadmin"><Icon name="shield" /></span><div><strong>{ROLE_LABELS.supremo}</strong><small title={g.sessao.user_email}>{g.sessao.user_email}</small></div><a href={urlFor('auth.logout')} aria-label="Sair do sistema" title="Sair do sistema"><Icon name="logout" /></a></div>
            </div>
        </aside>
    );
}

// Navegação principal por perfil (antes: partials/workspace_sidebar.html).
export default function WorkspaceSidebar() {
    const { global: g } = useApp();
    const role = g.sessao.user_role;
    const admin = role === 'admin' || role === 'superadmin';
    if (role === 'supremo') return <SidebarSupremo g={g} />;
    return (
        <aside className="workspace-sidebar">
            <Marca escola={g.escola} />
            <div className="workspace-label">ESPAÇO DE TRABALHO <span>ESCOLA</span></div>
            <nav className="sidebar-nav" aria-label="Navegação principal">
                {admin ? <>
                    <NavLink endpoint="home.admin_dashboard" text="Visão geral" symbol="grid" />
                    <span className="nav-section">PESSOAS & ACESSOS</span>
                    {role === 'superadmin' && <NavLink endpoint="gestao.usuarios" text="Usuários e permissões" symbol="users" />}
                    <NavLink endpoint="home.admin_cadastro_alunos" text="Alunos" symbol="cap" related={['home.admin_detalhes_aluno', 'home.admin_detalhes_aluno_legacy']} />
                    <NavLink endpoint="home.admin_cadastro_professores" text="Professores" symbol="book" related={['home.admin_detalhes_professor', 'home.admin_detalhes_professor_legacy']} />
                    <NavLink endpoint="home.admin_banco_dados" text="Registros acadêmicos" symbol="users" />
                    <span className="nav-section">ORGANIZAÇÃO DA ESCOLA</span>
                    <NavLink endpoint="home.admin_turmas" text="Turmas" symbol="grid" />
                    <NavLink endpoint="home.admin_disciplinas" text="Disciplinas" symbol="book" />
                    <NavLink endpoint="home.admin_comunicados" text="Publicar comunicado" symbol="mail" />
                </> : role === 'aluno' ? <>
                    <span className="nav-section">MINHA ESCOLA</span>
                    {g.endpoint === 'aluno.dashboard' ? <>
                        <button type="button" data-aluno-tab="disciplinas" className="active" aria-pressed="true"><Icon name="book" /> Disciplinas</button>
                        <button type="button" data-aluno-tab="notas" aria-pressed="false"><Icon name="cap" /> Minhas notas</button>
                        <button type="button" data-aluno-tab="documentos" aria-pressed="false"><Icon name="users" /> Documentos</button>
                    </> : <>
                        <NavLink endpoint="aluno.dashboard" text="Minhas disciplinas" symbol="book" related={['aluno.disciplina_detail']} />
                        <a href={`${urlFor('aluno.dashboard')}#notas`}><Icon name="cap" /> Minhas notas</a>
                        <a href={`${urlFor('aluno.dashboard')}#documentos`}><Icon name="users" /> Documentos</a>
                    </>}
                </> : role === 'professor' ? <>
                    <span className="nav-section">MINHA ESCOLA</span>
                    {g.endpoint === 'professor.dashboard' ? <>
                        <button type="button" data-professor-tab="turmas" className="active" aria-pressed="true"><Icon name="grid" /> Minhas turmas</button>
                        <button type="button" data-professor-tab="notas" aria-pressed="false"><Icon name="cap" /> Lançar notas</button>
                        <button type="button" data-professor-tab="documentos" aria-pressed="false"><Icon name="users" /> Documentos</button>
                    </> : <>
                        <NavLink endpoint="professor.dashboard" text="Minhas turmas" symbol="grid" />
                        <a href={`${urlFor('professor.dashboard')}#notas`}><Icon name="cap" /> Lançar notas</a>
                        <a href={`${urlFor('professor.dashboard')}#documentos`}><Icon name="users" /> Documentos</a>
                    </>}
                </> : null}
                <span className="nav-section">APRENDIZAGEM</span>
                <NavLink endpoint="cursos.biblioteca" text={role === 'aluno' ? 'Meus cursos' : 'Biblioteca de cursos'} symbol="book" related={['cursos.editor', 'cursos.aprender']} />
                {admin && <NavLink endpoint="cursos.gestao_turmas" text="Gestão acadêmica" symbol="grid" />}
                <span className="nav-section">VIDA ACADÊMICA</span>
                {role === 'aluno'
                    ? <NavLink endpoint="academico.meu_boletim" text="Boletim por período" symbol="cap" />
                    : <>
                        <NavLink endpoint="academico.painel" text="Diário e avaliações" symbol="cap" related={['academico.diario']} />
                        {admin && <>
                            <NavLink endpoint="academico.lista_reconciliacao" text="Revisar atribuições" symbol="users" related={['academico.reconciliar']} />
                            <NavLink endpoint="academico.notas_antigas" text="Histórico de notas" symbol="book" />
                        </>}
                    </>}
                <span className="nav-section">PRIVACIDADE</span>
                <NavLink endpoint="privacidade.meus_pedidos" text="Meus dados e direitos" symbol="shield" />
                {admin && <NavLink endpoint="privacidade.administrar" text="Atendimento LGPD" symbol="shield" />}
                <span className="nav-section">COMUNIDADE</span>
                <NavLink endpoint="escola.calendario_publicado" text="Calendário escolar" symbol="grid" />
                <NavLink endpoint="gestao.mensagens" text="Mensagens" symbol="mail" />
                {role === 'superadmin' && <NavLink endpoint="gestao.layout" text="Aparência" symbol="palette" />}
                {role === 'superadmin' && <NavLink endpoint="escola.configurar" text="Regras e identidade da escola" symbol="shield" />}
            </nav>
            <div className="sidebar-bottom">
                <div className="security-note"><Icon name="shield" /><div><strong>Sua escola, mais conectada</strong><p>Pessoas, aprendizado e comunicação no mesmo lugar.</p></div></div>
                <div className="account"><span className={`avatar avatar-${role}`}><Icon name={admin ? 'shield' : 'cap'} /></span><div><strong>{ROLE_LABELS[role] || 'Usuário'}</strong><small title={g.sessao.user_email}>{g.sessao.user_email}</small></div><a href={urlFor('auth.logout')} aria-label="Sair do sistema" title="Sair do sistema"><Icon name="logout" /></a></div>
            </div>
        </aside>
    );
}
