import ShellPagina, { headPainel } from '../components/ShellPagina';
import Token from '../components/Token';
import { urlFor } from '../core/urls';

export const head = headPainel('admin_comunicados.css');
export const bodyClass = 'app-page';
export const titulo = () => 'Comunicados | Educa Fast';

export default function AdminComunicados({ d }) {
    return (
        <ShellPagina id="admin-comunicados" titulo="Comunicados">
            <header className="flex justify-between items-center mb-10">
                <div>
                    <span className="eyebrow">GESTÃO ESCOLAR</span>
                    <h1 className="text-3xl font-bold">Comunicados</h1>
                    <p className="text-gray-400">Envie recados institucionais para todos os usuários do sistema.</p>
                </div>
            </header>
            <div className="comunicados-layout">
                <section className="glass-card comunicado-card rounded-[20px] p-10">
                    <div className="mb-10 flex items-center gap-4">
                        <h2 className="text-2xl font-bold">Comunicado Geral</h2>
                    </div>
                    {d.error && <p className="mb-6 rounded-xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm font-semibold text-red-200">{d.error}</p>}
                    <form method="post" className="space-y-9"><Token />
                        <Token />
                        <label className="block">
                            <span className="mb-2 block text-sm font-bold text-slate-300">Título do Recado</span>{' '}
                            <input name="titulo" type="text" maxLength={150} placeholder="Ex: Reunião de Pais e Mestres" className="comunicado-field" required />
                        </label>
                        <label className="block">
                            <span className="mb-2 block text-sm font-bold text-slate-300">Mensagem</span>{' '}
                            <textarea name="mensagem" rows={6} maxLength={10000} placeholder="Digite a mensagem oficial para envio imediato..." className="comunicado-field comunicado-textarea" required></textarea>
                        </label>
                        <div className="flex justify-end">
                            <button type="submit" className="comunicado-submit">
                                Disparar Comunicado
                            </button>
                        </div>
                    </form>
                </section>
                <aside className="glass-card comunicados-enviados rounded-[20px] p-8">
                    <h2 className="text-lg font-bold">Recados Enviados</h2>
                    <div className="mt-7 space-y-4">
                        {d.comunicados.length ? d.comunicados.map((comunicado) => (
                            <article key={comunicado.id} className="recado-card">
                                <div className="flex items-start justify-between gap-4">
                                    <h3>{comunicado.titulo}</h3>
                                    <span>{comunicado.created_at_label}</span>
                                </div>
                                <p>{comunicado.mensagem_resumo}</p>
                            </article>
                        )) : (
                            <div className="recado-card">
                                <h3>Nenhum comunicado enviado</h3>
                                <p>Os recados criados aparecerão nesta lista.</p>
                            </div>
                        )}
                    </div>
                    <a href={urlFor('gestao.mensagens')} className="ver-todos-button">Ver mensagens completas</a>
                </aside>
            </div>
        </ShellPagina>
    );
}
