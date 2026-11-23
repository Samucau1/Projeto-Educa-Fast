import { useEffect } from 'react';

// Grupos de abas das telas de painel (antes: js/compartilhado/shell_react.js), com as mesmas classes.
const GRUPOS = [
    { seletorAba: '[data-aluno-tab]', seletorPainel: '[data-aluno-panel]', chaveAba: 'alunoTab', chavePainel: 'alunoPanel', classeOculta: 'aluno-panel-hidden' },
    { seletorAba: '[data-professor-tab]', seletorPainel: '[data-professor-panel]', chaveAba: 'professorTab', chavePainel: 'professorPanel', classeOculta: 'professor-panel-hidden' },
    { seletorAba: '[data-documento-tab]', seletorPainel: '[data-documento-panel]', chaveAba: 'documentoTab', chavePainel: 'documentoPanel', classeOculta: 'hidden' },
    { seletorAba: '[data-professor-section-tab]', seletorPainel: '[data-professor-section-panel]', chaveAba: 'professorSectionTab', chavePainel: 'professorSectionPanel', classeOculta: 'hidden' },
];

function ativarAba(tabs, panels, abaAtiva, config) {
    tabs.forEach((tab) => {
        const ativa = tab.dataset[config.chaveAba] === abaAtiva;
        tab.classList.toggle('active', ativa);
        tab.setAttribute('aria-pressed', String(ativa));
        tab.classList.toggle('bg-cyan-500/10', ativa);
        tab.classList.toggle('text-cyan-400', ativa);
        tab.classList.toggle('border', ativa);
        tab.classList.toggle('border-cyan-500/20', ativa);
        tab.classList.toggle('border-b-2', ativa);
        tab.classList.toggle('border-cyan-400', ativa);
        tab.classList.toggle('text-white', ativa);
        tab.classList.toggle('text-gray-500', !ativa);
        tab.classList.toggle('text-gray-300', !ativa);
    });
    panels.forEach((panel) => {
        panel.classList.toggle(config.classeOculta, panel.dataset[config.chavePainel] !== abaAtiva);
    });
}

// Liga as abas da tela e abre a aba indicada no endereço (#notas, #documentos...).
export function useAbas() {
    useEffect(() => {
        const limpar = [];
        GRUPOS.forEach((config) => {
            const tabs = Array.from(document.querySelectorAll(config.seletorAba));
            const panels = Array.from(document.querySelectorAll(config.seletorPainel));
            if (!tabs.length || !panels.length) return;
            tabs.forEach((tab) => {
                const clique = () => ativarAba(tabs, panels, tab.dataset[config.chaveAba], config);
                tab.addEventListener('click', clique);
                limpar.push(() => tab.removeEventListener('click', clique));
            });
        });
        const alvo = window.location.hash.slice(1);
        if (['notas', 'documentos', 'disciplinas', 'turmas'].includes(alvo)) {
            document.querySelectorAll('[data-aluno-tab], [data-professor-tab]').forEach((button) => {
                if (button.dataset.alunoTab === alvo || button.dataset.professorTab === alvo) button.click();
            });
        }
        return () => limpar.forEach((fn) => fn());
    }, []);
}
