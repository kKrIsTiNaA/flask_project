from flask import Flask, render_template


app = Flask(__name__)


@app.route('/')
@app.route('/main')
def main():
    return render_template('main.html', title="Главная | PrettyLibrary")


@app.route('/private_area')
def private_area():
    return render_template('private_area.html', title="Личный кабинет | PrettyLibrary")


@app.route('/news')
def news():
    return render_template('news.html', title="Новости | PrettyLibrary")


@app.route('/search/')
def search():
    return render_template('search.html', title="Поиск | PrettyLibrary", search='string')


@app.route('/registration')
def registration():
    return render_template('registration.html', title="Регистрация | PrettyLibrary")


@app.route('/login')
def login():
    return render_template('login.html', title="Вход | PrettyLibrary")


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
