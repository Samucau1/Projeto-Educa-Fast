import CadastroPessoa, { Campo } from '../components/CadastroPessoa';
import { headPainel } from '../components/ShellPagina';

export const head = headPainel('cadastro.css');
export const bodyClass = 'app-page';
export const titulo = () => 'Cadastro de Alunos | Educa Fast';

export default function AdminCadastroAluno() {
    return (
        <CadastroPessoa tipo="aluno" cabecalho="Cadastro de Alunos" titulo="Cadastro de alunos" descricao="Insira as informações do novo aluno no sistema."
            endpoint="auth.cadastro_aluno" sucesso="Aluno cadastrado com sucesso." erroPadrao="Erro ao cadastrar aluno."
            foto={{ titulo: 'Foto do Aluno', texto: 'Formatos aceitos: JPG, PNG.' }}
            secoes={[
                ['Informações Pessoais', <>
                    <Campo rotulo="Nome Completo"><input type="text" name="nome" placeholder="Ex: João da Silva" required /></Campo>
                    <Campo rotulo="Número de Matrícula"><input type="text" name="matricula" placeholder="Ex: 20240001" required /></Campo>
                    <Campo rotulo="Curso / Série"><select name="curso"><option value="">Selecione um curso</option><option>Ensino Fundamental</option><option>Ensino Médio</option><option>Educação de Jovens e Adultos</option></select></Campo>
                    <Campo rotulo="Status da Matrícula"><select name="status"><option>Ativo</option><option>Pendente</option><option>Inativo</option></select></Campo>
                    <Campo rotulo="E-mail de Acesso"><input type="email" name="email" placeholder="aluno@email.com" required /></Campo>
                    <Campo rotulo="Senha Inicial"><input type="password" name="senha" placeholder="Defina uma senha" required /></Campo>
                </>],
                ['Documentação', <>
                    <Campo rotulo="CPF" px="px-5"><input type="text" name="cpf" placeholder="000.000.000-00" /></Campo>
                    <Campo rotulo="Data de Nascimento" px="px-5"><input type="date" name="data_nascimento" /></Campo>
                </>],
            ]}
            dica={<section className="management-tip">
                <h2 className="text-lg font-extrabold text-white">Dica de Gestão</h2>
                <p className="mt-5 text-sm leading-6 text-slate-300">Confira a matrícula e o e-mail antes de salvar. Após o cadastro, compartilhe as credenciais com o aluno e organize os documentos na página de detalhes.</p>
            </section>} />
    );
}
