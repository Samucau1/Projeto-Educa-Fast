import { useState } from 'react';
import Icon from '../components/Icon';
import Marca from '../components/Marca';
import { useApp } from '../core/contexto';
import { urlFor } from '../core/urls';
import { css, headWorkspace } from '../core/head';

export const head = (g) => [...headWorkspace(g), css('login.css')];
export const bodyClass = 'login-page';
export const titulo = (_d, g) => `Entrar | ${g.escola?.nome ?? 'Educa Fast'}`;

const DESTINOS = { SUPERADMIN: '/super/usuarios', ADMIN: '/admin/dashboard', ALUNO: '/aluno', PROFESSOR: '/professor' };

export default function Login({ g }) {
    const { navegar } = useApp();
    const escola = g.escola;
    const [erro, setErro] = useState('');
    const [carregando, setCarregando] = useState(false);
    const [verSenha, setVerSenha] = useState(false);

    async function enviar(e) {
        e.preventDefault();
        const form = e.currentTarget;
        setErro('');
        setCarregando(true);
        try {
            const resposta = await fetch(new URL('/login', window.location.origin), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: form.email.value, senha: form.senha.value }),
            });
            const data = await resposta.json();
            if (!resposta.ok) throw new Error(data?.erro || 'Falha ao logar');
            if (!DESTINOS[data.tipo]) throw new Error('Tipo de usuário sem área configurada');
            setCarregando(false);
            navegar(DESTINOS[data.tipo]);
        } catch (erroRequisicao) {
            setErro(erroRequisicao.message || 'Erro ao conectar com o servidor');
            setCarregando(false);
        }
    }

    return (
        <>
            <main className="login-layout">
                <section className="login-story" aria-label={`${escola.nome ?? 'Educa Fast'}, gestão escolar`}>
                    <Marca escola={escola} />
                    <div className="login-intro"><span className="eyebrow">MAIS CONEXÃO. MAIS POSSIBILIDADES.</span><h1>Sua escola.<br />Mais <span>conectada.</span></h1><p>Menos distância entre a gestão, os professores e quem está aqui para aprender.</p></div>
                    <div className="school-illustration" aria-hidden="true"><div className="school-orbit orbit-one"></div><div className="school-orbit orbit-two"></div><div className="school-center">{escola.sigla ?? 'ef'}<span>↗</span></div><span className="school-node node-users"><Icon name="users" /></span><span className="school-node node-book"><Icon name="book" /></span><span className="school-node node-mail"><Icon name="mail" /></span><span className="school-node node-cap"><Icon name="cap" /></span><span className="school-caption">Um lugar para toda a escola</span></div>
                    <div className="login-features"><span><Icon name="grid" /> Gestão integrada</span><span><Icon name="book" /> Aprendizado</span><span><Icon name="mail" /> Comunicação</span></div>
                    <p className="login-story-footer">Pessoas e conhecimento, sempre mais próximos.</p>
                </section>
                <section className="login-access">
                    <div className="login-card"><span className="login-card-icon"><Icon name="shield" /></span><span className="eyebrow">BOM TER VOCÊ POR AQUI</span><h2>Bem-vindo de volta<span>.</span></h2><p>Entre para acessar seu espaço na escola.</p>
                        <form id="login-form" className="login-form" onSubmit={enviar}><input type="hidden" name="csrf_token" value={g.csrf_token} />
                            <label className="login-field" htmlFor="email">E-mail institucional<span className="login-input-wrap"><Icon name="mail" /><input name="email" id="email" type="email" placeholder="seu.nome@escola.com.br" autoComplete="username" required autoFocus /></span></label>
                            <label className="login-field" htmlFor="senha">Senha<span className="login-input-wrap"><Icon name="lock" /><input name="senha" id="senha" type={verSenha ? 'text' : 'password'} placeholder="Digite sua senha" autoComplete="current-password" required /><button type="button" className="icon-button" data-toggle-password aria-label={verSenha ? 'Ocultar senha' : 'Mostrar senha'} aria-pressed={String(verSenha)} onClick={() => setVerSenha(!verSenha)}><Icon name="eye" /></button></span></label>
                            <p id="login-error" className="login-error" role="alert" hidden={!erro}>{erro}</p>
                            <button type="submit" className="button button-primary login-submit" disabled={carregando}>{carregando ? 'Entrando…' : <>Acessar sistema <Icon name="arrow" /></>}</button>
                        </form>
                        <p className="login-help">Seu acesso é fornecido pela administração da escola.<br />Se precisar de ajuda, entre em contato com a secretaria.</p>
                    </div>
                    <div className="login-access-footer"><span><Icon name="shield" /> Um acesso para cada responsabilidade</span><small>{escola.nome ?? 'Educa Fast'} · {escola.subtitulo ?? 'Gestão escolar'}</small></div>
                </section>
            </main>
            <p style={{ textAlign: 'center' }}><a href={urlFor('privacidade.aviso')}>Privacidade e protecao de dados</a></p>
        </>
    );
}
