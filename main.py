from string import ascii_letters

from flask import Flask, render_template, redirect, request, abort, make_response, jsonify
from flask_login import LoginManager, login_user, login_required, \
    logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField, StringField, \
    SelectMultipleField, widgets, TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired

import books_api
from data import db_session, users, books

CHOICES = [('Детские', 'Детские'),
           ('Классика', "Классика"),
           ('Поэзия', "Поэзия"),
           ('Приключения', "Приключения"),
           ('Психология', 'Психология'),
           ('Романтика', 'Романтика'),
           ('Ужасы', 'Ужасы'),
           ('Фантастика', 'Фантастика')]

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////db/books.sqlite'
WHOOSH_BASE = '/db/books.sqlite'

login_manager = LoginManager()
login_manager.init_app(app)


@app.errorhandler(404)
def not_found():
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(500)
def cant_process():
    return make_response(jsonify({'error': 'Server error'}), 404)


class SymbolError(Exception):
    error = 'Пароль может содержать только латинские буквы, цифры ' \
            'и дефис ("-").'


class NumeralError(Exception):
    error = 'Пароль должен содержать хотя бы одну цифру.'


class LetterError(Exception):
    error = 'В пароле должна быть по крайней мере одна латинская буква.'


class LengthError(Exception):
    error = 'Длина пароля должна быть не менее 8 символов.'


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


def more_7(field):
    if len(field.data) < 8:
        field.errors = [LengthError.error]


def has_lat(field):
    if not any(map(lambda x: x in ascii_letters, list(field.data))):
        field.errors = [LetterError.error]


def has_num(field):
    if not any(map(lambda x: x.isdigit(), list(field.data))):
        field.errors = [NumeralError.error]


def allowed_data(field):
    if not all(map(lambda x: x.isdigit() or x in ascii_letters or x == '-', list(field.data))):
        field.errors = [SymbolError.error]


class RegisterForm(FlaskForm):
    email = StringField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired(),
                                                   more_7, has_lat, has_num,
                                                   allowed_data])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    categories = MultiCheckboxField(u"Какие жанры книг вы предпочитаете?",
                                    choices=CHOICES)
    submit = SubmitField('Зарегистрироваться')


class BooksForm(FlaskForm):
    name = StringField("Название", validators=[DataRequired()])
    author = StringField('Автор', validators=[DataRequired()])
    categories = StringField('Категория', validators=[DataRequired()])
    content = TextAreaField("Содержание", validators=[DataRequired()])
    submit = SubmitField('Применить')


@app.route('/')
@app.route('/books')
def show_books():
    db_session.global_init('db/books.sqlite')
    session = db_session.create_session()
    if current_user.is_authenticated:
        all_books = session.query(books.Books).filter(
            (books.Books.who_added == 1) |
            (books.Books.who_added == current_user.id))
        return render_template("books.html", books=all_books,
                               user=current_user, title='Главная | PrettyLibrary')
    else:
        all_books = session.query(books.Books).filter(books.Books.who_added == 1)
        return render_template("books.html", books=all_books,
                               user=current_user, title='Главная | PrettyLibrary')


@app.route('/private_area')
def private_area():
    return render_template('private_area.html', title="Личный кабинет | PrettyLibrary")


@app.route('/books/<int:book_id>', methods=['GET', 'POST'])
def get_one_book(book_id):
    db_session.global_init('db/books.sqlite')
    session = db_session.create_session()
    book = session.query(books.Books).get(book_id)
    if not book:
        abort(404)
    return render_template('show_book.html', book=book,
                           title=f'Читать {book.name} | PrettyLibrary')


@app.route('/books/new/', methods=['GET', 'POST'])
@login_required
def new_book():
    form = BooksForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        book = books.Books()
        book.who_added = current_user.id
        book.name = form.name.data
        book.author = form.author.data
        book.categories = form.categories.data
        book.content = form.content.data
        current_user.books.append(book)
        session.merge(current_user)
        session.commit()
        return redirect('/')
    return render_template('new_book.html', title='Добавление книги | PrettyLibrary',
                           form=form)


@app.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_books(book_id):
    form = BooksForm()
    if request.method == "GET":
        session = db_session.create_session()
        all_books = session.query(books.Books).filter(
            books.Books.id == book_id,
            books.Books.users == current_user).first()
        if all_books:
            form.name.data = all_books.name
            form.author.data = all_books.author
            form.content.data = all_books.content
            form.categories.data = all_books.categories
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        all_books = session.query(books.Books).filter(
            books.Books.id == book_id,
            books.Books.users == current_user).first()
        if all_books:
            all_books.name = form.name.data
            all_books.author = form.author.data
            all_books.categories = form.categories.data
            all_books.content = form.content.data
            session.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('edit_book.html', title='Редактирование книги | PrettyLibrary',
                           form=form)


@app.route('/books/delete/<int:book_id>', methods=['GET', 'POST'])
@login_required
def delete_book(book_id):
    session = db_session.create_session()
    book = session.query(books.Books).filter(
        books.Books.id == book_id,
        books.Books.who_added == current_user.id).first()
    if book:
        return render_template('delete_book.html', book=book)
    else:
        abort(404)
    return redirect('/')


@app.route('/books/delete_2/<int:book_id>')
@login_required
def one_more_delete(book_id):
    session = db_session.create_session()
    book = session.query(books.Books).filter(
        books.Books.id == book_id,
        books.Books.who_added == current_user.id).first()
    session.delete(book)
    session.commit()
    all_books = session.query(books.Books).filter(
        books.Books.who_added == 1)
    return render_template('books.html', books=all_books,
                           title='Все книги | PrettyLibrary')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html',
                                   title='Регистрация | PrettyLibrary',
                                   form=form,
                                   message="Пароли не совпадают")
        sessions = db_session.create_session()
        if sessions.query(users.User).filter(
                users.User.email == form.email.data).first():
            return render_template('register.html',
                                   title='Регистрация | PrettyLibrary',
                                   form=form,
                                   message="Такой пользователь уже есть")
        categories = ', '.join(x for x in form.categories.data)
        user = users.User(name=form.name.data,
                          email=form.email.data,
                          categories=categories)
        user.set_password(form.password.data)
        sessions.add(user)
        sessions.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация | PrettyLibrary', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(users.User).filter(
            users.User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация | PrettyLibrary', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/login")


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(users.User).get(user_id)


def main():
    db_session.global_init("db/books.sqlite")
    app.register_blueprint(books_api.blueprint)
    app.run()


if __name__ == '__main__':
    main()
