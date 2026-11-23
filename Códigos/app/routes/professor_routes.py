from flask import Blueprint, abort, jsonify, redirect, render_template, request, session, url_for

from app.controllers.professor_controller import (
    get_teacher_area_data,
    launch_activity,
    save_student_grade,
    upload_requested_document,
)
from app.routes.guards import teacher_required

professor_bp = Blueprint("professor", __name__)


@professor_bp.route("/professor", methods=["GET"])
@professor_bp.route("/professor/dashboard", methods=["GET"])
def dashboard():
    teacher_required()
    data = get_teacher_area_data(session.get("user_id"))
    if not data:
        abort(404)

    return render_template("professor_painel.html", **data)


@professor_bp.route("/professor/notas/salvar", methods=["POST"])
def salvar_nota():
    teacher_required()
    response, status = save_student_grade(session.get("user_id"), request.form)
    if 200 <= status < 300:
        return redirect(url_for("professor.dashboard"))

    return jsonify(response), status


@professor_bp.route("/professor/atividades/lancar", methods=["POST"])
def lancar_atividade():
    teacher_required()
    response, status = launch_activity(session.get("user_id"), request.form, request.files)
    if 200 <= status < 300:
        return redirect(url_for("professor.dashboard"))

    return jsonify(response), status


@professor_bp.route("/professor/documentos/upload", methods=["POST"])
def upload_documento_professor():
    teacher_required()
    response, status = upload_requested_document(
        session.get("user_id"),
        request.form,
        request.files,
    )
    if 200 <= status < 300:
        return redirect(url_for("professor.dashboard"))

    return jsonify(response), status
