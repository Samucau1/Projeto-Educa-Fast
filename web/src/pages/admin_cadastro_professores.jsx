import CadastroPessoa, { Campo } from '../components/CadastroPessoa';
import { headPainel } from '../components/ShellPagina';

export const head = headPainel('cadastro.css');
export const bodyClass = 'app-page';
export const titulo = () => 'Cadastro de Professores | Educa Fast';

export default function AdminCadastroProfessores() {
    return (
        <CadastroPessoa tipo="professor" cabecalho="Cadastro de Professores" titulo="Cadastro de professores" descricao="Insira as informações do novo docente no sistema."
            endpoint="auth.cadastro_professor" sucesso="Professor cadastrado com sucesso." erroPadrao="Erro ao cadastrar professor."
            foto={{ titulo: 'Foto do Professor', texto: 'Imagem para o crachá funcional.' }}
            secoes={[
                ['Informações Gerais', <>
                    <Campo rotulo="Nome Completo"><input type="text" name="nome" placeholder="Ex: Prof. Mariana Souza" required /></Campo>
                    <Campo rotulo="Disciplina Principal"><input type="text" name="disciplina" placeholder="Ex: Matemática" required /></Campo>
                    <Campo rotulo="Formação Acadêmica"><input type="text" name="formacao" placeholder="Ex: Licenciatura em Matemática" /></Campo>
                    <Campo rotulo="Telefone / WhatsApp"><input type="tel" name="telefone" placeholder="(61) 99999-9999" /></Campo>
                    <Campo rotulo="CPF"><input type="text" name="cpf" placeholder="000.000.000-00" required /></Campo>
                    <Campo rotulo="E-mail de Acesso"><input type="email" name="email" placeholder="professor@email.com" required /></Campo>
                </>],
                ['Cargo e Horários', <>
                    <Campo rotulo="Regime de Trabalho" px="px-5"><select name="regime"><option>20 horas semanais</option><option>30 horas semanais</option><option>40 horas semanais</option><option>Dedicação exclusiva</option></select></Campo>
                    <Campo rotulo="Data de Admissão" px="px-5"><input type="date" name="data_admissao" /></Campo>
                    <Campo rotulo="Senha Inicial" px="px-5"><input type="password" name="senha" placeholder="Defina uma senha" required /></Campo>
                </>],
            ]}
            dica={<section className="rounded-[20px] border border-cyan-500/20 bg-cyan-500/10 px-8 py-8 shadow-2xl shadow-black/20">
                <h2 className="text-lg font-extrabold text-white">Nota Informativa</h2>
                <p className="mt-5 text-sm leading-6 text-slate-300">Os dados de formação acadêmica são validados automaticamente com o banco de dados do MEC. Certifique-se da grafia correta do nome.</p>
            </section>} />
    );
}
