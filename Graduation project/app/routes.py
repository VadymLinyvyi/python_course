# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, PostForm, RegistrationForm, EditProfileForm, ResetPasswordRequestForm, ResetPasswordForm
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app.models import User, Post
from datetime import datetime
from app.email import send_password_reset_email
from flask_babel import _


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Зміни збережено'))
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Редагувати профіль'),
                           form=form)


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title=_('Автосервіс'))


@app.route('/about')
def about():
    return "pass"


@app.route('/service')
def service():
    return 'pass'


@app.route('/press')
def press():
    return 'pass'


@app.route('/history')
def history():
    return 'pass'


@app.route('/sos_program')
def sos_program():
    return 'pass'


@app.route('/vacancies')
def vacancies():
    return 'pass'


@app.route('/contacts')
def contacts():
    return 'pass'


@app.route('/reviews', methods=['GET', 'POST'])
@login_required
def reviews():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash(_('Дякуємо за Ваш відгук!'))
        return redirect(url_for('reviews'))
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('reviews', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('reviews', page=posts.prev_num) if posts.has_prev else None
    return render_template('reviews.html', title=_('Відгуки'), form=form, posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_("Невірне ім'я користувача або пароль"))
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title=_('Авторизація'), form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Вітаємо, тепер Ви зареєстрований користувач!'))
        return redirect(url_for('login'))
    return render_template('register.html', title=_('Реєстрація'), form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(_('Вам надіслано email з інструкціями щодо зміни пароля'))
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Пароль змінено.'))
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)