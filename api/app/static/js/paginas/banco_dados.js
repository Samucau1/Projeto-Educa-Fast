(function () {
    document.addEventListener("react-shell:mounted", function (event) {
        inicializarFiltrosBanco(event.detail.root);
    });

    function inicializarFiltrosBanco(scope) {
        const campoBusca = scope.querySelector("#banco-search-input");
        const seletorTipo = scope.querySelector("#banco-type-select");
        const linhas = Array.from(scope.querySelectorAll(".banco-row"));
        const linhaVazia = scope.querySelector("#banco-empty-row");

        if (!campoBusca || !seletorTipo || campoBusca.dataset.pageBound === "true") {
            return;
        }

        function filtrarLinhas() {
            const termoBusca = campoBusca.value.trim().toLowerCase();
            const tipoSelecionado = seletorTipo.value;
            let linhasVisiveis = 0;

            linhas.forEach(function (linha) {
                const tipoCombina = tipoSelecionado === "todos" || linha.dataset.type === tipoSelecionado;
                const buscaCombina = !termoBusca || (linha.dataset.search || "").toLowerCase().includes(termoBusca);
                const visivel = tipoCombina && buscaCombina;

                linha.classList.toggle("hidden", !visivel);
                if (visivel) {
                    linhasVisiveis += 1;
                }
            });

            if (linhaVazia) {
                linhaVazia.classList.toggle("hidden", linhasVisiveis > 0);
            }
        }

        campoBusca.dataset.pageBound = "true";
        campoBusca.addEventListener("input", filtrarLinhas);
        seletorTipo.addEventListener("change", filtrarLinhas);
    }
})();
