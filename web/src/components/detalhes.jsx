import { urlFor } from '../core/urls';
import { j } from '../core/formatos';

// Peças comuns às telas de detalhes de aluno e professor.
export function Campo({ rotulo, children }) {
    return <label><span>{rotulo}</span>{' '}{children}</label>;
}

export function Vazio({ children }) {
    return (
        <div className="bg-white/5 p-4 rounded-xl mb-4 border border-white/5 text-gray-400">
            {children}
        </div>
    );
}

export function ItemSolicitacao({ s }) {
    return (
        <div className="documento-request-item">
            <div>
                <span className="block text-white">{j(s.titulo)}</span>{' '}
                <span className="text-xs text-gray-500">{j(s.mensagem)}</span>
            </div>
            <div className="text-right">
                <span className={`documento-status documento-status-${s.status}`}>{j(s.status_label)}</span>{' '}
                <span className="block text-xs text-gray-500 mt-2">{j(s.data)}</span>
            </div>
        </div>
    );
}

export function ItemArquivo({ titulo, detalhe, arquivo }) {
    return (
        <div className="bg-white/5 p-4 rounded-xl mb-4 flex justify-between border border-white/5">
            <div>
                <span className="block text-white">{j(titulo)}</span>{' '}
                <span className="text-xs text-gray-500">{detalhe}</span>
            </div>
            <a href={urlFor('document.download_arquivo', { filename: arquivo })} className="text-cyan-400">Baixar</a>
        </div>
    );
}

export function Foto({ pessoa }) {
    return pessoa.foto_perfil
        ? <img src={urlFor('document.perfil_arquivo', { filename: pessoa.foto_perfil })} alt={`Foto de ${pessoa.nome}`} className="w-32 h-32 rounded-full mx-auto mb-4 border-4 border-white/10 object-cover" />
        : <div className="w-32 h-32 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full mx-auto mb-4 border-4 border-white/10"></div>;
}

export function AbasDocumentos() {
    return (
        <div className="flex gap-4 border-b border-white/10 mb-6" data-documento-tabs>
            <button type="button" className="documento-tab pb-2 border-b-2 border-cyan-400 text-white" data-documento-tab="solicitacoes">Solicitações</button>
            <button type="button" className="documento-tab pb-2 text-gray-500" data-documento-tab="enviados">Enviados</button>
        </div>
    );
}

export const H4 = ({ children }) => <h4 className="mb-4 text-sm font-bold uppercase tracking-wider text-gray-400">{children}</h4>;
