import { useState } from 'react';
import Icon from './Icon';
import ShellPagina from './ShellPagina';
import { useApp } from '../core/contexto';
import { urlFor } from '../core/urls';

const SUCESSO = 'mt-8 rounded-2xl border border-green-400/30 bg-green-500/10 px-4 py-3 text-sm font-semibold text-green-200';
const FALHA = 'mt-8 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm font-semibold text-red-200';

export function Campo({ rotulo, px = 'px-4', children }) {
    return (
        <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-300">{rotulo}</span>
            <span className={`field flex h-14 items-center rounded-2xl ${px}`}>
                {children}
            </span>
        </label>
    );
}

// Formulário de cadastro de aluno/professor enviado à API sem sair da tela (antes: js/paginas/cadastro.js).
export default function CadastroPessoa({ tipo, titulo, cabecalho, descricao, secoes, foto, dica, endpoint, sucesso, erroPadrao }) {
    const { global: g } = useApp();
    const [retorno, setRetorno] = useState(null);
    const formId = `${tipo}-form`;

    async function enviar(e) {
        e.preventDefault();
        const formulario = e.currentTarget;
        try {
            const resposta = await fetch(urlFor(endpoint), { method: 'POST', headers: { 'X-CSRF-Token': g.csrf_token }, body: new FormData(formulario) });
            const data = await resposta.json();
            if (!resposta.ok) throw new Error(data.erro || erroPadrao);
            formulario.reset();
            setRetorno({ texto: sucesso, ok: true });
        } catch (erro) {
            setRetorno({ texto: erro.message || erroPadrao, ok: false });
        }
    }

    return (
        <ShellPagina id={`admin-cadastro-${tipo === 'aluno' ? 'aluno' : 'professores'}`} titulo={titulo}>
            <header className="mb-10 flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
                <div>
                    <span className="eyebrow">GESTÃO ESCOLAR</span>
                    <h1 className="text-3xl font-bold">{cabecalho}</h1>
                    <p className="text-gray-400">{descricao}</p>
                </div>
                <div className="flex flex-wrap gap-4">
                    <button type="reset" form={formId} className="inline-flex h-12 items-center rounded-xl border border-white/10 bg-white/5 px-6 font-bold text-white transition hover:bg-white/10">
                        Limpar
                    </button>
                    <button type="submit" form={formId} className="inline-flex h-12 items-center rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-7 font-bold text-white transition hover:brightness-110">
                        Salvar Registro
                    </button>
                </div>
            </header>
            <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_368px]">
                <form id={formId} className="glass-card cadastro-card rounded-[32px] px-6 py-8 md:px-10 lg:px-10" encType="multipart/form-data" onSubmit={enviar}><input type="hidden" name="csrf_token" value={g.csrf_token} />
                    {secoes.map(([nome, campos], i) => (
                        <section key={nome} className={i ? 'mt-9' : undefined}>
                            <h2 className="text-xl font-extrabold text-white">{nome}</h2>
                            <div className="mt-5 border-t border-white/10 pt-7">
                                <div className="grid gap-8 md:grid-cols-2">
                                    {campos}
                                </div>
                            </div>
                        </section>
                    ))}
                    <p id={`${tipo}-feedback`} className={retorno ? (retorno.ok ? SUCESSO : FALHA) : 'mt-8 hidden rounded-2xl border px-4 py-3 text-sm font-semibold'}>{retorno?.texto}</p>
                </form>
                <aside className="space-y-8">
                    <section className="glass-card cadastro-card rounded-[32px] px-8 py-9">
                        <h2 className="text-lg font-extrabold text-white">{foto.titulo}</h2>
                        <label className="mx-auto mt-7 flex aspect-square w-40 cursor-pointer flex-col items-center justify-center rounded-[22px] border-2 border-dashed border-cyan-400/35 bg-white/5 text-center transition hover:border-cyan-300 hover:bg-white/10">
                            <input type="file" name="foto_perfil" form={formId} className="sr-only" accept="image/png,image/jpeg" />
                            <span className="photo-upload-symbol"><Icon name="users" /></span>
                            <span className="mt-3 text-xs text-slate-400">Carregar Imagem</span>
                        </label>
                        <p className="mt-7 text-center text-[11px] leading-5 text-slate-400">{foto.texto}<br />Tamanho máximo: 2MB.</p>
                    </section>
                    {dica}
                </aside>
            </div>
        </ShellPagina>
    );
}
