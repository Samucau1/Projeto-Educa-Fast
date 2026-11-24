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

const gerenciados = () => Array.from(document.head.querySelectorAll('[data-gerenciado]'));

// Garante os itens da tela nova na ordem declarada, sem mover nenhum elemento existente:
// mover um <link> faz o navegador reaplicar a folha e a página "pisca" sem estilo.
// Itens novos (ou fora de ordem, que viram uma cópia na posição certa, vinda do cache)
// entram desativados (media="not all") para não alterar a tela atual enquanto carregam;
// finalizarHead os ativa no mesmo quadro em que a tela nova aparece.
// Devolve os elementos usados pela tela.
export async function prepararHead(itens) {
    const usados = [];
    const esperas = [];
    let cursor = null;
    for (const item of itens) {
        let el = gerenciados().find((e) => e.dataset.gerenciado === item.chave && !usados.includes(e)
            && (item.tipo !== 'style' || e.textContent === item.texto)
            && (!cursor || (cursor.compareDocumentPosition(e) & Node.DOCUMENT_POSITION_FOLLOWING)));
        if (el) {
            if (item.tipo === 'meta') el.content = item.conteudo ?? '';
        } else {
            el = criar(item);
            if (item.tipo !== 'meta') {
                el.media = 'not all';
                el.dataset.pendente = '';
            }
            if (item.tipo === 'css') {
                esperas.push(new Promise((resolve) => {
                    el.addEventListener('load', resolve, { once: true });
                    el.addEventListener('error', resolve, { once: true });
                }));
            }
            if (cursor) cursor.after(el);
            else {
                const primeiro = gerenciados()[0];
                if (primeiro) primeiro.before(el);
                else document.head.appendChild(el);
            }
        }
        usados.push(el);
        cursor = el;
    }
    await Promise.all(esperas);
    return usados;
}

// No quadro em que a tela nova aparece: ativa os itens dela e remove o que ela não usa.
export function finalizarHead(usados) {
    usados.forEach((el) => {
        if ('pendente' in el.dataset) {
            el.removeAttribute('media');
            delete el.dataset.pendente;
        }
    });
    gerenciados().forEach((el) => {
        if (!usados.includes(el)) el.remove();
    });
}
