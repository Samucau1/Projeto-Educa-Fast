import GestaoBase, { bodyGestao, tituloGestao } from '../components/GestaoBase';
import Token from '../components/Token';

export const bodyClass = bodyGestao();
export const titulo = tituloGestao('Gestão acadêmica');

function TurmaSelect({ turmas }) {
    return <label>Turma e ano<select name="turma_id" required><option value="">Selecione</option>{turmas.map((t) => <option key={t.id} value={t.id}>{t.nome} · {t.ano_letivo}</option>)}</select></label>;
}

export default function CursoTurmas({ d }) {
    const estado = (id) => d.estados[id];
    return (
        <GestaoBase titulo="Gestão acadêmica" error={d.error}>
            <section className="page-heading"><div><span className="eyebrow">ORGANIZAÇÃO ACADÊMICA</span><h1>Turmas, professores e matérias</h1><p>Defina exatamente quem leciona cada matéria, em cada turma e ano.</p></div></section>
            <div className="course-grid"><section className="panel course-panel"><h2>Criar turma</h2><form method="post" className="course-form"><Token /><input type="hidden" name="acao" value="criar" /><label>Nome<input name="nome" maxLength={120} required /></label><label>Código<input name="codigo" maxLength={30} required /></label><label>Ano letivo<input type="number" name="ano_letivo" min="1900" max="2200" required /></label><button className="button button-primary">Criar turma</button></form></section>
                <section className="panel course-panel"><h2>Atribuir professor e matéria</h2><form method="post" className="course-form"><Token /><input type="hidden" name="acao" value="atribuir" /><TurmaSelect turmas={d.turmas} /><label>Professor<select name="professor_id" required>{d.professores.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}</select></label><label>Disciplina<select name="disciplina_id" required>{d.disciplinas.map((disc) => <option key={disc.id} value={disc.id}>{disc.nome}</option>)}</select></label><p>Ao atribuir, esta turma passa a usar permissões explícitas. Cadastre cada combinação autorizada.</p><button className="button button-primary">Salvar atribuição</button></form></section>
                <section className="panel course-panel"><h2>Matrículas</h2><form method="post" className="course-form"><Token /><TurmaSelect turmas={d.turmas} /><label>Aluno<select name="aluno_id" required>{d.alunos.map((a) => <option key={a.id} value={a.id}>{a.nome} · {a.matricula}</option>)}</select></label><label>Operação<select name="acao"><option value="matricular">Matricular</option><option value="desmatricular">Remover da turma e revogar cursos</option></select></label><button className="button button-primary">Atualizar matrícula</button></form></section></div>
            <section className="panel course-panel"><h2>Turmas cadastradas</h2>{d.turmas.length ? d.turmas.map((turma) => {
                const e = estado(turma.id);
                const arquivada = e && e.arquivada;
                return (
                    <details key={turma.id} className="course-outline"><summary>{turma.nome} · {turma.ano_letivo} · {turma.codigo} · {arquivada ? 'Arquivada' : (e ? 'Gestão explícita' : 'Legada: reconciliar atribuições')}</summary>
                        {d.atribuicoes.filter(([, vinculo]) => vinculo.turma_id === turma.id).map(([atribuicao, , prof, disc]) => <div key={atribuicao.id} className="course-actions"><span>{prof.nome} — {disc.nome} · {atribuicao.ativo ? 'Ativo' : 'Revogado'}</span>{atribuicao.ativo && <form method="post"><Token /><input type="hidden" name="acao" value="revogar" /><input type="hidden" name="turma_id" value={turma.id} /><input type="hidden" name="atribuicao_id" value={atribuicao.id} /><button className="button">Revogar</button></form>}</div>)}
                        {!arquivada && <><form method="post" className="course-form"><Token /><input type="hidden" name="acao" value="editar" /><input type="hidden" name="turma_id" value={turma.id} /><label>Nome<input name="nome" defaultValue={turma.nome} maxLength={120} required /></label><label>Ano letivo<input type="number" name="ano_letivo" defaultValue={turma.ano_letivo} min="1900" max="2200" required /></label><button className="button">Salvar dados</button></form><form method="post"><Token /><input type="hidden" name="acao" value="arquivar" /><input type="hidden" name="turma_id" value={turma.id} /><button className="button">Arquivar turma e suspender acessos</button></form></>}
                    </details>
                );
            }) : <p>Nenhuma turma cadastrada.</p>}</section>
        </GestaoBase>
    );
}
