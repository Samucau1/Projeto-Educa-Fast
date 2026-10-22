(function () {
    "use strict";
    function initialize(scope) {
        scope.querySelectorAll(".app-content table").forEach(function (table) {
            const headings = table.tHead ? Array.from(table.tHead.rows[0].cells).map(function (cell) { return cell.textContent.trim(); }) : [];
            table.querySelectorAll("tbody tr").forEach(function (row) {
                Array.from(row.cells).forEach(function (cell, index) { if (cell.colSpan === 1) cell.dataset.label = headings[index] || ""; });
            });
            if (table.parentElement.classList.contains("app-table-scroll")) return;
            const wrapper = document.createElement("div");
            wrapper.className = "app-table-scroll";
            wrapper.setAttribute("tabindex", "0");
            wrapper.setAttribute("role", "region");
            wrapper.setAttribute("aria-label", "Tabela com rolagem horizontal");
            table.before(wrapper);
            wrapper.append(table);
        });
        const target = window.location.hash.slice(1);
        if (["notas", "documentos", "disciplinas", "turmas"].includes(target)) {
            scope.querySelectorAll("[data-aluno-tab], [data-professor-tab]").forEach(function (button) {
                if (button.dataset.alunoTab === target || button.dataset.professorTab === target) button.click();
            });
        }
    }
    document.addEventListener("react-shell:mounted", function (event) { initialize(event.detail.root); });
    document.addEventListener("DOMContentLoaded", function () {
        initialize(document);
        document.querySelectorAll("[data-toggle-password]").forEach(function (button) {
            if (button.closest("#create-form")) return;
            button.addEventListener("click", function () {
                const input = button.parentElement.querySelector("input");
                const show = input.type === "password";
                input.type = show ? "text" : "password";
                button.setAttribute("aria-label", show ? "Ocultar senha" : "Mostrar senha");
                button.setAttribute("aria-pressed", String(show));
            });
        });
        const messagesSearch = document.getElementById("messages-search");
        if (messagesSearch) {
            messagesSearch.addEventListener("input", function () {
                const term = messagesSearch.value.trim().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
                let count = 0;
                document.querySelectorAll("[data-message]").forEach(function (card) {
                    const text = card.textContent.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
                    card.hidden = !text.includes(term);
                    if (!card.hidden) count += 1;
                });
                document.getElementById("messages-no-results").hidden = count !== 0;
                document.getElementById("messages-count").textContent = count + (count === 1 ? " mensagem" : " mensagens");
            });
        }
        const themeForm = document.getElementById("theme-form");
        if (themeForm) {
            const preview = document.querySelector("[data-theme-preview]");
            function sync() {
                ["cor_fundo", "cor_destaque"].forEach(function (name) {
                    const picker = themeForm.elements[name];
                    document.querySelector('[data-color-hex="' + name + '"]').value = picker.value;
                    preview.style.setProperty(name === "cor_fundo" ? "--preview-bg" : "--preview-accent", picker.value);
                });
            }
            themeForm.querySelectorAll("input[type=color]").forEach(function (picker) { picker.addEventListener("input", sync); });
            themeForm.querySelectorAll("[data-color-hex]").forEach(function (input) {
                input.addEventListener("input", function () {
                    if (/^#[0-9a-fA-F]{6}$/.test(input.value)) { themeForm.elements[input.dataset.colorHex].value = input.value; sync(); }
                });
            });
            document.querySelectorAll("[data-theme-preset]").forEach(function (button) {
                button.addEventListener("click", function () {
                    const colors = button.dataset.themePreset.split(",");
                    themeForm.elements.cor_fundo.value = colors[0];
                    themeForm.elements.cor_destaque.value = colors[1];
                    sync();
                });
            });
            themeForm.addEventListener("reset", function () { window.setTimeout(sync, 0); });
            sync();
        }
    });
}());
