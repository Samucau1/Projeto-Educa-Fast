from flask import render_template


def render_dashboard(context=None):
    return render_template("admin_painel.html", **(context or {}))
