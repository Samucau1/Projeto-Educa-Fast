"""Self-service rights with authenticated ownership and accountable handling."""
from datetime import date, datetime
from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from app.database import get_session
from app.models import (AlunoModel, ProfessorModel, UsuarioModel, DocumentoModel, NotaModel,
                        PedidoPrivacidadeModel, AuditoriaPrivacidadeModel)
from app.routes.guards import admin_required

privacidade_bp = Blueprint("privacidade", __name__)
TIPOS = {"acesso": "Acesso e informações", "correcao": "Correção de dados", "eliminacao": "Eliminação ou anonimização",
         "oposicao": "Oposição ou revogação de consentimento", "compartilhamento": "Informações sobre compartilhamento"}


def titular():
    if not session.get("user_id"):
        abort(403)
    return session["user_id"]


def serialize_profile(profile):
    if not profile:
        return None
    # Explicit field list: never include passwords, internal identity links or other users.
    fields = ("nome", "cpf", "matricula", "curso_serie", "status_matricula", "data_nascimento",
              "telefone", "disciplina_principal", "formacao_academica", "regime_trabalho", "data_admissao")
    data = {}
    for field in fields:
        if hasattr(profile, field):
            value = getattr(profile, field)
            data[field] = value.isoformat() if isinstance(value, (date, datetime)) else value
    return data


@privacidade_bp.get("/privacidade")
def aviso():
    return render_template("privacidade.html", controlador=current_app.config["LGPD_CONTROLADOR"],
                           contato=current_app.config["LGPD_CONTATO"])


@privacidade_bp.route("/minha-privacidade", methods=["GET", "POST"])
def meus_pedidos():
    user_id = titular()
    with get_session() as db:
        if request.method == "POST":
            tipo = request.form.get("tipo", "")
            detalhe = request.form.get("detalhe", "").strip()
            if tipo not in TIPOS or len(detalhe) > 2000:
                abort(400, "Solicitacao invalida; limite de 2000 caracteres.")
            db.query(UsuarioModel).filter_by(id=user_id).with_for_update().one()
            if db.query(PedidoPrivacidadeModel).filter(PedidoPrivacidadeModel.usuario_id == user_id,
                                                     PedidoPrivacidadeModel.status.in_(["aberto", "em_analise"])).count() >= 5:
                abort(409, "Voce ja possui cinco pedidos abertos. Acompanhe os protocolos existentes.")
            pedido = PedidoPrivacidadeModel(usuario_id=user_id, tipo=tipo, detalhe=detalhe)
            db.add(pedido)
            db.flush()
            db.add(AuditoriaPrivacidadeModel(ator_id=user_id, acao="pedido_criado", referencia=pedido.id))
            db.commit()
            flash("Solicitação registrada. Acompanhe o protocolo nesta página.", "success")
            return redirect(url_for("privacidade.meus_pedidos"))
        pedidos = db.query(PedidoPrivacidadeModel).filter_by(usuario_id=user_id).order_by(PedidoPrivacidadeModel.id.desc()).all()
        return render_template("minha_privacidade.html", pedidos=pedidos, tipos=TIPOS, administracao=False)


@privacidade_bp.post("/minha-privacidade/exportar")
def exportar():
    user_id = titular()
    with get_session() as db:
        user = db.get(UsuarioModel, user_id)
        aluno = db.query(AlunoModel).filter_by(usuario_id=user_id).first()
        professor = db.query(ProfessorModel).filter_by(usuario_id=user_id).first()
        data = {"conta": {"email": user.email, "perfil": user.tipo}, "aluno": serialize_profile(aluno),
                "professor": serialize_profile(professor), "notas": [], "documentos": [], "pedidos": []}
        if aluno:
            from app.services.academico import boletim
            data['boletim_por_periodo'] = boletim(db, aluno.id)
            data["notas"] = [{"disciplina_id": n.disciplina_id, "nota": str(n.nota), "observacao": n.observacao}
                             for n in db.query(NotaModel).filter_by(aluno_id=aluno.id)]
        documents = db.query(DocumentoModel)
        documents = documents.filter_by(aluno_id=aluno.id) if aluno else documents.filter_by(professor_id=professor.id, aluno_id=None) if professor else None
        if documents is not None:
            data["documentos"] = [{"titulo": d.titulo, "arquivo": d.caminho_arquivo} for d in documents]
        data["pedidos"] = [{"protocolo": p.id, "tipo": p.tipo, "detalhe": p.detalhe, "status": p.status, "resposta": p.resposta}
                           for p in db.query(PedidoPrivacidadeModel).filter_by(usuario_id=user_id)]
        db.add(AuditoriaPrivacidadeModel(ator_id=user_id, acao="dados_exportados"))
        db.commit()
    response = jsonify(data)
    response.headers["Content-Disposition"] = 'attachment; filename="meus-dados-educafast.json"'
    return response


@privacidade_bp.route("/admin/privacidade", methods=["GET"])
def administrar():
    admin_required()
    page = max(1, request.args.get("pagina", 1, type=int))
    with get_session() as db:
        pedidos = db.query(PedidoPrivacidadeModel).order_by(PedidoPrivacidadeModel.id.desc()).offset((page - 1) * 100).limit(101).all()
        return render_template("minha_privacidade.html", pedidos=pedidos[:100], tipos=TIPOS,
                               administracao=True, pagina=page, proxima=len(pedidos) > 100)


@privacidade_bp.post("/admin/privacidade/<int:pedido_id>")
def responder(pedido_id):
    admin_required()
    status = request.form.get("status", "")
    resposta = request.form.get("resposta", "").strip()
    if status not in {"em_analise", "concluido", "indeferido"} or not resposta or len(resposta) > 2000:
        abort(400, "Informe status e resposta fundamentada de ate 2000 caracteres.")
    with get_session() as db:
        pedido = db.get(PedidoPrivacidadeModel, pedido_id)
        if not pedido:
            abort(404)
        if pedido.status in {"concluido", "indeferido"}:
            abort(409, "Pedido encerrado. Registre novo protocolo para nova analise.")
        changed = db.query(PedidoPrivacidadeModel).filter(
            PedidoPrivacidadeModel.id == pedido_id,
            PedidoPrivacidadeModel.status.in_(["aberto", "em_analise"])
        ).update({"status": status, "resposta": resposta}, synchronize_session=False)
        if not changed:
            abort(409, "Pedido encerrado por outro atendimento. Recarregue a pagina.")
        db.add(AuditoriaPrivacidadeModel(ator_id=session["user_id"], acao="pedido_" + status, referencia=pedido.id))
        db.commit()
    return redirect(url_for("privacidade.administrar"))
