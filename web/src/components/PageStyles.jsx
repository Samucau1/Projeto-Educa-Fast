import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import cadastro from '../styles/cadastro.css?inline';
import detalhes from '../styles/detalhes.css?inline';
import disciplinas from '../styles/admin_disciplinas.css?inline';
import turmas from '../styles/admin_turmas.css?inline';
import comunicados from '../styles/admin_comunicados.css?inline';
import banco from '../styles/admin_banco_dados.css?inline';
import aluno from '../styles/aluno_painel.css?inline';
import professor from '../styles/professor_painel.css?inline';
import login from '../styles/login.css?inline';

const styles = { cadastro, detalhes, disciplinas, turmas, comunicados, banco, aluno, professor, login };
export function PageStyles({ name, title, children }) {
    useEffect(() => {
        document.title = `${title} | Secretaria Escolar DF`;
        window.scrollTo(0, 0);
    }, [title]);
    return <>
        {styles[name] && createPortal(<style>{styles[name]}</style>, document.head)}
        {children}
    </>;
}
