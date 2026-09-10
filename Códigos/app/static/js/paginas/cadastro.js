(function (window) {
    const configPagina = window.__REACT_PAGE__ || {};

    const formularios = [
        {
            idFormulario: "aluno-form",
            idRetorno: "aluno-feedback",
            endpoint: configPagina.routes?.cadastroAluno,
            mensagemSucesso: "Aluno cadastrado com sucesso.",
            mensagemPadraoErro: "Erro ao cadastrar aluno."
        },
        {
            idFormulario: "professor-form",
            idRetorno: "professor-feedback",
            endpoint: configPagina.routes?.cadastroProfessor,
            mensagemSucesso: "Professor cadastrado com sucesso.",
            mensagemPadraoErro: "Erro ao cadastrar professor."
        }
    ];

    document.addEventListener("react-shell:mounted", function (event) {
        formularios.forEach(function (config) {
            inicializarFormularioAjax(event.detail.root, config);
        });
    });

    function inicializarFormularioAjax(scope, config) {
        const formulario = scope.querySelector(`#${config.idFormulario}`);
        const retorno = scope.querySelector(`#${config.idRetorno}`);

        if (!formulario || !retorno || !config.endpoint || formulario.dataset.pageBound === "true") {
            return;
        }

        formulario.dataset.pageBound = "true";
        formulario.addEventListener("submit", function (event) {
            event.preventDefault();

            fetch(config.endpoint, {
                method: "POST",
                body: new FormData(formulario)
            })
                .then(function (response) {
                    return response.json().then(function (data) {
                        if (!response.ok) {
                            throw new Error(data.erro || config.mensagemPadraoErro);
                        }

                        return data;
                    });
                })
                .then(function () {
                    formulario.reset();
                    mostrarRetorno(retorno, config.mensagemSucesso, true);
                })
                .catch(function (erro) {
                    mostrarRetorno(retorno, erro.message || config.mensagemPadraoErro, false);
                });
        });
    }

    function mostrarRetorno(retorno, mensagem, sucesso) {
        retorno.textContent = mensagem;
        retorno.className = sucesso
            ? "mt-8 rounded-2xl border border-green-400/30 bg-green-500/10 px-4 py-3 text-sm font-semibold text-green-200"
            : "mt-8 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm font-semibold text-red-200";
    }
})(window);
