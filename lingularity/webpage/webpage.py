from typing import *

from flask import Flask, render_template, request

from lingularity.database import MongoDBClient

app = Flask(__name__)
mongo_client = MongoDBClient(user=None, language=None, credentials=MongoDBClient.Credentials.default())


@app.route('/')
def index():
    return render_template('front-page.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    global mongo_client
    html_file_path = 'login-page.html'

    if request.method == 'GET':
        return render_template(html_file_path)
    else:
        user, password = map(request.form.get, ['usr', 'pwd'])
        if user in mongo_client.user_names:
            mongo_client.set_user(user)
            if mongo_client.query_password() == password:
                # TODO
                pass
            else:
                return render_template(html_file_path, error_code=2)
        else:
            return render_template(html_file_path, error_code=1)

        return render_template(html_file_path)


@app.route('/sign-up', methods=['POST', 'GET'])
def sign_up():
    global mongo_client
    html_file_path = 'sign-up-page.html'

    if request.method == 'GET':
        return render_template(html_file_path)
    else:
        error_code: Optional[int] = None
        mailadress, username, password = map(request.form.get, ['email', 'usr', 'pwd'])

        if '@' not in mailadress or mailadress.strip().__len__() < 3:
            error_code = 1
        elif mailadress in mongo_client.mail_addresses:
            # TODO
            error_code = 2
        elif not len(username.strip()):
            error_code = 3
        elif len(password) < 5:
            error_code = 4

        if error_code is not None:
            return render_template(html_file_path, error_code=error_code)
        else:
            mongo_client.initialize_user(mailadress, username, password)
            return render_template(html_file_path)


if __name__ == '__main__':
    app.run(debug=True)
