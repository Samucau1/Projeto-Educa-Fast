from flask import jsonify, render_template, request


def register_error_pages(app):
    pages = {
        400: ("Vamos revisar essa solicitação", "Não foi possível concluir a ação. Confira os dados e tente novamente."),
        403: ("Este acesso não está disponível", "Seu perfil não tem permissão para abrir esta página. Volte ao seu painel para continuar."),
        404: ("Não encontramos esta página", "O endereço pode ter mudado ou a informação não está disponível para seu perfil."),
        405: ("Esta ação não está disponível", "Abra a página pelo menu e utilize as ações disponíveis para continuar."),
    }

    def handle(error):
        title, message = pages[error.code]
        if error.code == 400 and error.description.startswith("Formulário expirado"):
            message = error.description
        if request.is_json or request.accept_mimetypes.best == "application/json":
            return jsonify({"erro": message}), error.code
        return render_template("erro.html", codigo=error.code, titulo=title, mensagem=message), error.code

    for code in pages:
        app.register_error_handler(code, handle)
