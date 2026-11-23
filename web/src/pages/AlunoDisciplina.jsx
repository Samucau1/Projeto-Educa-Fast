import React, { Fragment } from 'react';
import { Link } from 'react-router-dom';
import { LogoutButton } from '../components/Navigation';

import { TabButton, TabPanel } from '../components/Tabs';
import { MutationForm } from '../components/MutationForm';
import { truthy } from '../utils';

export default function AlunoDisciplina({ data }) {
    const { aluno = {}, atividades = [], disciplina = {} } = data;
    return <>

    <aside className="w-72 glass-sidebar h-screen sticky top-0 flex flex-col p-6">
        <div className="mb-10 text-center">
            <h2 className="text-xl font-bold tracking-tighter text-cyan-400">SECRETARIA DF</h2>
            <p className="text-[10px] text-gray-500 uppercase tracking-widest">Portal do Aluno</p>
        </div>

        <nav className="flex-1 space-y-2">
            <div className="text-[10px] font-bold text-gray-500 mb-2 ml-4">MINHA ÁREA</div>
            <Link to={"/aluno"} className="flex items-center px-4 py-3 rounded-xl hover:bg-white/5 transition-all text-gray-300 hover:text-white">
                Voltar
            </Link>
            <Link to={"/aluno"} className="flex items-center px-4 py-3 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                Disciplinas
            </Link>
            <Link to="/aluno?aba=comunicados" className="flex items-center px-4 py-3 rounded-xl hover:bg-white/5 text-gray-300">Comunicados</Link>
        </nav>

        <div className="mt-auto pt-6 border-t border-white/10">
            <LogoutButton  className="flex items-center px-4 py-3 rounded-xl text-red-400 hover:bg-red-500/10 transition-all">
                Sair do Sistema
            </LogoutButton>
        </div>
    </aside>

    <main className="flex-1 p-10 overflow-y-auto">
        <header className="flex justify-between items-center mb-10">
            <div>
                <p className="text-sm text-cyan-400 font-bold">Disciplina</p>
                <h1 className="text-3xl font-bold">{disciplina.nome}</h1>
                <p className="text-gray-400">Código {disciplina.codigo} · {disciplina.carga_horaria}h</p>
            </div>
            <div className="flex items-center gap-4">
                <div className="text-right">
                    <p className="text-sm font-bold">{aluno.nome}</p>
                    <p className="text-[10px] text-cyan-400">Matrícula {aluno.matricula}</p>
                </div>
                {truthy(aluno.foto_perfil) ? <> 
                <img src={`/arquivos/perfil/${encodeURIComponent(aluno.foto_perfil)}`} alt={`Foto de ${aluno.nome}`} className="w-12 h-12 rounded-full border-2 border-white/20 object-cover" />
                 </> : <> 
                <div className="w-12 h-12 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 border-2 border-white/20"></div>
                 </>}
            </div>
        </header>

        <section className="glass-card aluno-card rounded-[32px] p-8">
            <div className="flex flex-wrap justify-between items-center gap-3 mb-6"><h2 className="text-xl font-bold">Atividades e conteúdos</h2><span className="text-sm text-cyan-400">Materiais enviados pelo professor</span></div>
            <div className="flex gap-4 border-b border-white/10 mb-6" role="tablist" aria-label="Materiais da disciplina">
                <TabButton group="disciplina-publicacoes" defaultValue="atividade" value="atividade" className="pb-2">Atividades</TabButton>
                <TabButton group="disciplina-publicacoes" defaultValue="atividade" value="conteudo" className="pb-2">Conteúdos</TabButton>
            </div>
        {['atividade', 'conteudo'].map(tipo => {
            const publicacoes = atividades.filter(item => (item.tipo || 'atividade') === tipo);
            return (
        <TabPanel key={tipo} group="disciplina-publicacoes" defaultValue="atividade" value={tipo}>
            <div className="aluno-exclusive-activities">
                {publicacoes.length ? <>{publicacoes.map((atividade, index25) => <Fragment key={atividade?.id ?? index25}>
                <article className="aluno-exclusive-activity">
                    <div>
                        <strong>{atividade.titulo}</strong>
                        <span>{atividade.professor}{tipo === 'atividade' && ` · Entrega: ${atividade.data_entrega}`}</span>
                        <p>{atividade.descricao}</p>
                        <small>{atividade.data}</small>
                    </div>
                    <div className="space-y-4">
                        <div className="button-actions">
                            {truthy(atividade.arquivo) && <a className="ui-button" href={`/arquivos/download/${encodeURIComponent(atividade.arquivo)}`}>Baixar arquivo</a>}
                            {tipo === 'atividade' && <MutationForm modalTitle={`Enviar atividade: ${atividade.titulo}`} modalLabel={atividade.entregas?.length ? 'Enviar novamente' : 'Enviar atividade'} action={`/api/aluno/atividades/${atividade.id}/enviar`} resetOnSuccess className="space-y-4">
                                <p className="text-slate-300">Selecione o arquivo com sua resposta. O envio ficará disponível para o professor responsável.</p>
                                <label className="block">Arquivo da atividade<input type="file" name="arquivo" required className="block mt-2 w-full" /></label>
                                <button className="ui-button">Confirmar envio</button>
                            </MutationForm>}
                        </div>
                        {!!atividade.entregas?.length && <div><p className="text-green-200 font-semibold">Atividade enviada</p><ul className="space-y-2 mt-2">{atividade.entregas.map(entrega => <li key={entrega.id} className="text-sm"><a className="text-cyan-200 underline" href={`/arquivos/download/${encodeURIComponent(entrega.arquivo)}`}>Baixar minha entrega · {entrega.data}</a></li>)}</ul></div>}
                    </div>
                </article>
                </Fragment>)}</> : <>
                <div className="aluno-activity-empty">{tipo === 'atividade' ? 'Nenhuma atividade lançada nesta disciplina.' : 'Nenhum conteúdo publicado nesta disciplina.'}</div>
                </>}
            </div>
        </TabPanel>
            );
        })}
        </section>
    </main>

    
    </>;
}
