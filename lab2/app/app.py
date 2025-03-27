from flask import Flask, render_template, request, make_response, redirect, url_for
import re
app = Flask(__name__)

# 1. Отображение данных запроса
@app.route('/request_data', methods=['GET', 'POST'])
def request_data():
    """Отображает данные запроса."""
    url_params = request.args.to_dict()
    headers = dict(request.headers)
    cookies = request.cookies
    form_params = request.form.to_dict()  
    return render_template('request_data.html',
                           url_params=url_params,
                           headers=headers,
                           cookies=cookies,
                           form_params=form_params,
                           title="Данные запроса")

# 2. Форма с обработкой ошибок
@app.route('/phone_form', methods=['GET', 'POST'])
def phone_form():
    """Страница с формой для ввода номера телефона и его проверки."""
    error_message = None
    formatted_number = None
    phone_number = request.args.get('phone', '')  

    if request.method == 'POST':
        phone_number = request.form.get('phone') 

        if phone_number:
            digits_only = re.sub(r'\D', '', phone_number)
            number_length = len(digits_only)

            if not re.match(r"^[\d\s()+.-]+$", phone_number):
                error_message = "Недопустимый ввод. В номере телефона встречаются недопустимые символы."
            elif number_length not in (10, 11):
                error_message = "Недопустимый ввод. Неверное количество цифр."
            else:
                # Преобразуем к формату 8-***-***-**-**
                if number_length == 11:
                    if digits_only.startswith('7') or digits_only.startswith('8'):
                        formatted_number = f"8-{digits_only[1:4]}-{digits_only[4:7]}-{digits_only[7:9]}-{digits_only[9:11]}"
                    else:
                        error_message = "Недопустимый ввод. Неверный формат номера телефона (11 цифр)."
                else:
                    formatted_number = f"8-{digits_only[0:3]}-{digits_only[3:6]}-{digits_only[6:8]}-{digits_only[8:10]}"
        else:
            error_message = "Пожалуйста, введите номер телефона." 

    return render_template('phone_form.html',
                           error_message=error_message,
                           formatted_number=formatted_number,
                           phone_number=phone_number,
                           title="Форма телефона")


@app.route('/', methods=['GET', 'POST'])
def index():
    cookie_value = request.cookies.get('my_cookie')  

    if request.method == 'POST':
        action = request.form.get('action')  
        if action == 'set':
            new_value = request.form.get('cookie_value')
            response = make_response(render_template('index.html', cookie_value=new_value, title="Главная"))
            response.set_cookie('my_cookie', new_value)
            return response
        elif action == 'delete':
            response = make_response(render_template('index.html', cookie_value=None, title="Главная"))
            response.delete_cookie('my_cookie')
            return response

    return render_template('index.html', cookie_value=cookie_value, title="Главная")

if __name__ == '__main__':
    app.run(debug=True)