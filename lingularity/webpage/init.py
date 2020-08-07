from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('front_page.html')


@app.route('/login')
def login():
    return render_template('login_page.html')


@app.route('/sign-up')
def sign_up():
    return render_template('login_page.html')


if __name__ == '__main__':
    app.run(debug=True)
