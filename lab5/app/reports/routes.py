from flask import Blueprint, render_template, send_file, url_for, redirect, request, flash
from models import VisitLog, User, db
import pandas as pd
from flask_login import login_required, current_user
from functools import wraps
from math import ceil
from io import StringIO, BytesIO
import csv

reports_bp = Blueprint('reports', __name__, template_folder='templates')


PER_PAGE = 10

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

# Visit logs
@reports_bp.route('/visit_logs', defaults={'page': 1})
@reports_bp.route('/visit_logs/page/<int:page>')
@login_required
@check_rights(['admin', 'user'])
def visit_logs(page):
    """Отображает журнал посещений."""
    if current_user.role.name == 'admin':
        visits = VisitLog.query.order_by(VisitLog.created_at.desc()).paginate(page=page, per_page=PER_PAGE, error_out=False)
    else:
        visits = VisitLog.query.filter_by(user_id=current_user.id).order_by(VisitLog.created_at.desc()).paginate(page=page, per_page=PER_PAGE, error_out=False)
    return render_template('reports/visit_logs.html', title='Журнал посещений', visits=visits)

@reports_bp.route('/pages')
@login_required
@check_rights(['admin'])
def reports_pages():
    """Отчет по страницам"""
    page = request.args.get('page', 1, type=int)
    pages = db.session.query(VisitLog.path, db.func.count(VisitLog.id))\
        .group_by(VisitLog.path)\
        .order_by(db.func.count(VisitLog.id).desc())\
        .paginate(page=page, per_page=PER_PAGE, error_out=False)
    return render_template('reports/reports_pages.html', pages=pages, page=page, title='Отчет по страницам', pagination=pages)

@reports_bp.route('/users')
@login_required
@check_rights(['admin'])
def reports_users():
    """Отчет по пользователям"""
    page = request.args.get('page', 1, type=int)
    users = db.session.query(User.first_name, db.func.count(VisitLog.id))\
        .outerjoin(VisitLog, User.id == VisitLog.user_id)\
        .group_by(User.id)\
        .order_by(db.func.count(VisitLog.id).desc())\
        .paginate(page=page, per_page=PER_PAGE, error_out=False)
    return render_template('reports/reports_users.html', users=users, title='Отчет по пользователям', page=page)

@reports_bp.route('/pages/csv')
@login_required
@check_rights(['admin'])
def reports_pages_csv():
    """Экспорт отчета по страницам в CSV"""
    try:
        # Запрос данных
        data = db.session.query(
            VisitLog.path, 
            db.func.count(VisitLog.id)
        ).group_by(VisitLog.path).all()

        if not data:
            flash("Нет данных для экспорта в CSV.", "info")
            return redirect(url_for('reports.reports_pages'))

        # Создаем DataFrame
        df = pd.DataFrame(data, columns=['Страница', 'Количество посещений'])

        # Сохраняем CSV в BytesIO
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)

        # Отправляем файл
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name='reports_pages.csv'
        )

    except Exception as e:
        flash(f"Ошибка при формировании CSV: {e}", "error")
        return redirect(url_for('reports.reports_pages'))

from sqlalchemy import func

@reports_bp.route('/users/csv')
@login_required
@check_rights(['admin'])
def reports_users_csv():
    """Экспорт отчета по пользователям в CSV"""
    try:
        data = db.session.query(
            func.concat(User.last_name, ' ', User.first_name, ' ', func.coalesce(User.middle_name, '')),
            func.count(VisitLog.id)
        ).outerjoin(VisitLog, User.id == VisitLog.user_id) \
         .group_by(User.id) \
         .all()

        if not data:
            flash("Нет данных для экспорта в CSV.", "info")
            return redirect(url_for('reports.reports_users'))

        # Используем StringIO для текстовых данных
        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer, quoting=csv.QUOTE_MINIMAL)

        # Записываем заголовки
        headers = ['Пользователь', 'Количество посещений']
        csv_writer.writerow(headers)

        # Записываем данные
        for row in data:
            csv_writer.writerow(row)

        # Перемещаем данные в BytesIO
        output = BytesIO()
        output.write(csv_buffer.getvalue().encode('utf-8-sig'))  # Добавляем BOM для корректного отображения
        output.seek(0)


        # Отправляем файл
        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name="reports_users.csv"
        )

    except Exception as e:
        flash(f"Ошибка при формировании CSV: {e}", "error")
        return redirect(url_for('reports.reports_users'))