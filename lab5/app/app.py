from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Role, VisitLog
from forms import RegistrationForm, LoginForm, UserForm, ChangePasswordForm
from reports.routes import reports_bp
import os
from datetime import datetime
from functools import wraps
import logging

from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
app.debug = True  # <--- Добавьте эту строку
logging.basicConfig(level=logging.DEBUG)  # Включаем логирование на уровне DEBUG
logger = logging.getLogger(__name__)
app.config['SECRET_KEY'] = os.urandom(24) 
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://freedb_Artemka:%3F2uCVKXWV%24rk%26sd@sql.freedb.tech:3306/freedb_user_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Для доступа к этой странице необходима аутентификация."

app.register_blueprint(reports_bp, url_prefix='/reports') 

# Создание таблиц
with app.app_context():
    db.create_all()

# Загрузка пользователей (Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Проверка прав
def check_rights(role_names):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Для доступа к этой странице необходима аутентификация.", 'error')
                return redirect(url_for('login', next=request.url))
            if current_user.role and current_user.role.name in role_names:
                return f(*args, **kwargs)
            else:
                flash("У вас недостаточно прав для доступа к данной странице.", 'error')
                return redirect(url_for('index'))
        return decorated_function
    return decorator

@app.before_request
def log_visit():
    if request.endpoint and request.endpoint != 'static':
        user_id = current_user.get_id() if current_user.is_authenticated else None
        visit_log = VisitLog(path=request.path, user_id=user_id)
        db.session.add(visit_log)
        db.session.commit()

# Главная страница (список пользователей)
@app.route('/')
@login_required
@check_rights(['admin', 'user'])
def index():
    users = User.query.all()
    return render_template('index.html', users=users, title="Список пользователей")

# Просмотр данных пользователя
@app.route('/users/<int:user_id>')
@login_required
@check_rights(['admin', 'user'])
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user_detail.html', user=user, title="Детали пользователя")

# Создание пользователя
@app.route('/users/create', methods=['GET', 'POST'])
@login_required
@check_rights(['admin'])
def user_create():
    form = UserForm()
    roles = Role.query.all()
    # Заполняем choices в любом случае (и при GET, и при POST)
    form.role_id.choices = [(role.id, role.name) for role in roles]

    if form.validate_on_submit():
        logger.debug("Форма прошла валидацию.")
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(
            login=form.login.data,
            password=hashed_password,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            middle_name=form.middle_name.data,
            role_id=form.role_id.data,
            created_at=datetime.utcnow()
        )

        try:
            logger.debug(f"Попытка добавления пользователя: {new_user.login}")
            db.session.add(new_user)
            logger.debug("Пользователь добавлен в сессию.")
            db.session.commit()
            logger.debug("Сессия закоммичена.")
            flash('Пользователь успешно создан!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Произошла ошибка при создании пользователя: {str(e)}")
            flash(f'Произошла ошибка при создании пользователя: {str(e)}', 'error')
    else:
        logger.debug("Форма не прошла валидацию.")
        for field, errors in form.errors.items():
            for error in errors:
                logger.error(f"Ошибка в поле {field}: {error}")
        return render_template('user_create.html', form=form, title="Создание пользователя")
# Редактирование пользователя
@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@check_rights(['admin', 'user'])
def user_edit(user_id):
    user = User.query.get_or_404(user_id)
    if not (current_user.role.name == 'admin' or current_user.id == user_id):
          flash("У вас недостаточно прав для редактирования этого пользователя.", 'error')
          return redirect(url_for('index'))
    form = UserForm(obj=user)  
    roles = Role.query.all()
    form.role_id.choices = [(role.id, role.name) for role in roles]
    if current_user.role.name == 'user':
         del form.role_id
    
    if form.validate_on_submit():
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.middle_name = form.middle_name.data
        if current_user.role.name == 'admin':
            user.role_id = form.role_id.data
        try:
            db.session.commit()
            flash('Пользователь успешно отредактирован!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Произошла ошибка при редактировании пользователя: {str(e)}', 'error')
    return render_template('user_edit.html', form=form, user=user, title="Редактирование пользователя")

# Удаление пользователя
@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@check_rights(['admin'])
def user_delete(user_id):
    user = User.query.get_or_404(user_id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash('Пользователь успешно удален!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Произошла ошибка при удалении пользователя: {str(e)}', 'error')
    return redirect(url_for('index'))

# Смена пароля
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
@check_rights(['admin', 'user'])
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if check_password_hash(current_user.password, form.old_password.data):
            hashed_password = generate_password_hash(form.new_password.data, method='pbkdf2:sha256')
            current_user.password = hashed_password
            try:
                db.session.commit()
                flash('Пароль успешно изменен!', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()
                flash(f'Произошла ошибка при смене пароля: {str(e)}', 'error')
        else:
            form.old_password.errors.append('Неверный старый пароль.')
            return render_template('change_password.html', form=form, title="Смена пароля")

    return render_template('change_password.html', form=form, title="Смена пароля")


# Аутентификация:
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(login=form.login.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Вы успешно вошли!', 'success')
            next_page = request.args.get('next') 
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверный логин или пароль.', 'error')
            return render_template('login.html', form=form, title="Вход")
    return render_template('login.html', form=form, title="Вход")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))


@app.teardown_request
def teardown_request(exception=None):
    db.session.remove()

if __name__ == '__main__':
    from flask import session
    app.run(debug=True)