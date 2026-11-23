// URLs geradas a partir do mapa de rotas da API (/api/rotas), igual ao url_for do Flask.
let rotas = {};

export function definirRotas(mapa) {
    rotas = mapa || {};
}

export function urlFor(endpoint, params = {}) {
    const modelo = rotas[endpoint];
    if (!modelo) throw new Error(`Rota desconhecida: ${endpoint}`);
    const resto = { ...params };
    let url = modelo.replace(/\{(\w+)\}/g, (_, nome) => {
        const valor = resto[nome];
        delete resto[nome];
        return encodeURIComponent(String(valor));
    });
    const query = new URLSearchParams();
    Object.entries(resto).forEach(([chave, valor]) => {
        if (valor !== undefined && valor !== null) query.append(chave, String(valor));
    });
    const texto = query.toString();
    return texto ? `${url}?${texto}` : url;
}

const BASE = import.meta.env.BASE_URL;

// Arquivos de public/ (CSS e fontes) servidos junto com o build.
export function asset(caminho) {
    return BASE + caminho.replace(/^\//, '');
}
