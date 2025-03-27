from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc, select
from models import db, Course, Category, User, Review
from tools import CoursesFilter, ImageSaver

bp = Blueprint('courses', __name__, url_prefix='/courses')
COURSE_PARAMS = ['author_id', 'name', 'category_id', 'short_desc', 'full_desc']

def params():
    return {p: request.form.get(p) or None for p in COURSE_PARAMS}

def search_params():
    return {
        'name': request.args.get('name'),
        'category_ids': [x for x in request.args.getlist('category_ids') if x],
    }

@bp.route('/')
def index():
    courses = CoursesFilter(**search_params()).perform()
    pagination = db.paginate(courses)
    courses = pagination.items
    categories = db.session.execute(select(Category)).scalars()
    return render_template('courses/index.html', courses=courses, categories=categories, pagination=pagination, search_params=search_params())

@bp.route('/new')
@login_required
def new():
    course = Course()
    categories = db.session.execute(select(Category)).scalars()
    users = db.session.execute(select(User)).scalars()
    return render_template('courses/new.html', categories=categories, users=users, course=course)

@bp.route('/create', methods=['POST'])
@login_required
def create():
    f = request.files.get('background_img')
    img = None
    course = Course()
    try:
        if f and f.filename:
            img = ImageSaver(f).save()

        image_id = img.id if img else None
        course = Course(**params(), background_image_id=image_id)
        db.session.add(course)
        db.session.commit()
    except IntegrityError as err:
        flash(f'Ошибка при записи данных в БД: {err}', 'danger')
        db.session.rollback()
        categories = db.session.execute(select(Category)).scalars()
        users = db.session.execute(select(User)).scalars()
        return render_template('courses/new.html', categories=categories, users=users, course=course)

    flash(f'Курс {course.name} успешно добавлен!', 'success')
    return redirect(url_for('courses.index'))

@bp.route('/<int:course_id>')
def show(course_id):
    course = db.get_or_404(Course, course_id)
    existing_review = db.session.execute(
        select(Review).filter_by(course_id=course_id, user_id=current_user.id)
    ).scalar_one_or_none() if current_user.is_authenticated else None
    return render_template('courses/show.html', course=course, existing_review=existing_review)

@bp.route('/<int:course_id>/reviews', methods=['GET', 'POST'])
def reviews(course_id):
    course = db.get_or_404(Course, course_id)

    sort_by = request.args.get('sort_by', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 5

    if sort_by == 'positive':
        reviews_query = select(Review).filter_by(course_id=course_id).order_by(desc(Review.rating), desc(Review.created_at))
    elif sort_by == 'negative':
        reviews_query = select(Review).filter_by(course_id=course_id).order_by(Review.rating, desc(Review.created_at))
    else:
        reviews_query = select(Review).filter_by(course_id=course_id).order_by(desc(Review.created_at))

    pagination = db.paginate(reviews_query, page=page, per_page=per_page)

    existing_review = db.session.execute(
        select(Review).filter_by(course_id=course_id, user_id=current_user.id)
    ).scalar_one_or_none() if current_user.is_authenticated else None

    return render_template('courses/reviews.html', course=course, pagination=pagination, sort_by=sort_by, existing_review=existing_review)

@bp.route('/<int:course_id>/reviews/create', methods=['POST'])
@login_required
def create_review(course_id):
    course = db.get_or_404(Course, course_id)

    existing_review = db.session.execute(
        select(Review).filter_by(course_id=course_id, user_id=current_user.id)
    ).scalar_one_or_none()

    if existing_review:
        flash('Вы уже оставили отзыв к этому курсу.', 'warning')
        return redirect(url_for('courses.reviews', course_id=course_id))

    rating = int(request.form.get('rating'))
    text = request.form.get('text')

    if not (0 <= rating <= 5):
        flash('Некорректная оценка.', 'danger')
        return redirect(url_for('courses.reviews', course_id=course_id))

    if not text:
        flash('Введите текст отзыва.', 'danger')
        return redirect(url_for('courses.reviews', course_id=course_id))

    review = Review(rating=rating, text=text, course_id=course_id, user_id=current_user.id)
    db.session.add(review)

    course.rating_sum += rating
    course.rating_num += 1
    db.session.commit()

    flash('Ваш отзыв успешно добавлен!', 'success')
    return redirect(url_for('courses.reviews', course_id=course_id))