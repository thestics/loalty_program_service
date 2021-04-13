from __main__ import app
from flask_security import current_user
from flask import redirect


@app.route('/')
def root():
    if current_user.is_active and\
       current_user.is_authenticated:
        return redirect('/admin/')
    else:
        return redirect('/login')