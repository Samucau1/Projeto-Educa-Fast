import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { AppContext } from './contexto';
import { definirRotas } from './urls';
import { finalizarHead, headWorkspace, prepararHead } from './head';
import { paginas } from '../pages';

const SPA = { 'X-EducaFast-SPA': '1' };
// Endereços que não são telas: arquivos, downloads e exportações seguem pelo navegador.
const NAO_TELA = /^\/(static|arquivos|uploads)(\/|$)|\/(download|exportar|relatorio)/;

function caminhoAtual() {
    return window.location.pathname + window.location.search;
}

function nomeArquivo(resposta) {
    const cd = resposta.headers.get('Content-Disposition') || '';
    const m = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(cd);
    return m ? decodeURIComponent(m[1]) : 'arquivo';
}

function headDaPagina(modulo, estado) {
    if (modulo.head) return modulo.head(estado.global, estado.dados);
    return [...headWorkspace(estado.global), ...(modulo.css || [])];
}

export default function App() {
    const [estado, setEstado] = useState(null);
    const [erro, setErro] = useState(null);
    const sequencia = useRef(0);

    const navegar = useCallback(async (url, { method = 'GET', body = null, substituir = false } = {}) => {
        const id = ++sequencia.current;
        const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
        let resposta;
        try {
            resposta = await fetch(url, {
                method,
                body,
                credentials: 'same-origin',
                headers: method === 'GET' ? SPA : { ...SPA, 'X-CSRF-Token': csrf },
            });
        } catch {
            setErro('Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.');
            return;
        }
        if (id !== sequencia.current) return;
        if (!resposta.headers.get('X-EducaFast-Pagina')) {
            if (method === 'GET') {
                window.location.assign(url);
                return;
            }
            // POST que devolve arquivo (ex.: exportação de dados): baixa sem sair da tela.
            const blob = await resposta.blob();
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = nomeArquivo(resposta);
            link.click();
            URL.revokeObjectURL(link.href);
            return;
        }
        const payload = await resposta.json();
        const modulo = paginas[payload.pagina];
        if (!modulo) {
            setErro(`Tela não encontrada: ${payload.pagina}`);
            return;
        }
        const destino = new URL(resposta.url);
        const hash = method === 'GET' ? new URL(url, window.location.href).hash : '';
        const novoEstado = { ...payload, chave: id, url: destino.pathname + destino.search };
        novoEstado.elementosHead = await prepararHead(headDaPagina(modulo, novoEstado));
        if (id !== sequencia.current) return;
        const endereco = novoEstado.url + hash;
        if (endereco !== window.location.pathname + window.location.search + window.location.hash) {
            window.history[substituir ? 'replaceState' : 'pushState']({}, '', endereco);
        }
        setErro(null);
        setEstado(novoEstado);
        if (!hash) window.scrollTo(0, 0);
    }, []);

    // Carga inicial: mapa de rotas e tela do endereço atual.
    useEffect(() => {
        fetch('/api/rotas', { credentials: 'same-origin' })
            .then((r) => r.json())
            .then((rotas) => {
                definirRotas(rotas);
                navegar(caminhoAtual() + window.location.hash, { substituir: true });
            })
            .catch(() => setErro('Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.'));
        const voltar = () => navegar(caminhoAtual() + window.location.hash, { substituir: true });
        window.addEventListener('popstate', voltar);
        return () => window.removeEventListener('popstate', voltar);
    }, [navegar]);

    // Links internos e formulários viram navegação da SPA.
    useEffect(() => {
        function clique(e) {
            if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
            const a = e.target.closest && e.target.closest('a[href]');
            if (!a || (a.target && a.target !== '_self') || a.hasAttribute('download')) return;
            const destino = new URL(a.href, window.location.href);
            if (destino.origin !== window.location.origin || NAO_TELA.test(destino.pathname)) return;
            if (destino.pathname === window.location.pathname && destino.search === window.location.search && destino.hash) return;
            e.preventDefault();
            navegar(destino.pathname + destino.search + destino.hash);
        }
        function envio(e) {
            if (e.defaultPrevented) return;
            const form = e.target;
            if (form.dataset.spa === 'off') return;
            e.preventDefault();
            const metodo = (form.getAttribute('method') || 'GET').toUpperCase();
            const acao = form.getAttribute('action') || caminhoAtual();
            const dados = new FormData(form, e.submitter || undefined);
            if (metodo === 'GET') {
                const destino = new URL(acao, window.location.href);
                destino.search = new URLSearchParams(dados).toString();
                navegar(destino.pathname + destino.search);
            } else {
                navegar(acao, { method: metodo, body: dados });
            }
        }
        document.addEventListener('click', clique);
        document.addEventListener('submit', envio);
        return () => {
            document.removeEventListener('click', clique);
            document.removeEventListener('submit', envio);
        };
    }, [navegar]);

    const modulo = estado && paginas[estado.pagina];

    useLayoutEffect(() => {
        if (!estado) return;
        finalizarHead(estado.elementosHead);
        document.body.className = typeof modulo.bodyClass === 'function' ? modulo.bodyClass(estado.dados, estado.global) : (modulo.bodyClass || '');
        document.title = modulo.titulo ? modulo.titulo(estado.dados, estado.global) : 'Educa Fast';
        document.getElementById('root')?.removeAttribute('data-spa-loading');
    }, [estado, modulo]);

    const contexto = useMemo(() => estado && { ...estado, navegar }, [estado, navegar]);

    if (erro) {
        return <main className="app-content" role="alert"><p>{erro}</p><button type="button" className="button button-primary" onClick={() => window.location.reload()}>Recarregar</button></main>;
    }
    if (!estado) return null;
    const Pagina = modulo.default;
    return (
        <AppContext.Provider value={contexto}>
            <Pagina key={estado.chave} d={estado.dados} g={estado.global} form={estado.form} args={estado.args} mensagens={estado.mensagens} />
        </AppContext.Provider>
    );
}
