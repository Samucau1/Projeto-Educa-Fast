import React from 'react';
import { BrowserRouter, Link, Navigate, Route, Routes, useParams, useSearchParams } from 'react-router-dom';
import { AuthProvider, HomeRedirect, RequireRole } from './components/Auth';
import { LogoutButton } from './components/Navigation';
import { DataPage } from './components/DataPage';
import { PageStyles } from './components/PageStyles';
import AlterarSenha from './pages/AlterarSenha';
import Gestao from './pages/Gestao';
import Login from './pages/Login';
import AdminPainel from './pages/AdminPainel';
import AdminBancoDados from './pages/AdminBancoDados';
import AdminCadastroAluno from './pages/AdminCadastroAluno';
import AdminCadastroProfessores from './pages/AdminCadastroProfessores';
import AdminComunicados from './pages/AdminComunicados';
import AdminDisciplinas from './pages/AdminDisciplinas';
import AdminTurmas from './pages/AdminTurmas';
import AdminDetalhesAluno from './pages/AdminDetalhesAluno';
import AdminDetalhesProfessor from './pages/AdminDetalhesProfessor';
import AlunoPainel from './pages/AlunoPainel';
import AlunoDisciplina from './pages/AlunoDisciplina';
import ProfessorPainel from './pages/ProfessorPainel';

const pages = [
    ['/admin/dashboard', 'secretaria', AdminPainel, '/api/admin/dashboard', null, 'Painel Geral'],
    ['/admin/banco-de-dados', 'secretaria', AdminBancoDados, '/api/admin/registros', 'banco', 'Banco de Dados'],
    ['/admin/cadastro-alunos', 'secretaria', AdminCadastroAluno, '/api/admin/banco-de-dados', 'cadastro', 'Cadastro de Alunos'],
    ['/admin/cadastro-professores', 'secretaria', AdminCadastroProfessores, '/api/admin/banco-de-dados', 'cadastro', 'Cadastro de Professores'],
    ['/admin/comunicados', 'secretaria', AdminComunicados, '/api/admin/comunicados', 'comunicados', 'Comunicados'],
    ['/admin/disciplinas', 'secretaria', AdminDisciplinas, '/api/admin/disciplinas', 'disciplinas', 'Disciplinas'],
    ['/admin/turmas', 'secretaria', AdminTurmas, '/api/admin/turmas', 'turmas', 'Turmas'],
    ['/admin/alunos/:id', 'secretaria', AdminDetalhesAluno, '/api/admin/alunos/:id', 'detalhes', 'Detalhes do Aluno'],
    ['/admin/professores/:id', 'secretaria', AdminDetalhesProfessor, '/api/admin/professores/:id', 'detalhes', 'Detalhes do Professor'],
    ['/aluno', 'aluno', AlunoPainel, '/api/aluno', 'aluno', 'Área do Aluno'],
    ['/aluno/disciplinas/:id', 'aluno', AlunoDisciplina, '/api/aluno/disciplinas/:id', 'aluno', 'Disciplina'],
    ['/professor', 'professor', ProfessorPainel, '/api/professor', 'professor', 'Área do Professor'],
];

const aliases = [
    ...['/dashboard', '/dashboard.html', '/admin_painel.html'].map((path) => [path, '/admin/dashboard']),
    ...['/cadastro/alunos', '/cadastro_aluno.html', '/admin_cadastro_aluno.html'].map((path) => [path, '/admin/cadastro-alunos']),
    ...['/cadastro/professores', '/cadastro_professores.html', '/admin_cadastro_professores.html'].map((path) => [path, '/admin/cadastro-professores']),
    ...['/banco-de-dados', '/banco_de_dados.html', '/admin_banco_dados.html'].map((path) => [path, '/admin/banco-de-dados']),
    ...['comunicados', 'disciplinas', 'turmas'].flatMap((name) => [[`/${name}`, `/admin/${name}`], [`/admin_${name}.html`, `/admin/${name}`]]),
    ...['/alunos/:id', '/detalhes_aluno/:id', '/admin_detalhes_aluno/:id'].map((path) => [path, '/admin/alunos/:id']),
    ...['/professores/:id', '/detalhes_professor/:id', '/admin_detalhes_professor/:id'].map((path) => [path, '/admin/professores/:id']),
    ...['/detalhes_aluno.html', '/admin_detalhes_aluno.html'].map((path) => [path, '/admin/alunos/:id']),
    ...['/detalhes_professor.html', '/admin_detalhes_professor.html'].map((path) => [path, '/admin/professores/:id']),
    ['/aluno/dashboard', '/aluno'], ['/professor/dashboard', '/professor'],
];

function LegacyRedirect({ to }) {
    const params = useParams();
    const [search] = useSearchParams();
    return <Navigate to={to.replace(':id', encodeURIComponent(params.id || search.get('id') || 'ultimo'))} replace />;
}

export default function App() {
    return <BrowserRouter><AuthProvider><Routes>
        <Route path="/alterar-senha" element={<AlterarSenha />} />
        <Route path="/gestao" element={<RequireRole role="admin"><Gestao /></RequireRole>} />
        <Route path="/" element={<HomeRedirect />} />
        <Route path="/login" element={<PageStyles name="login" title="Login"><Login /></PageStyles>} />
        <Route path="/logout" element={<main className="p-10"><LogoutButton /></main>} />
        {pages.map(([path, role, component, endpoint, style, title]) => <Route key={path} path={path} element={
            <RequireRole role={role}><PageStyles name={style} title={title}>
                <DataPage key={path} component={component} endpoint={endpoint} />
            </PageStyles></RequireRole>
        } />)}
        {aliases.map(([path, to]) => <Route key={path} path={path} element={<LegacyRedirect to={to} />} />)}
        <Route path="*" element={<main className="p-10"><h1 className="text-2xl mb-4">Página não encontrada</h1><Link to="/">Voltar ao início</Link></main>} />
    </Routes></AuthProvider></BrowserRouter>;
}
