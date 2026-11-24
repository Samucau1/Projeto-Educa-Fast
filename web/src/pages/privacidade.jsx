import GestaoBase, { bodyGestao, tituloGestao } from '../components/GestaoBase';
import { urlFor } from '../core/urls';

export const bodyClass = bodyGestao();
export const titulo = tituloGestao('Privacidade e proteção de dados');

export default function Privacidade({ d, g }) {
    return (
        <GestaoBase titulo="Privacidade e proteção de dados" error={d.error}>
            <section className="page-heading"><div><span className="eyebrow">SEUS DADOS, SEUS DIREITOS</span><h1>Privacidade<span>.</span></h1><p>Entenda como seus dados são tratados no Educa Fast.</p></div></section>
            <section className="panel" style={{ padding: '2rem', maxWidth: '900px' }}>
                <h2>Quem é responsável</h2>
                <p>{d.controlador || 'Instituição responsável ainda não configurada. Procure a secretaria antes de fornecer dados reais.'}</p>
                <p>Contato de privacidade: {d.contato || 'A secretaria deve informar o canal de atendimento e configurar o contato antes do uso com dados reais.'}</p>
                <h2>Dados e finalidades</h2><p>O sistema guarda conta de acesso, nome, matrícula, CPF quando informado, dados acadêmicos e profissionais, fotos, notas, documentos e solicitações. Esses dados apoiam a gestão escolar, autenticação, comunicação institucional e atendimento aos titulares. Não publique dados pessoais ou documentos de alunos em comunicados gerais.</p>
                <h2>Acesso e compartilhamento</h2><p>Alunos acessam seus registros. Professores acessam as turmas vinculadas. Administração e superperfil têm acesso conforme suas atribuições. Hospedagem, backups e demais operadores devem ser informados pela instituição; esta instalação não mantém um cadastro verificado desses terceiros.</p>
                <h2>Base legal e prazo de guarda</h2><p>A instituição deve informar a base legal aplicável a cada finalidade e seus prazos de retenção. A criação da conta não representa consentimento genérico. Pedidos de exclusão são analisados considerando obrigações de guarda, defesa de direitos e demais hipóteses legais. O sistema não elimina automaticamente históricos escolares.</p>
                <h2>Crianças e adolescentes</h2><p>O tratamento deve observar o melhor interesse do estudante. A instituição deve verificar representação legal quando necessária e informar responsáveis de forma clara. Não envie documentos de identidade ou dados sensíveis no texto livre dos pedidos.</p>
                <h2>Cookies e segurança</h2><p>Utilizamos cookie de sessão para autenticação e proteção de formulários. Não há ferramenta de publicidade ou análise comportamental configurada pelo aplicativo. Fotos e documentos exigem autenticação. A instituição deve usar HTTPS, controlar acessos e proteger backups.</p>
                <h2>Como exercer seus direitos</h2><p>Você pode solicitar informações, acesso, correção, análise de eliminação/anonimização, oposição ou revogação quando aplicável e informações sobre compartilhamento. Representantes e pessoas sem acesso à conta podem procurar o contato da instituição. Revogar consentimento não afeta tratamentos mantidos por outra base legal válida.</p>
                {g.sessao.user_id ? <a className="button button-primary" href={urlFor('privacidade.meus_pedidos')}>Meus dados e solicitações</a> : <a className="button button-primary" href={urlFor('home.home')}>Voltar para entrar</a>}
                <p><a href="https://www.gov.br/anpd/pt-br/assuntos/titular-de-dados/direito-dos-titulares" rel="noreferrer">Direitos dos titulares — ANPD</a></p>
            </section>
        </GestaoBase>
    );
}
