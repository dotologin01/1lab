#Правим шапку
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
#Меняем с models на app.models
from models import db, User, Role
from forms import RegistrationForm, LoginForm, UserForm, ChangePasswordForm
import os
from datetime import datetime

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24) 
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://freedb_Artemka:%3F2uCVKXWV%24rk%26sd@sql.freedb.tech:3306/freedb_user_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Для доступа к этой странице необходима аутентификация."

# Создание таблиц
with app.app_context():
    db.create_all()

# Загрузка пользователей (Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Главная страница (список пользователей)
@app.route('/')
@login_required 
def index():
    users = User.query.all()
    return render_template('index.html', users=users, title="Список пользователей")

# Просмотр данных пользователя
@app.route('/users/<int:user_id>')
@login_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user_detail.html', user=user, title="Детали пользователя")

# Создание пользователя
@app.route('/users/create', methods=['GET', 'POST'])
@login_required
def user_create():
    form = UserForm()
    roles = Role.query.all()
    form.role_id.choices = [(role.id, role.name) for role in roles]

    if form.validate_on_submit():
        try:
            hashed_password = generate_password_hash(
                form.password.data,
                method='pbkdf2:sha256'
            )
            
            new_user = User(
                login=form.login.data,
                password=hashed_password,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                middle_name=form.middle_name.data,
                role_id=form.role_id.data,
                created_at=datetime.utcnow()
            )

            db.session.add(new_user)
            db.session.commit()
            flash('Пользователь успешно создан!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Произошла ошибка при создании пользователя: {str(e)}', 'error')
    
    return render_template('user_create.html', form=form, title="Создание пользователя")

# Редактирование пользователя
@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)  
    roles = Role.query.all()
    form.role_id.choices = [(role.id, role.name) for role in roles]
    
    if form.validate_on_submit():
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.middle_name = form.middle_name.data
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
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if check_password_hash(current_user.password, form.old_password.data):
            hashed_password = generate_password_hash(
                form.new_password.data,
                method='pbkdf2:sha256'
            )
            try:
                current_user.password = hashed_password
                db.session.commit()
                flash('Пароль успешно изменен!', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()
                flash(f'Произошла ошибка при смене пароля: {str(e)}', 'error')
        else:
            form.old_password.errors.append('Неверный старый пароль.')
    
    return render_template('change_password.html', form=form, title="Смена пароля")

# Аутентификация:
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(login=form.login.data).first()
        
        if user and user.password:
            if not user.password.startswith('pbkdf2:sha256'):
                user.password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    flash('Ошибка при обновлении пароля', 'error')
                    return render_template('login.html', form=form, title="Вход")
            
            try:
                if check_password_hash(user.password, form.password.data):
                    login_user(user, remember=form.remember.data)
                    next_page = request.args.get('next')
                    flash('Вы успешно вошли!', 'success')
                    return redirect(next_page or url_for('index'))
            except ValueError:
                flash('Ошибка проверки пароля', 'error')
                return render_template('login.html', form=form, title="Вход")
        
        flash('Неверный логин или пароль', 'error')
    return render_template('login.html', form=form, title="Вход")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
  from flask import session
  app.run(debug=True)