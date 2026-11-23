from flask import render_template


def render_home(context, form_data=None):
    return render_template("login.html", form_data=form_data or {}, **context)
