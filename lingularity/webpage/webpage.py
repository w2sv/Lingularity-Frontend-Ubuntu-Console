from flask import Flask, render_template, request

from lingularity.database import MongoDBClient

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('front_page.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    html_link = 'login_page.html'
    mongo_client = MongoDBClient(user=None, language=None, credentials=MongoDBClient.Credentials.default())

    if request.method == 'GET':
        return render_template(html_link)
    else:
        user, password = map(request.form.get, ['usr', 'pwd'])
        if user in mongo_client.user_names:
            mongo_client.set_user(user)
            if mongo_client.query_password() == password:
                # TODO
                print('Successfully logged in')
                pass
            else:
                return render_template(html_link, error_code=2)
        else:
            return render_template(html_link, error_code=1)

        return render_template('sign_up_page.html')


@app.route('/sign-up')
def sign_up():
    return render_template('sign_up_page.html')


if __name__ == '__main__':
    app.run(debug=True)
