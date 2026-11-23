import { useEffect } from 'react';
import GestaoBase, { bodyGestao, tituloGestao } from '../components/GestaoBase';
import Token from '../components/Token';
import { urlFor } from '../core/urls';
import { dataBR } from '../core/formatos';

export const bodyClass = bodyGestao();
export const titulo = tituloGestao('Regras e identidade da escola');

const DIAS = [[0, 'Segunda'], [1, 'Terça'], [2, 'Quarta'], [3, 'Quinta'], [4, 'Sexta'], [5, 'Sábado'], [6, 'Domingo']];
const CORES = [['fundo', 'Cor de fundo'], ['destaque', 'Cor de destaque'], ['superficie', 'Cor dos cartões'], ['texto', 'Cor do texto'], ['muted', 'Cor do texto secundário']];
const PERIODOS = Array.from({ length: 12 }, (_, i) => i + 1);

function DiasSemana({ selecionados }) {
    return <div className="school-checks">{DIAS.map(([i, nome]) => <label key={i}><input type="checkbox" name="dias_semana" value={i} defaultChecked={selecionados.includes(i)} />{nome}</label>)}</div>;
}

export default function EscolaConfigurar({ d }) {
    const identidade = d.identidade;

    // Regras do boletim: mostra só os períodos da divisão escolhida; paletas prontas preenchem o formulário.
    useEffect(() => {
        const limpar = [];
        const policy = document.querySelector('[data-school-policy]');
        if (policy) {
            const refresh = () => {
                const division = policy.elements.divisao.value;
                const count = { semestres: 2, trimestres: 3, bimestres: 4 }[division] || Number(policy.elements.quantidade.value);
                policy.querySelectorAll('[data-school-slot]').forEach((slot) => {
                    const hidden = Number(slot.dataset.schoolSlot) > count;
                    slot.hidden = hidden;
                    slot.querySelectorAll('input').forEach((input) => { input.disabled = hidden; });
                });
            };
            policy.addEventListener('change', refresh);
            limpar.push(() => policy.removeEventListener('change', refresh));
            refresh();
        }
        document.querySelectorAll('[data-school-preset]').forEach((button) => {
            const aplicar = () => {
                const form = document.querySelector('#school-identity');
                if (!form) return;
                const light = button.dataset.schoolPreset === 'claro';
                const values = light ? { modo: 'claro', fundo: '#f3f6fb', destaque: '#1d4ed8', superficie: '#ffffff', texto: '#18283b', muted: '#475569' }
                    : { modo: 'escuro', fundo: '#06385d', destaque: '#22d3ee', superficie: '#111c2b', texto: '#ecf1f8', muted: '#a4bdce' };
                Object.entries(values).forEach(([name, value]) => { form.elements[name].value = value; });
                form.querySelector('[data-school-status]').textContent = 'Paleta preenchida no formulário. Salve para aplicar à escola.';
            };
            button.addEventListener('click', aplicar);
            limpar.push(() => button.removeEventListener('click', aplicar));
        });
        return () => limpar.forEach((fn) => fn());
    }, []);

    return (
        <GestaoBase titulo="Regras e identidade da escola" error={d.error}>
            <section className="page-heading"><div><span className="eyebrow">SUPERADMINISTRADOR</span><h1>A escola do seu jeito<span>.</span></h1><p>Identidade, calendário e regras acadêmicas no mesmo padrão EducaFast.</p></div></section>
            <nav className="school-tabs" aria-label="Seções de configuração"><a className="button button-primary" href="#identidade">Identidade visual</a><a className="button button-secondary" href="#calendarios">Calendário letivo</a><a className="button button-secondary" href="#politicas">Regras do boletim</a></nav>
            <section className="panel course-panel school-anchor" id="identidade"><h2>Identidade da escola</h2><p>Mantenha a estrutura do EducaFast e ajuste a marca e os detalhes visuais para sua comunidade.</p><form method="post" action={urlFor('escola.identidade_visual')} className="course-form" id="school-identity"><Token /><input type="hidden" name="versao" value={identidade.versao} />
                <div className="school-fields"><label>Nome da escola<input name="nome" defaultValue={identidade.nome} maxLength={60} required /></label><label>Sigla da marca<input name="sigla" defaultValue={identidade.sigla} maxLength={3} required /></label><label>Subtítulo<input name="subtitulo" defaultValue={identidade.subtitulo} maxLength={40} required /></label></div>
                <div className="school-fields"><label>Modo<select name="modo" defaultValue={identidade.modo === 'claro' ? 'claro' : 'escuro'}><option value="escuro">Escuro</option><option value="claro">Claro</option></select></label><label>Fonte<select name="fonte" defaultValue={identidade.fonte === 'sistema' ? 'sistema' : 'dm-sans'}><option value="dm-sans">DM Sans — padrão EducaFast</option><option value="sistema">Fonte do dispositivo</option></select></label><label>Espaçamento<select name="densidade" defaultValue={identidade.densidade === 'compacta' ? 'compacta' : 'confortavel'}><option value="confortavel">Confortável</option><option value="compacta">Compacto</option></select></label><label>Bordas dos cartões<select name="raio" defaultValue={['8', '12', '16'].includes(identidade.raio) ? identidade.raio : '8'}>{['8', '12', '16'].map((v) => <option key={v} value={v}>{v} px{v === '12' ? ' — padrão' : ''}</option>)}</select></label></div>
                <div className="school-fields">{CORES.map(([campo, rotulo]) => <label key={campo}>{rotulo}<input type="color" className="school-swatch" name={campo} defaultValue={identidade[campo]} /></label>)}</div>
                <p className="course-meta">Os textos e cartões precisam manter contraste legível. O sistema valida as combinações antes de aplicar para todos os perfis.</p><div className="course-actions"><button className="button button-primary">Salvar identidade</button><button className="button button-secondary" type="button" data-school-preset="padrao">Restaurar padrão no formulário</button><button className="button button-secondary" type="button" data-school-preset="claro">Experimentar paleta clara</button></div><p role="status" className="school-form-status" data-school-status></p></form></section>
            <section className="panel course-panel school-anchor" id="calendarios"><h2>Calendários e dias letivos</h2><p>Defina os dias da semana, feriados, recessos e reposições. Os eventos são cadastrados pela escola; não há inclusão automática de feriados.</p>
                <details className="course-outline"><summary>Criar calendário de um ano</summary><form className="course-form" method="post" action={urlFor('escola.criar_calendario')}><Token /><div className="school-fields"><label>Ano<input type="number" name="ano" min="1900" max="2200" required /></label><label>Nome do calendário<input name="nome" maxLength={120} required /></label><label>Primeiro dia<input type="date" name="inicio" required /></label><label>Último dia<input type="date" name="fim" required /></label><label>Meta de dias letivos<input type="number" name="meta_letivos" min="1" max="366" defaultValue="200" required /></label></div><fieldset><legend>Dias da semana letivos</legend><DiasSemana selecionados={[0, 1, 2, 3, 4]} /></fieldset><p className="course-meta">A meta é uma configuração da escola. Confira as exigências aplicáveis à instituição antes de adotá-la.</p><button className="button button-primary">Criar calendário</button></form></details>
                {d.calendarios.map((c) => {
                    const resumo = d.resumos[c.id];
                    return (
                        <details key={c.id} className="course-outline"><summary>{c.ano} · {c.nome} · {resumo.dias_planejados} dias planejados</summary><div className="school-summary"><p><strong>{resumo.dias_planejados}</strong>planejados</p><p><strong>{c.meta_letivos}</strong>meta</p><p><strong>{resumo.faltam}</strong>dias para atingir a meta</p></div>
                            <details><summary>Editar base do calendário</summary><form className="course-form" method="post" action={urlFor('escola.editar_calendario', { calendario_id: c.id })}><Token /><input type="hidden" name="versao" value={c.versao} /><div className="school-fields"><label>Ano<input type="number" name="ano" defaultValue={c.ano} required /></label><label>Nome<input name="nome" defaultValue={c.nome} maxLength={120} required /></label><label>Primeiro dia<input type="date" name="inicio" defaultValue={c.inicio} required /></label><label>Último dia<input type="date" name="fim" defaultValue={c.fim} required /></label><label>Meta de dias letivos<input type="number" name="meta_letivos" defaultValue={c.meta_letivos} min="1" max="366" required /></label></div><DiasSemana selecionados={resumo.dias_semana} /><button className="button button-primary">Salvar calendário</button></form></details>
                            <details><summary>Adicionar feriado, recesso ou reposição</summary><form className="course-form" method="post" action={urlFor('escola.criar_evento', { calendario_id: c.id })}><Token /><input type="hidden" name="versao" value={c.versao} /><div className="school-fields"><label>Título<input name="titulo" maxLength={150} required /></label><label>Tipo<select name="tipo"><option value="feriado">Feriado — não letivo</option><option value="recesso">Recesso — não letivo</option><option value="letivo">Reposição — letivo</option><option value="evento">Evento — mantém a regra semanal</option></select></label><label>De<input type="date" name="inicio" required /></label><label>Até (opcional)<input type="date" name="fim" /></label></div><button className="button button-primary">Adicionar datas</button></form></details>
                            {d.eventos.filter((e) => e.calendario_id === c.id).map((e) => <article key={e.id} className="course-outline school-event"><div><span className="eyebrow">{dataBR(e.dia)} · {e.tipo}</span><h3>{e.titulo}</h3></div><form method="post" action={urlFor('escola.remover_evento', { evento_id: e.id })}><Token /><input type="hidden" name="versao" value={c.versao} /><button className="button button-secondary">Remover esta data</button></form></article>)}
                        </details>
                    );
                })}
            </section>
            <section className="panel course-panel school-anchor" id="politicas"><h2>Regras do boletim</h2><p>Crie uma versão da regra e aplique às turmas do mesmo ano que ainda não têm períodos. Regras aplicadas preservam seus nomes, pesos e arredondamento.</p>
                <details className="course-outline"><summary>Criar uma versão das regras acadêmicas</summary><form className="course-form" method="post" action={urlFor('escola.criar_politica')} data-school-policy><Token /><div className="school-fields"><label>Nome da versão<input name="nome" maxLength={120} placeholder="Ensino fundamental — 2027" required /></label><label>Calendário<select name="calendario_id" required><option value="">Selecione</option>{d.calendarios.map((c) => <option key={c.id} value={c.id}>{c.ano} · {c.nome}</option>)}</select></label><label>Divisão do ano<select name="divisao"><option value="bimestres">Bimestres — 4 períodos</option><option value="trimestres">Trimestres — 3 períodos</option><option value="semestres">Semestres — 2 períodos</option><option value="personalizada">Personalizada</option></select></label><label>Quantidade personalizada<input type="number" name="quantidade" min="1" max="12" defaultValue="4" /></label><label>Média de referência<input name="media_referencia" type="number" min="0" max="10" step="0.01" defaultValue="6" required /></label><label>Casas decimais<select name="casas"><option value="2">Duas</option><option value="1">Uma</option></select></label><label>Arredondamento<select name="arredondamento"><option value="comercial">Comercial</option><option value="truncar">Truncar</option></select></label></div>
                    {PERIODOS.map((i) => <fieldset key={i} className="course-outline school-period" data-school-slot={i}><legend>Período {i}</legend><div className="school-fields"><label>Nome<input name={`periodo_${i}_nome`} defaultValue={`${i}º período`} maxLength={80} /></label><label>Peso no resultado anual<input name={`periodo_${i}_peso`} type="number" defaultValue="1" min="0.01" max="100" step="0.01" /></label><label>Início<input name={`periodo_${i}_inicio`} type="date" /></label><label>Fim<input name={`periodo_${i}_fim`} type="date" /></label></div></fieldset>)}<p className="course-meta">O resultado anual pondera as médias dos períodos e só é fechado quando todos os períodos estão encerrados e completos. A escola mantém a responsabilidade por frequência e outros critérios ainda não implementados.</p><button className="button button-primary">Criar versão das regras</button></form></details>
                {d.politicas.map((p) => <article key={p.id} className="course-outline"><span className="eyebrow">VERSÃO #{p.id} · {p.divisao}</span><h3>{p.nome}</h3><p>Referência {p.media_referencia} · {p.casas} casa(s) · {p.arredondamento}</p>{p.periodos.map((item, i) => <p key={i}>{item.nome} · peso {item.peso} · {item.inicio} a {item.fim}</p>)}<form className="course-form" method="post" action={urlFor('escola.aplicar', { politica_id: p.id })}><Token /><label>Aplicar à turma<select name="turma_id" required><option value="">Selecione</option>{d.turmas.filter((t) => !(String(t.id) in d.aplicadas)).map((t) => <option key={t.id} value={t.id}>{t.nome} · {t.ano_letivo}</option>)}</select></label><button className="button button-primary">Aplicar regra e criar os períodos</button></form></article>)}
            </section>
        </GestaoBase>
    );
}
