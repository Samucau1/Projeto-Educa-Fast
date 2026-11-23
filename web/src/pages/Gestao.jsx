import React, { useEffect, useRef, useState } from 'react';
import { ActionDialog } from '../components/ActionDialog';
import { Pagination } from '../components/Pagination';
import { api } from '../api';
import { GestaoSidebar } from '../components/Navigation';
import { useAuth } from '../components/Auth';

const blank = { email: '', senha: '', role: 'secretaria', ativo: true, exigir_troca: true, permissoes: {} };
const inputStyle = 'bg-white/5 border border-white/10 text-white outline-none focus:ring-2 focus:ring-cyan-500 rounded-lg p-3 w-full';
export default function Gestao() {
    const { user } = useAuth();
    const contaDialog = useRef(null);
    const configDialog = useRef(null);
    const [data, setData] = useState(null);
    const [form, setForm] = useState(blank);
    const [config, setConfig] = useState({});
    const [tab, setTab] = useState('Contas');
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');
    const [pending, setPending] = useState(false);
    const [page, setPage] = useState(1);
    const [size, setSize] = useState(20);
    const [search, setSearch] = useState('');
    const [role, setRole] = useState('');
    const [loading, setLoading] = useState(false);
    const query = new URLSearchParams({ page, page_size: size, search, role }).toString();
    async function load() {
        const result = await api(`/api/gestao/painel?${query}`);
        setData(result);
        setConfig({ ano_letivo: new Date().getFullYear(), periodos: 4, media_aprovacao: 6, prazo_notas: '', ...result.configuracoes });
    }
    useEffect(() => {
        const controller = new AbortController();
        setLoading(true);
        const timer = setTimeout(() => {
            api(`/api/gestao/painel?${query}`, { signal: controller.signal }).then(result => {
                setData(result);
                setConfig({ ano_letivo: new Date().getFullYear(), periodos: 4, media_aprovacao: 6, prazo_notas: '', ...result.configuracoes });
            }).catch(e => { if (e.name !== 'AbortError') setError(e.message); })
                .finally(() => { if (!controller.signal.aborted) setLoading(false); });
        }, 250);
        return () => { clearTimeout(timer); controller.abort(); };
    }, [query]);
    async function save(event, endpoint, values) {
        event.preventDefault();
        setPending(true); setError(''); setMessage('');
        try {
            const result = await api(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values) });
            await load(); setMessage(result.mensagem); setForm(blank); contaDialog.current?.close(); configDialog.current?.close();
        } catch (e) { setError(e.message); }
        finally { setPending(false); }
    }
    async function restore(event) {
        event.preventDefault();
        setPending(true); setError(''); setMessage('');
        try {
            const result = await api('/api/gestao/restaurar', { method: 'POST', body: new FormData(event.currentTarget) });
            window.alert(result.mensagem);
            window.location.assign('/login');
        } catch (e) { setError(e.message); }
        finally { setPending(false); }
    }
    return <div className="gestao-page app-layout flex w-full text-white">
        <GestaoSidebar active={tab} onSelect={name => { setTab(name); window.scrollTo(0, 0); }} />
        <main className="flex-1 min-w-0 p-6 md:p-10">
        <header className="flex justify-between gap-4 mb-8"><div><p className="text-cyan-400">SECRETARIA DF · ADMINISTRAÇÃO</p><h1 className="text-3xl font-bold">Administração geral</h1><p className="text-slate-300">{user.email}</p></div></header>
        {error && <p role="alert" className="p-4 text-red-300">{error}</p>}
        {message && <p role="status" className="p-4 text-green-300">{message}</p>}
        {!data ? <button onClick={() => load().catch(e => setError(e.message))}>Carregar painel</button> : <>
            <div className="grid grid-cols-2 xl:grid-cols-5 gap-4 mb-8">{Object.entries(data.resumo).map(([key, value]) => <div key={key} className="glass-card rounded-xl p-5"><p className="capitalize text-slate-300">{key.replaceAll('_', ' ')}</p><strong className="text-3xl">{value}</strong></div>)}</div>
            {tab === 'Contas' && <div className="space-y-6">
                <div className="flex justify-between items-center gap-4"><h2 className="text-xl">Usuários do sistema</h2><button type="button" className="action-dialog-trigger" onClick={() => { setForm(blank); setError(''); contaDialog.current.open(); }}>Nova conta</button></div><div className="flex flex-wrap gap-4"><label>Pesquisar e-mail<input aria-label="Pesquisar usuários" type="search" className={inputStyle} value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} /></label><label>Perfil<select className={inputStyle} value={role} onChange={e => { setRole(e.target.value); setPage(1); }}><option value="">Todos os perfis</option><option value="admin">Administrador</option><option value="secretaria">Secretaria Escolar</option><option value="professor">Professor</option><option value="aluno">Aluno</option></select></label></div><section className="gestao-table-panel" aria-busy={loading}><table className="w-full text-left"><thead><tr><th className="p-2">E-mail</th><th>Perfil</th><th>Status</th><th>Ação</th></tr></thead><tbody>{data.usuarios.map(u => <tr key={u.id} className="border-t border-white/10"><td className="p-3">{u.email}</td><td>{u.role === 'secretaria' ? 'Secretaria Escolar' : u.role}</td><td>{u.ativo ? 'Ativo' : 'Bloqueado'}</td><td><button data-ui-action disabled={u.id === user.id} onClick={() => { setForm({ ...u, senha: '' }); setMessage(''); setError(''); contaDialog.current.open(); }} className="text-cyan-300 disabled:opacity-40">Editar</button></td></tr>)}{!data.usuarios.length && <tr><td colSpan={4} className="p-4">Nenhum usuário encontrado.</td></tr>}</tbody></table></section><Pagination pagination={data.pagination} busy={loading} onPage={setPage} onSize={n => { setSize(n); setPage(1); }} />
                <ActionDialog ref={contaDialog} title={form.id ? 'Editar conta' : 'Nova conta administrativa'} busy={pending}>
                {error && <p role="alert" className="text-red-200 mb-4">{error}</p>}
                <form onSubmit={event => save(event, `/api/gestao/usuarios${form.id ? '/' + form.id : ''}`, ['admin', 'secretaria'].includes(form.role) ? form : { ativo: form.ativo, exigir_troca: form.exigir_troca, ...(form.senha ? { senha: form.senha } : {}) })} className="space-y-4 glass-card rounded-xl p-6">
                    <h2 className="text-xl">{form.id ? 'Editar conta' : 'Nova conta administrativa'}</h2>
                    {['admin', 'secretaria'].includes(form.role) && <><label className="block">E-mail<input type="email" required className={inputStyle} value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></label>
                    <label className="block">Perfil<select className={inputStyle} value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}><option className="bg-[#16466e] text-white" value="secretaria">Secretaria Escolar</option><option className="bg-[#16466e] text-white" value="admin">Administrador</option></select></label></>}
                    <label className="block">{form.id ? 'Nova senha (opcional)' : 'Senha inicial'}<input type="password" minLength={8} required={!form.id} autoComplete="new-password" className={inputStyle} value={form.senha} onChange={e => setForm({ ...form, senha: e.target.value })} /></label>
                    <label className="block"><input type="checkbox" checked={form.ativo} onChange={e => setForm({ ...form, ativo: e.target.checked })} /> Conta ativa</label>
                    <label className="block"><input type="checkbox" checked={form.exigir_troca} onChange={e => setForm({ ...form, exigir_troca: e.target.checked })} /> Exigir troca de senha no próximo acesso</label>
                    {form.role === 'secretaria' && <fieldset className="space-y-2"><legend>Permissões da secretaria</legend>{Object.entries(data.permissoes).map(([key, label]) => <label key={key} className="block"><input type="checkbox" checked={form.permissoes[key] ?? true} onChange={e => setForm({ ...form, permissoes: { ...form.permissoes, [key]: e.target.checked } })} /> {label}</label>)}</fieldset>}
                    {form.id && <p className="text-sm text-slate-300">Salvar encerra todas as sessões anteriores desta conta.</p>}
                    <div className="button-actions"><button data-ui-action disabled={pending} className="ui-button">{pending ? 'Salvando…' : 'Salvar conta'}</button> <button data-ui-action type="button" className="ui-button" onClick={() => setForm(blank)}>Limpar</button></div>
                </form>
                </ActionDialog>
            </div>}
            {tab === 'Configurações' && <section className="space-y-5"><h2 className="text-xl">Parâmetros acadêmicos</h2><dl className="grid sm:grid-cols-2 gap-4 max-w-xl">{[['ano_letivo','Ano letivo'],['periodos','Períodos'],['media_aprovacao','Média de aprovação'],['prazo_notas','Prazo para notas']].map(([key,label]) => <div key={key} className="glass-card rounded-xl p-4"><dt className="text-slate-300 text-sm">{label}</dt><dd className="mt-2 font-semibold">{data.configuracoes[key] === '' ? 'Não definido' : data.configuracoes[key] ?? 'Não definido'}</dd></div>)}</dl><ActionDialog ref={configDialog} title="Editar configurações" label="Editar configurações" busy={pending}>{error && <p role="alert" className="text-red-200">{error}</p>}<form className="max-w-xl space-y-4" onSubmit={e => save(e, '/api/gestao/configuracoes', config)}><h2 className="text-xl">Parâmetros acadêmicos</h2><p className="text-slate-300">Referência institucional para o ano letivo. O prazo limita novos lançamentos de notas.</p>{[['ano_letivo', 'Ano letivo', 'number'], ['periodos', 'Quantidade de períodos', 'number'], ['media_aprovacao', 'Média para aprovação', 'number'], ['prazo_notas', 'Prazo para notas', 'date']].map(([key, label, type]) => <label key={key} className="block">{label}<input type={type} required={key !== 'prazo_notas'} step={key === 'media_aprovacao' ? '0.1' : undefined} className={inputStyle} value={config[key]} onChange={e => setConfig({ ...config, [key]: e.target.value })} /></label>)}<button data-ui-action disabled={pending} className="bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold rounded-lg px-5 py-3">Salvar configurações</button></form></ActionDialog></section>}
            {tab === 'Auditoria' && <section className="gestao-table-panel"><h2 className="text-xl mb-4">Últimos 100 eventos</h2><table className="w-full text-left"><thead><tr><th>Data</th><th>Usuário</th><th>Ação</th><th>Detalhes</th></tr></thead><tbody>{data.auditoria.map(a => <tr key={a.id} className="border-t border-white/10"><td className="p-3">{new Date(a.data + 'Z').toLocaleString('pt-BR')}</td><td className="p-3">{a.email}</td><td className="p-3">{a.acao}</td><td className="p-3 text-sm"><ActionDialog title="Detalhes do evento" label="Ver detalhes"><p className="text-slate-300 mb-4">{a.email} · {a.acao}</p><pre className="whitespace-pre-wrap break-all">{JSON.stringify(a.detalhes, null, 2)}</pre></ActionDialog></td></tr>)}</tbody></table>{!data.auditoria.length && <p>Nenhum evento registrado.</p>}</section>}
            {tab === 'Backup' && <section className="max-w-xl space-y-5"><h2 className="text-xl">Backup e recuperação do banco</h2><p>O backup inclui os dados e credenciais protegidas do banco. Guarde o arquivo em local seguro. Os arquivos enviados devem ser copiados separadamente do volume de uploads.</p><div className="button-actions"><a data-ui-action href="/api/gestao/backup" className="ui-button">Baixar backup do banco</a><ActionDialog title="Restaurar banco" label="Restaurar backup" busy={pending}><form onSubmit={restore} className="space-y-4 border border-red-400/30 bg-red-500/5 p-5 rounded-xl">{error && <p role="alert" className="text-red-200">{error}</p>}<h3 className="text-xl">Restaurar banco</h3><p>A restauração substitui os dados atuais pelos do backup e encerra as sessões. Baixe um backup atual antes de continuar.</p><label className="block">Arquivo de backup<input className={inputStyle} type="file" name="backup" accept="application/json,.json" required /></label><label className="block">Sua senha de administrador<input className={inputStyle} type="password" name="senha" required autoComplete="current-password" /></label><label className="block">Digite RESTAURAR<input className={inputStyle} name="confirmacao" required pattern="RESTAURAR" /></label><button data-ui-action className="bg-red-500/20 border border-red-400/30 text-red-200 hover:bg-red-500/30 rounded-lg px-5 py-3" disabled={pending}>Restaurar backup</button></form></ActionDialog></div></section>}
            {tab === 'Relatórios' && <section><h2 className="text-xl mb-4">Relatório de contas</h2><p className="mb-4">Exporte a relação de usuários, perfis e status de acesso.</p><div className="button-actions"><a data-ui-action className="ui-button" href="/api/gestao/relatorio.csv">Exportar CSV</a> <a data-ui-action className="ui-button" href="/api/gestao/academico.csv">Exportar relatório acadêmico</a></div></section>}
        </>}
        </main>
    </div>;
}
