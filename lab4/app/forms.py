from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
import re

def validate_login(form, field):
    """Проверяет, чтобы логин состоял только из латинских букв и цифр."""
    pattern = r'^[a-zA-Z0-9]+$'
    if not re.match(pattern, field.data):
        raise ValidationError('Логин должен состоять только из латинских букв и цифр.')

def validate_password(form, field):
    """Проверяет надежность пароля."""
    password = field.data
    if len(password) < 8:
        raise ValidationError('Длина пароля должна быть не менее 8 символов.')
    if len(password) > 128:
        raise ValidationError('Длина пароля должна быть не более 128 символов.')
    if not re.search(r"[A-Z]", password):
        raise ValidationError('Пароль должен содержать хотя бы одну заглавную букву.')
    if not re.search(r"[a-z]", password):
        raise ValidationError('Пароль должен содержать хотя бы одну строчную букву.')
    if not re.search(r"\d", password):
        raise ValidationError('Пароль должен содержать хотя бы одну цифру.')
    if re.search(r"\s", password):
        raise ValidationError('Пароль не должен содержать пробелы.')

class RegistrationForm(FlaskForm):
    """Форма для регистрации."""
    login = StringField('Логин', validators=[DataRequired(), Length(min=5), validate_login])
    password = PasswordField('Пароль', validators=[DataRequired(), validate_password])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password', message='Пароли должны совпадать')])
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    """Форма для входа."""
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class UserForm(FlaskForm):
    """Форма для создания/редактирования пользователя."""
    login = StringField('Логин', validators=[DataRequired(), Length(min=5), validate_login])
    password = PasswordField('Пароль', validators=[DataRequired(), validate_password])
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    middle_name = StringField('Отчество')
    role_id = SelectField('Роль', coerce=int) 
    submit = SubmitField('Сохранить')

class ChangePasswordForm(FlaskForm):
    """Форма для смены пароля."""
    old_password = PasswordField('Старый пароль', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[DataRequired(), validate_password])
    confirm_new_password = PasswordField('Подтвердите новый пароль', validators=[DataRequired(), EqualTo('new_password', message='Пароли должны совпадать')])
    submit = SubmitField('Изменить пароль')