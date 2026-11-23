import { useEffect } from 'react';
import Icon from '../components/Icon';
import Token from '../components/Token';
import WorkspaceSidebar from '../components/WorkspaceSidebar';
import WorkspaceTopbar from '../components/WorkspaceTopbar';
import { urlFor } from '../core/urls';

export const bodyClass = 'app-page users-page';
export const titulo = () => 'Usuários e permissões | Educa Fast';

const PERFIS = { superadmin: 'Superperfil', admin: 'Administrador', professor: 'Professor', aluno: 'Aluno' };
const OPCOES = [['aluno', 'cap', 'Consulta e aprendizado'], ['professor', 'book', 'Atividades e notas'], ['admin', 'shield', 'Gestão da escola']];
const RESUMO = { superadmin: 'Controle total do sistema', admin: 'Gestão acadêmica e comunicados', professor: 'Atividades e notas', aluno: 'Consulta de informações' };
const ROLES = ['superadmin', 'admin', 'professor', 'aluno'];
const RECURSOS = [['Criar alunos e professores', ['superadmin', 'admin']], ['Criar administradores e alterar perfis', ['superadmin']], ['Personalizar as cores do sistema', ['superadmin']], ['Publicar comunicados para todos', ['superadmin', 'admin']], ['Ler comunicados', ['superadmin', 'admin', 'professor', 'aluno']], ['Lançar atividades e notas', ['professor']], ['Consultar suas disciplinas e notas', ['aluno']]];

function RoleOptions({ selected = 'aluno' }) {
    return (
        <div className="role-options" role="group" aria-label="Perfil de acesso">
            {OPCOES.map(([role, symbol, description]) => <label key={role} className="role-option"><input type="radio" name="tipo" value={role} defaultChecked={role === selected} /><Icon name={symbol} /><strong>{PERFIS[role]}</strong><span>{description}</span><span className="role-check"><Icon name="check" /></span></label>)}
        </div>
    );
}

// Diálogos, filtros, abas e formulários de perfil (antes: js/paginas/super_usuarios.js).
function useComportamentos() {
    useEffect(() => {
        const limpar = [];
        const on = (el, ev, fn) => { el.addEventListener(ev, fn); limpar.push(() => el.removeEventListener(ev, fn)); };
        const labels = { aluno: 'Aluno', professor: 'Professor', admin: 'Administrador' };
        const descriptions = {
            aluno: 'O aluno pode consultar suas disciplinas, notas e mensagens.',
            professor: 'O professor pode lançar atividades e notas nas turmas vinculadas e ler mensagens.',
            admin: 'O administrador pode gerenciar cadastros, turmas, disciplinas e publicar comunicados.',
        };
        const createDialog = document.getElementById('create-dialog');
        const permissionDialog = document.getElementById('permission-dialog');
        const permissionForm = document.getElementById('permission-form');
        let editingUser = null;
        let trigger = null;

        function openDialog(dialog, button) {
            trigger = button || document.activeElement;
            if (!dialog.open) dialog.showModal();
        }
        document.querySelectorAll('[data-open-create]').forEach((button) => on(button, 'click', () => openDialog(createDialog, button)));
        document.querySelectorAll('[data-close-dialog]').forEach((button) => on(button, 'click', () => button.closest('dialog').close()));
        document.querySelectorAll('dialog').forEach((dialog) => {
            on(dialog, 'close', () => { if (trigger && trigger.isConnected) trigger.focus(); });
            on(dialog, 'click', (event) => {
                const rect = dialog.getBoundingClientRect();
                if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) dialog.close();
            });
        });

        function updateRole(form) {
            const selected = form.querySelector('input[name="tipo"]:checked');
            const role = selected ? selected.value : 'aluno';
            const isPermission = form.dataset.userForm === 'permission';
            const existing = isPermission && editingUser && ((role === 'aluno' && editingUser.tem_aluno) || (role === 'professor' && editingUser.tem_professor));
            const needsAcademic = role !== 'admin' && !existing;
            form.querySelector('[data-role-preview]').textContent = descriptions[role];
            form.querySelector('[data-academic-section]').hidden = !needsAcademic;
            form.querySelectorAll('[data-academic]').forEach((field) => {
                const show = needsAcademic && (field.dataset.academic === role || field.dataset.academic === 'nome');
                field.hidden = !show;
                field.querySelectorAll('input').forEach((input) => { input.disabled = !show; input.required = show; });
            });
            const preservedNote = form.querySelector('[data-existing-record]');
            if (preservedNote) preservedNote.hidden = !existing;
        }
        document.querySelectorAll('[data-user-form]').forEach((form) => {
            form.querySelectorAll('input[name="tipo"]').forEach((radio) => on(radio, 'change', () => updateRole(form)));
            updateRole(form);
            on(form, 'submit', () => {
                const button = form.querySelector('button[type="submit"]');
                button.disabled = true;
                button.textContent = 'Salvando…';
            });
        });
        document.querySelectorAll('[data-toggle-password]').forEach((button) => on(button, 'click', () => {
            const input = button.parentElement.querySelector('input');
            const visible = input.type === 'password';
            input.type = visible ? 'text' : 'password';
            button.setAttribute('aria-label', visible ? 'Ocultar senha' : 'Mostrar senha');
            button.setAttribute('aria-pressed', String(visible));
        }));
        function editUser(button, submitted) {
            editingUser = JSON.parse(button.dataset.editUser);
            permissionForm.reset();
            permissionForm.setAttribute('action', permissionForm.dataset.actionTemplate.replace(/\/0\/perfil$/, `/${editingUser.id}/perfil`));
            permissionForm.querySelectorAll('input[name="tipo"]').forEach((radio) => { radio.checked = radio.value === editingUser.tipo; });
            document.getElementById('edit-name').textContent = editingUser.nome;
            document.getElementById('edit-email').textContent = editingUser.email;
            document.getElementById('edit-avatar').textContent = editingUser.nome.slice(0, 2).toUpperCase();
            document.getElementById('edit-avatar').className = `avatar avatar-${editingUser.tipo}`;
            document.getElementById('current-role').textContent = labels[editingUser.tipo] || editingUser.tipo;
            permissionForm.elements.nome.value = editingUser.nome;
            if (submitted) {
                Object.keys(submitted).forEach((name) => {
                    if (['nome', 'cpf', 'matricula', 'tipo'].includes(name)) permissionForm.elements[name].value = submitted[name];
                });
            }
            updateRole(permissionForm);
            openDialog(permissionDialog, button);
        }
        document.querySelectorAll('[data-edit-user]').forEach((button) => on(button, 'click', () => editUser(button)));

        const search = document.getElementById('user-search');
        const roleFilter = document.getElementById('role-filter');
        const rows = Array.from(document.querySelectorAll('[data-user-row]'));
        const normalize = (text) => text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLocaleLowerCase('pt-BR');
        function filterUsers() {
            const term = normalize(search.value.trim());
            let count = 0;
            rows.forEach((row) => {
                const match = normalize(row.dataset.search).includes(term) && (!roleFilter.value || row.dataset.role === roleFilter.value);
                row.hidden = !match;
                if (match) count += 1;
            });
            document.getElementById('users-empty').hidden = count !== 0;
            document.getElementById('results-count').textContent = `${count} de ${rows.length} usuários`;
        }
        on(search, 'input', filterUsers);
        on(roleFilter, 'change', filterUsers);
        on(document.getElementById('clear-filters'), 'click', () => { search.value = ''; roleFilter.value = ''; filterUsers(); search.focus(); });

        const tabs = Array.from(document.querySelectorAll('[data-tab]'));
        function selectTab(tab) {
            tabs.forEach((item) => {
                const selected = item === tab;
                item.classList.toggle('active', selected);
                item.setAttribute('aria-selected', String(selected));
                item.tabIndex = selected ? 0 : -1;
                document.getElementById(item.dataset.tab).hidden = !selected;
            });
        }
        tabs.forEach((tab, index) => {
            on(tab, 'click', () => selectTab(tab));
            on(tab, 'keydown', (event) => {
                let next;
                if (event.key === 'ArrowRight') next = tabs[(index + 1) % tabs.length];
                if (event.key === 'ArrowLeft') next = tabs[(index + tabs.length - 1) % tabs.length];
                if (event.key === 'Home') next = tabs[0];
                if (event.key === 'End') next = tabs[tabs.length - 1];
                if (next) { event.preventDefault(); selectTab(next); next.focus(); }
            });
        });
        document.querySelectorAll('[data-dismiss-notice]').forEach((button) => on(button, 'click', () => { button.closest('.notice').remove(); }));
        if (createDialog.hasAttribute('data-open-on-load')) openDialog(createDialog);
        if (permissionDialog.dataset.openUser) {
            const button = document.querySelector(`[data-user-id="${permissionDialog.dataset.openUser}"]`);
            if (button) editUser(button, JSON.parse(permissionDialog.dataset.submitted || '{}'));
        }
        return () => {
            limpar.forEach((fn) => fn());
            document.querySelectorAll('dialog[open]').forEach((dialog) => dialog.close());
        };
    }, []);
}

export default function SuperUsuarios({ d, g, form, mensagens }) {
    useComportamentos();
    const usuarios = d.usuarios;
    const contar = (tipo) => usuarios.filter((u) => u.tipo === tipo).length;
    const valor = (campo) => (d.error ? form[campo] ?? '' : '');
    return (
        <>
            <a className="skip-link" href="#main-content">Pular para o conteúdo</a>
            <WorkspaceSidebar />
            <div className="workspace-main">
                <WorkspaceTopbar titulo="Usuários e permissões" />
                <main id="main-content">
                    <section className="page-heading"><div><span className="eyebrow">PESSOAS & ACESSOS</span><h1>Usuários e permissões<span>.</span></h1><p>As pessoas certas, com os acessos certos. Tudo em um só lugar.</p></div><button className="button button-primary" type="button" data-open-create><Icon name="plus" /> Novo usuário</button></section>
                    {mensagens.map(([, message], i) => <div key={i} className="notice notice-success" role="status"><Icon name="check" /><span>{message}</span><button type="button" className="icon-button" data-dismiss-notice aria-label="Fechar aviso"><Icon name="close" /></button></div>)}
                    <section className="stats-grid" aria-label="Resumo dos usuários">
                        {[['Total de usuários', usuarios.length, 'users', 'cyan'], ['Administradores', contar('admin'), 'shield', 'violet'], ['Professores', contar('professor'), 'book', 'amber'], ['Alunos', contar('aluno'), 'cap', 'green']]
                            .map(([label, value, symbol, color]) => <article key={label} className="stat-card"><span className={`stat-icon ${color}`}><Icon name={symbol} /></span><div><span>{label}</span><strong>{value}</strong></div></article>)}
                    </section>
                    <div className="tabs" role="tablist" aria-label="Gestão de acesso"><button type="button" className="tab active" id="tab-users" role="tab" aria-selected="true" aria-controls="panel-users" data-tab="panel-users"><Icon name="users" /> Usuários <span>{usuarios.length}</span></button><button type="button" className="tab" id="tab-permissions" role="tab" aria-selected="false" aria-controls="panel-permissions" tabIndex={-1} data-tab="panel-permissions"><Icon name="shield" /> Mapa de permissões</button></div>
                    <section className="users-panel panel" id="panel-users" role="tabpanel" aria-labelledby="tab-users">
                        <div className="list-toolbar"><div><h2>Todos os usuários</h2><p>Consulte os cadastros e ajuste os perfis de acesso.</p></div><div className="filters"><label className="search-field"><Icon name="search" /><input type="search" id="user-search" placeholder="Buscar por nome ou e-mail" aria-label="Buscar usuário por nome ou e-mail" /></label><label className="filter-field"><span className="sr-only">Filtrar por perfil</span><select id="role-filter"><option value="">Todos os perfis</option><option value="superadmin">Superperfil</option><option value="admin">Administrador</option><option value="professor">Professor</option><option value="aluno">Aluno</option></select></label></div></div>
                        <div className="table-scroll"><table className="users-table"><thead><tr><th scope="col">Usuário</th><th scope="col">Perfil de acesso</th><th scope="col">Permissões</th><th scope="col" className="action-heading">Ações</th></tr></thead><tbody>
                            {usuarios.map((usuario) => (
                                <tr key={usuario.id} data-user-row data-role={usuario.tipo} data-search={`${usuario.nome} ${usuario.email}`.toLowerCase()}>
                                    <td><div className="user-identity"><span className={`avatar avatar-${usuario.tipo}`}>{usuario.nome.slice(0, 2).toUpperCase()}</span><div><strong>{usuario.nome}</strong><span>{usuario.email}</span></div>{usuario.id === g.sessao.user_id && <span className="you-tag">Você</span>}</div></td>
                                    <td><span className={`role-badge role-${usuario.tipo}`}><span></span>{PERFIS[usuario.tipo] ?? usuario.tipo}</span></td>
                                    <td className="permission-summary">{RESUMO[usuario.tipo] ?? 'Sem perfil definido'}</td>
                                    <td className="row-action">{usuario.tipo !== 'superadmin' ? <button type="button" className="edit-button" data-edit-user={JSON.stringify(usuario)} data-user-id={usuario.id} aria-label={`Editar permissões de ${usuario.email}`}>Gerenciar <Icon name="arrow" /></button> : <span className="protected-label"><Icon name="lock" /> Protegido</span>}</td>
                                </tr>
                            ))}
                        </tbody></table></div>
                        <div className="empty-state" id="users-empty" hidden><Icon name="search" /><h3>Nenhum usuário encontrado</h3><p>Tente outro nome, e-mail ou perfil.</p><button type="button" className="button button-secondary" id="clear-filters">Limpar filtros</button></div>
                        <footer className="list-footer"><span id="results-count" role="status" aria-live="polite">{usuarios.length} usuários cadastrados</span><span><Icon name="lock" /> Apenas o superperfil pode alterar permissões</span></footer>
                    </section>
                    <section className="panel permission-panel" id="panel-permissions" role="tabpanel" aria-labelledby="tab-permissions" hidden>
                        <div className="permission-heading"><span className="stat-icon violet"><Icon name="shield" /></span><div><h2>Um perfil para cada responsabilidade</h2><p>Confira o que cada pessoa pode fazer no sistema.</p></div></div>
                        <div className="table-scroll"><table className="permission-table"><thead><tr><th scope="col">Recurso</th>{ROLES.map((role) => <th key={role} scope="col"><span className={`role-badge role-${role}`}>{PERFIS[role]}</span></th>)}</tr></thead><tbody>
                            {RECURSOS.map(([resource, allowed]) => <tr key={resource}><th scope="row">{resource}</th>{ROLES.map((role) => <td key={role}>{allowed.includes(role) ? <span className="permission-yes" aria-label="Permitido"><Icon name="check" /></span> : <span className="permission-no" aria-label="Não permitido">—</span>}</td>)}</tr>)}
                        </tbody></table></div><p className="panel-note"><Icon name="info" /> Atividades, notas e disciplinas respeitam os vínculos de cada professor e aluno.</p>
                    </section>
                    <p className="page-footnote"><Icon name="shield" /> Uma escola conectada começa com acessos bem definidos.</p>
                </main>
            </div>
            <dialog className="user-dialog" id="create-dialog" data-open-on-load={d.error ? '' : undefined} aria-labelledby="create-title">
                <form method="post" action={urlFor('gestao.usuarios')} id="create-form" className="user-form" data-user-form="create"><Token />
                    <Token />
                    <header className="dialog-heading"><div><span className="eyebrow">UM NOVO ACESSO À ESCOLA</span><h2 id="create-title">Criar usuário</h2><p>Escolha o perfil e preencha os dados de acesso.</p></div><button type="button" className="icon-button" data-close-dialog aria-label="Fechar cadastro"><Icon name="close" /></button></header>
                    <div className="dialog-content">
                        {d.error && <div className="notice notice-error" role="alert"><Icon name="info" /><span>{d.error}</span></div>}
                        <fieldset className="role-fieldset"><legend>Qual será o perfil de acesso?</legend><RoleOptions selected={d.error ? (form.tipo ?? 'aluno') : 'aluno'} /></fieldset>
                        <div className="access-preview"><Icon name="shield" /><p data-role-preview>O aluno pode consultar suas disciplinas, notas e mensagens.</p></div>
                        <div className="form-section-heading"><span>01</span><h3>Dados de acesso</h3></div>
                        <div className="form-grid">
                            <label className="field field-full">Nome completo <input name="nome" required maxLength={120} placeholder="Como a pessoa se chama?" autoComplete="name" defaultValue={valor('nome')} /></label>
                            <label className="field">E-mail <input name="email" type="email" required maxLength={120} placeholder="nome@escola.com.br" autoComplete="email" defaultValue={valor('email')} /></label>
                            <label className="field">Senha de acesso <span className="password-field"><input name="senha" type="password" required minLength={8} autoComplete="new-password" placeholder="Pelo menos 8 caracteres" /><button type="button" className="icon-button" data-toggle-password aria-label="Mostrar senha" aria-pressed="false"><Icon name="eye" /></button></span><small>Compartilhe a senha com o novo usuário.</small></label>
                        </div>
                        <div data-academic-section><div className="form-section-heading"><span>02</span><h3>Dados acadêmicos</h3></div><div className="form-grid">
                            <label className="field" data-academic="professor">CPF <input name="cpf" maxLength={14} placeholder="000.000.000-00" inputMode="numeric" defaultValue={valor('cpf')} /><small>Necessário para cadastrar o professor.</small></label>
                            <label className="field" data-academic="aluno">Matrícula <input name="matricula" maxLength={30} placeholder="Ex.: 2026-001" defaultValue={valor('matricula')} /><small>Use uma matrícula exclusiva para este aluno.</small></label>
                        </div></div>
                    </div>
                    <footer className="dialog-footer"><span><Icon name="lock" /> O usuário terá somente os acessos do perfil escolhido.</span><div><button type="button" className="button button-secondary" data-close-dialog>Cancelar</button><button type="submit" className="button button-primary"><Icon name="plus" /> Criar usuário</button></div></footer>
                </form>
            </dialog>
            <dialog className="user-dialog" id="permission-dialog" aria-labelledby="permission-title" data-open-user={d.edit_user_id || ''} data-submitted={d.permission_error ? JSON.stringify(form) : undefined}>
                <form method="post" id="permission-form" className="user-form" data-user-form="permission" data-action-template={urlFor('gestao.perfil', { user_id: 0 })}><Token />
                    <Token />
                    <header className="dialog-heading"><div><span className="eyebrow">CONTROLE DE ACESSO</span><h2 id="permission-title">Gerenciar permissões</h2><p>Defina o que este usuário pode acessar.</p></div><button type="button" className="icon-button" data-close-dialog aria-label="Fechar permissões"><Icon name="close" /></button></header>
                    <div className="dialog-content">
                        {d.permission_error && <div className="notice notice-error" role="alert"><Icon name="info" /><span>{d.permission_error}</span></div>}
                        <div className="selected-user"><span className="avatar" id="edit-avatar"></span><div><strong id="edit-name"></strong><span id="edit-email"></span></div><span className="you-tag" id="current-role"></span></div>
                        <fieldset className="role-fieldset"><legend>Perfil de acesso</legend><RoleOptions /></fieldset>
                        <div className="access-preview"><Icon name="shield" /><p data-role-preview></p></div>
                        <div data-academic-section><div className="form-section-heading"><span>+</span><h3>Complete o cadastro acadêmico</h3></div><div className="form-grid">
                            <label className="field field-full" data-academic="nome">Nome completo <input name="nome" maxLength={120} autoComplete="name" /></label>
                            <label className="field" data-academic="professor">CPF <input name="cpf" maxLength={14} placeholder="000.000.000-00" inputMode="numeric" /></label>
                            <label className="field" data-academic="aluno">Matrícula <input name="matricula" maxLength={30} placeholder="Ex.: 2026-001" /></label>
                        </div></div>
                        <p className="preserved-note" data-existing-record hidden><Icon name="check" /> Este usuário já possui cadastro acadêmico para o perfil selecionado.</p>
                        <div className="change-note"><Icon name="info" /><p>A mudança vale no próximo acesso ou ao recarregar a página. Os vínculos acadêmicos existentes serão preservados.</p></div>
                    </div>
                    <footer className="dialog-footer"><span><Icon name="shield" /> Alteração exclusiva do superperfil.</span><div><button type="button" className="button button-secondary" data-close-dialog>Cancelar</button><button type="submit" className="button button-primary"><Icon name="check" /> Salvar permissões</button></div></footer>
                </form>
            </dialog>
        </>
    );
}
