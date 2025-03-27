from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my-secret-key' 


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  
login_manager.login_message = "Для доступа к этой странице необходимо войти."


class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = str(id) 
        self.username = username
        self.password = password

user = User(id=1, username="user", password=generate_password_hash("qwerty"))
users = {user.id: user}


@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)


@app.route('/')
def index():
    return render_template('index.html', title="Главная", user=current_user)


@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html', title="Секретная страница", user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = True if request.form.get('remember') else False

        user_obj = next((user for user in users.values() if user.username == username), None) 

        if user_obj and check_password_hash(user_obj.password, password):
            login_user(user_obj, remember=remember)  
            flash('Вы успешно вошли!', 'success')
            next_page = request.args.get('next') 
            return redirect(next_page or url_for('index'))  
        else:
            flash('Неверный логин или пароль.', 'error')
            return render_template('login.html', title="Вход", error="Неверный логин или пароль")

    return render_template('login.html', title="Вход")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))


@app.route('/counter')
def counter():
    session['visits'] = session.get('visits', 0) + 1  
    return render_template('counter.html', title='Счётчик посещений', visits=session['visits'], user=current_user)

if __name__ == '__main__':
    from flask import session
    app.run(debug=True)