(function (window) {
    const h = window.React.createElement;

    const gruposAbas = [
        {
            seletorAba: "[data-aluno-tab]",
            seletorPainel: "[data-aluno-panel]",
            chaveAba: "alunoTab",
            chavePainel: "alunoPanel",
            classeOculta: "aluno-panel-hidden"
        },
        {
            seletorAba: "[data-professor-tab]",
            seletorPainel: "[data-professor-panel]",
            chaveAba: "professorTab",
            chavePainel: "professorPanel",
            classeOculta: "professor-panel-hidden"
        },
        {
            seletorAba: "[data-documento-tab]",
            seletorPainel: "[data-documento-panel]",
            chaveAba: "documentoTab",
            chavePainel: "documentoPanel",
            classeOculta: "hidden"
        },
        {
            seletorAba: "[data-professor-section-tab]",
            seletorPainel: "[data-professor-section-panel]",
            chaveAba: "professorSectionTab",
            chavePainel: "professorSectionPanel",
            classeOculta: "hidden"
        }
    ];

    function PaginaShell({ html }) {
        return h("div", {
            className: "react-shell flex w-full",
            dangerouslySetInnerHTML: { __html: html }
        });
    }

    function montar(root) {
        const template = document.getElementById(root.dataset.reactTemplate);

        if (!template || root.dataset.reactMounted === "true") {
            return;
        }

        root.dataset.reactMounted = "true";
        window.ReactDOM.createRoot(root).render(h(PaginaShell, { html: template.innerHTML }));
        window.setTimeout(function () {
            inicializarComportamentosPagina(root);
            dispararEventoMontado(root);
        }, 0);
    }

    function montarTodos() {
        document.querySelectorAll("[data-react-shell]").forEach(montar);
    }

    function inicializarComportamentosPagina(scope) {
        gruposAbas.forEach(function (tabConfig) {
            inicializarAbas(scope, tabConfig);
        });
    }

    function inicializarAbas(scope, config) {
        const tabs = Array.from(scope.querySelectorAll(config.seletorAba));
        const panels = Array.from(scope.querySelectorAll(config.seletorPainel));

        if (!tabs.length || !panels.length) {
            return;
        }

        tabs.forEach(function (tab) {
            if (tab.dataset.reactBound === "true") {
                return;
            }

            tab.dataset.reactBound = "true";
            tab.addEventListener("click", function () {
                ativarAba(tabs, panels, tab.dataset[config.chaveAba], config);
            });
        });
    }

    function dispararEventoMontado(root) {
        root.dispatchEvent(new CustomEvent("react-shell:mounted", {
            bubbles: true,
            detail: { root }
        }));
    }

    function ativarAba(tabs, panels, abaAtiva, config) {
        tabs.forEach(function (tab) {
            const ativa = tab.dataset[config.chaveAba] === abaAtiva;

            tab.classList.toggle("bg-cyan-500/10", ativa);
            tab.classList.toggle("text-cyan-400", ativa);
            tab.classList.toggle("border", ativa);
            tab.classList.toggle("border-cyan-500/20", ativa);
            tab.classList.toggle("border-b-2", ativa);
            tab.classList.toggle("border-cyan-400", ativa);
            tab.classList.toggle("text-white", ativa);
            tab.classList.toggle("text-gray-500", !ativa);
            tab.classList.toggle("text-gray-300", !ativa);
        });

        panels.forEach(function (panel) {
            panel.classList.toggle(config.classeOculta, panel.dataset[config.chavePainel] !== abaAtiva);
        });
    }

    window.ReactShell = {
        montar,
        montarTodos
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", montarTodos);
    } else {
        montarTodos();
    }
})(window);
