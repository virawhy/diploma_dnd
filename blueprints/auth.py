from flask import Blueprint

from main import *


bp = Blueprint('auth', __name__)


@bp.route('/auth.html', methods=("POST", "GET"))
def auth():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if not user:
            flash('Акаунт із такою e-mail адресою не знайдено. Перевірте адресу або зареєструйтесь.', 'account_missing')
            return redirect(url_for('auth'))

        if not check_password_hash(user.password, password):
            flash('Пароль введено невірно.', 'error')
            return redirect(url_for('auth'))
        login_user(user)
        return redirect(url_for("profile"))

    return render_template('auth.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth'))


@bp.route("/registration.html", methods=("POST", "GET"))
def registration():
    if request.method == "POST":
        username = request.form['username'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash("Паролі не збігаються", "error")
            return redirect(url_for("registration"))
        if User.query.filter_by(username=username).first():
            flash("Профіль із таким нікнеймом вже існує. Оберіть інший нікнейм.", "username_taken")
            return redirect(url_for("registration"))
        else:
            try:
                hash = generate_password_hash(password)
                new_user = User(username=username, email=request.form['email'],
                                password=hash)
                db.session.add(new_user)
                db.session.flush()
                db.session.commit()
                return redirect(url_for("auth"))
            except Exception as e:
                db.session.rollback()
                current_app.logger.exception("Error adding user to database: %s", e)
                flash("Не вдалося створити акаунт", "error")
    return render_template("registration.html")

