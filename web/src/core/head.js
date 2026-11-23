// Elementos do <head> de cada tela (folhas de estilo, variáveis de tema e da escola),
// na mesma ordem em que o layout original os declarava.
import { asset } from './urls';

export const css = (nome) => ({ tipo: 'css', chave: `css:${nome}`, href: asset(`css/${nome}`) });
export const estilo = (chave, texto) => ({ tipo: 'style', chave: `style:${chave}`, texto });
export const meta = (nome, conteudo) => ({ tipo: 'meta', chave: `meta:${nome}`, nome, conteudo });

// Equivalente a partials/workspace_head.html.
export function headWorkspace(g) {
    const tema = g.tema || {};
    const escola = g.escola || {};
    const itens = [
        meta('csrf-token', g.csrf_token),
        css('design_system.css'),
        css('app.css'),
        css('escola.css'),
        estilo('tema', `:root { --theme-background: ${tema.cor_fundo ?? '#06385d'}; --accent: ${tema.cor_destaque ?? '#22d3ee'}; }`),
    ];
    if ((escola.versao ?? 0) > 0) {
        const fonte = escola.fonte === 'dm-sans' ? "'DM Sans', sans-serif" : 'system-ui, sans-serif';
        const claro = escola.modo === 'claro' ? `--page:${escola.fundo};--school-sidebar:${escola.superficie};` : '';
        itens.push(meta('school-theme', escola.modo));
        itens.push(estilo('escola', `:root{--surface:${escola.superficie};--text:${escola.texto};--muted:${escola.muted};--school-radius:${escola.raio}px;--school-space:${escola.densidade === 'compacta' ? '16' : '24'}px;--school-font:${fonte};--school-button-text:${escola.texto_botao};--surface-hover:color-mix(in srgb,${escola.superficie} 92%,${escola.texto});--line:color-mix(in srgb,${escola.texto} 18%,transparent);${claro}}`));
    }
    return itens;
}

function criar(item) {
    let el;
    if (item.tipo === 'css') {
        el = document.createElement('link');
        el.rel = 'stylesheet';
        el.href = item.href;
    } else if (item.tipo === 'style') {
        el = document.createElement('style');
        el.textContent = item.texto;
    } else {
        el = document.createElement('meta');
        el.name = item.nome;
        el.content = item.conteudo ?? '';
    }
    el.dataset.gerenciado = item.chave;
    return el;
}

function atual(chave) {
    return document.head.querySelector(`[data-gerenciado="${CSS.escape(chave)}"]`);
}

// Insere o que falta e espera as folhas novas carregarem, sem remover as da tela anterior.
export async function prepararHead(itens) {
    const esperas = [];
    for (const item of itens) {
        let el = atual(item.chave);
        if (el && item.tipo === 'style' && el.textContent !== item.texto) el.textContent = item.texto;
        if (el && item.tipo === 'meta') el.content = item.conteudo ?? '';
        if (!el) {
            el = criar(item);
            if (item.tipo === 'css') {
                esperas.push(new Promise((resolve) => {
                    el.addEventListener('load', resolve, { once: true });
                    el.addEventListener('error', resolve, { once: true });
                }));
            }
            document.head.appendChild(el);
        }
    }
    await Promise.all(esperas);
}

// Depois que a tela nova aparece: deixa somente os itens dela, na ordem declarada.
export function finalizarHead(itens) {
    const chaves = new Set(itens.map((i) => i.chave));
    document.head.querySelectorAll('[data-gerenciado]').forEach((el) => {
        if (!chaves.has(el.dataset.gerenciado)) el.remove();
    });
    for (const item of itens) {
        const el = atual(item.chave);
        if (el) document.head.appendChild(el);
    }
}
