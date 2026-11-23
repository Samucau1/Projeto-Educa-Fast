from flask import jsonify, request
from werkzeug.exceptions import HTTPException, InternalServerError

from app.spa import is_spa_request, render_page


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
        return render_page("erro.html", codigo=error.code, titulo=title, mensagem=message), error.code

    for code in pages:
        app.register_error_handler(code, handle)

    # Demais erros (409, 413, 429, 507, 500...) fora dos módulos com página própria:
    # na SPA viram a tela de erro; no acesso direto, a resposta padrão continua a mesma.
    outros = {
        409: ("Não foi possível concluir", "Os dados mudaram ou já existem. Recarregue a página e tente novamente."),
        413: ("Arquivo muito grande", "O arquivo excede o limite permitido. Envie um arquivo menor."),
        429: ("Muitas tentativas", "Aguarde alguns minutos e tente novamente."),
        507: ("Armazenamento cheio", "Não há espaço para novos arquivos. Contate a administração."),
        500: ("Algo deu errado", "Não foi possível concluir a ação. Tente novamente em instantes."),
    }

    def handle_outros(error):
        if not is_spa_request():
            return error
        code = getattr(error, "code", None) or 500
        title, message = outros.get(code, outros[500])
        descricao = getattr(error, "description", None)
        if descricao and descricao != type(error).description:
            message = descricao
        return render_page("erro.html", codigo=code, titulo=title, mensagem=message), code

    app.register_error_handler(HTTPException, handle_outros)
    app.register_error_handler(InternalServerError, handle_outros)
