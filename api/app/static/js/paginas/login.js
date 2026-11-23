(function () {
    function inicializarLogin(root) {
        const form = root.querySelector("#login-form");

        if (!form || form.dataset.pageBound === "true") {
            return;
        }

        form.dataset.pageBound = "true";
        form.addEventListener("submit", enviarLogin);
    }
    document.addEventListener("react-shell:mounted", function (event) { inicializarLogin(event.detail.root); });
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () { inicializarLogin(document); });
    } else {
        inicializarLogin(document);
    }

    function enviarLogin(event) {
        event.preventDefault();

        const form = event.currentTarget;
        const error = form.querySelector("#login-error");
        const button = form.querySelector("button[type='submit']");

        definirErro(error, "");
        definirCarregamento(button, true);

        fetch(new URL("/login", window.location.origin), {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: form.email.value,
                senha: form.senha.value
            })
        })
            .then(function (response) {
                return response.json().then(function (data) {
                    if (!response.ok) {
                        throw new Error(data?.erro || "Falha ao logar");
                    }

                    return data;
                });
            })
            .then(redirecionarPorPerfil)
            .catch(function (erroRequisicao) {
                definirErro(error, erroRequisicao.message || "Erro ao conectar com o servidor");
            })
            .finally(function () {
                definirCarregamento(button, false);
            });
    }

    function redirecionarPorPerfil(data) {
        const destinos = {
            SUPERADMIN: "/super/usuarios",
            ADMIN: "/admin/dashboard",
            ALUNO: "/aluno",
            PROFESSOR: "/professor"
        };

        if (!destinos[data.tipo]) {
            throw new Error("Tipo de usuário sem área configurada");
        }

        window.location.href = destinos[data.tipo];
    }

    function definirErro(element, message) {
        element.textContent = message;
        element.classList.toggle("hidden", !message);
        element.hidden = !message;
    }

    function definirCarregamento(button, loading) {
        if (!button.dataset.originalLabel) button.dataset.originalLabel = button.innerHTML;
        button.disabled = loading;
        if (loading) button.textContent = "Entrando…";
        else button.innerHTML = button.dataset.originalLabel;
    }
})();
