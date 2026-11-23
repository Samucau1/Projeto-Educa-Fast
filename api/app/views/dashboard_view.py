from app.spa import render_page


def render_dashboard(context=None):
    return render_page("admin_painel.html", **(context or {}))
