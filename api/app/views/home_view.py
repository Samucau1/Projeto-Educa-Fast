from app.spa import render_page


def render_home(context, form_data=None):
    return render_page("login.html", form_data=form_data or {}, **context)
