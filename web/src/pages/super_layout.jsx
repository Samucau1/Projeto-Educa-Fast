import { useEffect, useRef } from 'react';
import GestaoBase, { bodyGestao, tituloGestao } from '../components/GestaoBase';
import Icon from '../components/Icon';
import Token from '../components/Token';
import { urlFor } from '../core/urls';

export const bodyClass = bodyGestao();
export const titulo = tituloGestao('Aparência');

const PRESETS = [['Original', '#06385d', '#22d3ee'], ['Noturno', '#16132b', '#b2a1ff'], ['Floresta', '#12372d', '#6ee7b7']];

export default function SuperLayout({ d, g }) {
    const formRef = useRef(null);
    const previewRef = useRef(null);

    // Prévia ao vivo: seletor de cor, código hexadecimal e combinações prontas ficam sincronizados.
    useEffect(() => {
        const form = formRef.current;
        const preview = previewRef.current;
        function sync() {
            ['cor_fundo', 'cor_destaque'].forEach((name) => {
                const picker = form.elements[name];
                form.querySelector(`[data-color-hex="${name}"]`).value = picker.value;
                preview.style.setProperty(name === 'cor_fundo' ? '--preview-bg' : '--preview-accent', picker.value);
            });
        }
        const limpar = [];
        const ouvir = (el, evento, fn) => { el.addEventListener(evento, fn); limpar.push(() => el.removeEventListener(evento, fn)); };
        form.querySelectorAll('input[type=color]').forEach((picker) => ouvir(picker, 'input', sync));
        form.querySelectorAll('[data-color-hex]').forEach((input) => ouvir(input, 'input', () => {
            if (/^#[0-9a-fA-F]{6}$/.test(input.value)) { form.elements[input.dataset.colorHex].value = input.value; sync(); }
        }));
        form.querySelectorAll('[data-theme-preset]').forEach((button) => ouvir(button, 'click', () => {
            const colors = button.dataset.themePreset.split(',');
            form.elements.cor_fundo.value = colors[0];
            form.elements.cor_destaque.value = colors[1];
            sync();
        }));
        ouvir(form, 'reset', () => window.setTimeout(sync, 0));
        sync();
        return () => limpar.forEach((fn) => fn());
    }, []);

    const tema = g.tema;
    return (
        <GestaoBase titulo="Aparência" error={d.error}>
            <div className="notice notice-success"><a href={urlFor('escola.configurar')}>Configurar marca, regras acadêmicas e calendário da escola →</a></div>
            <section className="page-heading"><div><span className="eyebrow">A IDENTIDADE DA SUA ESCOLA</span><h1>Seu espaço, suas cores<span>.</span></h1><p>Personalize o ambiente que conecta toda a comunidade escolar.</p></div><span className="access-label"><Icon name="palette" /> Aparência do sistema</span></section>
            <div className="theme-layout">
                <form method="post" className="panel settings-card" id="theme-form" ref={formRef}><Token />
                    <Token />
                    <h2>Cores do layout</h2><p>Escolha as cores de fundo e destaque para todos os usuários.</p>
                    <div className="theme-color-row"><label htmlFor="cor-fundo">Fundo do ambiente<small>A base visual dos painéis e da navegação.</small></label><input id="cor-fundo" type="color" name="cor_fundo" defaultValue={tema.cor_fundo} required /><input type="text" data-color-hex="cor_fundo" defaultValue={tema.cor_fundo} aria-label="Código da cor de fundo" pattern="#[0-9a-fA-F]{6}" maxLength={7} required /></div>
                    <div className="theme-color-row"><label htmlFor="cor-destaque">Cor de destaque<small>Botões, links e elementos selecionados.</small></label><input id="cor-destaque" type="color" name="cor_destaque" defaultValue={tema.cor_destaque} required /><input type="text" data-color-hex="cor_destaque" defaultValue={tema.cor_destaque} aria-label="Código da cor de destaque" pattern="#[0-9a-fA-F]{6}" maxLength={7} required /></div>
                    <div className="theme-presets"><p>Ou comece com uma combinação</p><div className="preset-list">
                        {PRESETS.map(([name, bg, accent]) => <button key={name} type="button" className="theme-preset" data-theme-preset={`${bg},${accent}`}><span style={{ background: accent }}></span>{name}</button>)}
                    </div></div>
                    <footer className="settings-footer"><button type="reset" className="button button-secondary">Desfazer ajustes</button><button type="submit" className="button button-primary"><Icon name="check" /> Salvar cores</button></footer>
                </form>
                <section className="panel settings-card theme-preview-card" aria-label="Prévia das cores">
                    <div className="theme-preview-heading"><span>Veja como vai ficar</span><span className="preview-label">Prévia ao vivo</span></div>
                    <div className="theme-preview" data-theme-preview ref={previewRef} style={{ '--preview-bg': tema.cor_fundo, '--preview-accent': tema.cor_destaque }}><div className="preview-sidebar" aria-hidden="true"><div className="preview-logo">ef</div><span className="preview-line active"></span><span className="preview-line"></span><span className="preview-line"></span><span className="preview-line"></span></div><div className="preview-content"><h3>Minha escola</h3><p>Um lugar para aprender e se conectar.</p><div className="preview-stats" aria-hidden="true"><div className="preview-stat"><span></span><strong></strong></div><div className="preview-stat"><span></span><strong></strong></div><div className="preview-stat"><span></span><strong></strong></div></div><span className="preview-button"><Icon name="plus" /> Novo registro</span></div></div>
                    <p className="settings-hint"><Icon name="info" /> Salve para aplicar as cores. Os outros usuários verão a atualização ao recarregar a página.</p>
                </section>
            </div>
        </GestaoBase>
    );
}
