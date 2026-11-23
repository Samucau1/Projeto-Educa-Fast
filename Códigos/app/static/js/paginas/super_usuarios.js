(function () {
    "use strict";
    const labels = { aluno: "Aluno", professor: "Professor", admin: "Administrador" };
    const descriptions = {
        aluno: "O aluno pode consultar suas disciplinas, notas e mensagens.",
        professor: "O professor pode lançar atividades e notas nas turmas vinculadas e ler mensagens.",
        admin: "O administrador pode gerenciar cadastros, turmas, disciplinas e publicar comunicados."
    };
    const createDialog = document.getElementById("create-dialog");
    const permissionDialog = document.getElementById("permission-dialog");
    const permissionForm = document.getElementById("permission-form");
    let editingUser = null;
    let trigger = null;

    function openDialog(dialog, button) {
        trigger = button || document.activeElement;
        if (!dialog.open) dialog.showModal();
    }
    document.querySelectorAll("[data-open-create]").forEach(function (button) {
        button.addEventListener("click", function () { openDialog(createDialog, button); });
    });
    document.querySelectorAll("[data-close-dialog]").forEach(function (button) {
        button.addEventListener("click", function () { button.closest("dialog").close(); });
    });
    document.querySelectorAll("dialog").forEach(function (dialog) {
        dialog.addEventListener("close", function () { if (trigger && trigger.isConnected) trigger.focus(); });
        dialog.addEventListener("click", function (event) {
            const rect = dialog.getBoundingClientRect();
            if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) dialog.close();
        });
    });

    function updateRole(form) {
        const selected = form.querySelector('input[name="tipo"]:checked');
        const role = selected ? selected.value : "aluno";
        const isPermission = form.dataset.userForm === "permission";
        const existing = isPermission && editingUser && ((role === "aluno" && editingUser.tem_aluno) || (role === "professor" && editingUser.tem_professor));
        const needsAcademic = role !== "admin" && !existing;
        form.querySelector("[data-role-preview]").textContent = descriptions[role];
        form.querySelector("[data-academic-section]").hidden = !needsAcademic;
        form.querySelectorAll("[data-academic]").forEach(function (field) {
            const show = needsAcademic && (field.dataset.academic === role || field.dataset.academic === "nome");
            field.hidden = !show;
            field.querySelectorAll("input").forEach(function (input) { input.disabled = !show; input.required = show; });
        });
        const preservedNote = form.querySelector("[data-existing-record]");
        if (preservedNote) preservedNote.hidden = !existing;
    }
    document.querySelectorAll("[data-user-form]").forEach(function (form) {
        form.querySelectorAll('input[name="tipo"]').forEach(function (radio) {
            radio.addEventListener("change", function () { updateRole(form); });
        });
        updateRole(form);
        form.addEventListener("submit", function () {
            const button = form.querySelector('button[type="submit"]');
            button.dataset.originalLabel = button.innerHTML;
            button.disabled = true;
            button.textContent = "Salvando…";
        });
    });
    window.addEventListener("pageshow", function () {
        document.querySelectorAll('[data-user-form] button[type="submit"]').forEach(function (button) {
            button.disabled = false;
            if (button.dataset.originalLabel) button.innerHTML = button.dataset.originalLabel;
        });
    });
    document.querySelectorAll("[data-toggle-password]").forEach(function (button) {
        button.addEventListener("click", function () {
            const input = button.parentElement.querySelector("input");
            const visible = input.type === "password";
            input.type = visible ? "text" : "password";
            button.setAttribute("aria-label", visible ? "Ocultar senha" : "Mostrar senha");
            button.setAttribute("aria-pressed", String(visible));
        });
    });
    function editUser(button, submitted) {
        editingUser = JSON.parse(button.dataset.editUser);
        permissionForm.reset();
        permissionForm.action = permissionForm.dataset.actionTemplate.replace(/\/0\/perfil$/, "/" + editingUser.id + "/perfil");
        permissionForm.querySelectorAll('input[name="tipo"]').forEach(function (radio) { radio.checked = radio.value === editingUser.tipo; });
        document.getElementById("edit-name").textContent = editingUser.nome;
        document.getElementById("edit-email").textContent = editingUser.email;
        document.getElementById("edit-avatar").textContent = editingUser.nome.slice(0, 2).toUpperCase();
        document.getElementById("edit-avatar").className = "avatar avatar-" + editingUser.tipo;
        document.getElementById("current-role").textContent = labels[editingUser.tipo] || editingUser.tipo;
        permissionForm.elements.nome.value = editingUser.nome;
        if (submitted) {
            Object.keys(submitted).forEach(function (name) {
                if (["nome", "cpf", "matricula", "tipo"].includes(name)) permissionForm.elements[name].value = submitted[name];
            });
        }
        updateRole(permissionForm);
        openDialog(permissionDialog, button);
    }
    document.querySelectorAll("[data-edit-user]").forEach(function (button) {
        button.addEventListener("click", function () { editUser(button); });
    });

    const search = document.getElementById("user-search");
    const roleFilter = document.getElementById("role-filter");
    const rows = Array.from(document.querySelectorAll("[data-user-row]"));
    function normalize(text) { return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR"); }
    function filterUsers() {
        const term = normalize(search.value.trim());
        let count = 0;
        rows.forEach(function (row) {
            const match = normalize(row.dataset.search).includes(term) && (!roleFilter.value || row.dataset.role === roleFilter.value);
            row.hidden = !match;
            if (match) count += 1;
        });
        document.getElementById("users-empty").hidden = count !== 0;
        document.getElementById("results-count").textContent = count + " de " + rows.length + " usuários";
    }
    search.addEventListener("input", filterUsers);
    roleFilter.addEventListener("change", filterUsers);
    document.getElementById("clear-filters").addEventListener("click", function () { search.value = ""; roleFilter.value = ""; filterUsers(); search.focus(); });

    const tabs = Array.from(document.querySelectorAll("[data-tab]"));
    function selectTab(tab) {
        tabs.forEach(function (item) {
            const selected = item === tab;
            item.classList.toggle("active", selected);
            item.setAttribute("aria-selected", String(selected));
            item.tabIndex = selected ? 0 : -1;
            document.getElementById(item.dataset.tab).hidden = !selected;
        });
    }
    tabs.forEach(function (tab, index) {
        tab.addEventListener("click", function () { selectTab(tab); });
        tab.addEventListener("keydown", function (event) {
            let next;
            if (event.key === "ArrowRight") next = tabs[(index + 1) % tabs.length];
            if (event.key === "ArrowLeft") next = tabs[(index + tabs.length - 1) % tabs.length];
            if (event.key === "Home") next = tabs[0];
            if (event.key === "End") next = tabs[tabs.length - 1];
            if (next) { event.preventDefault(); selectTab(next); next.focus(); }
        });
    });
    document.querySelectorAll("[data-dismiss-notice]").forEach(function (button) {
        button.addEventListener("click", function () { button.closest(".notice").remove(); });
    });
    if (createDialog.hasAttribute("data-open-on-load")) openDialog(createDialog);
    if (permissionDialog.dataset.openUser) {
        const button = document.querySelector('[data-user-id="' + permissionDialog.dataset.openUser + '"]');
        if (button) editUser(button, JSON.parse(permissionDialog.dataset.submitted || "{}"));
    }
}());
