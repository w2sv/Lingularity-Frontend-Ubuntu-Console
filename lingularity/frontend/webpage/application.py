from typing import *

from flask import Flask, render_template, request

from lingularity.backend.database import MongoDBClient
from lingularity.frontend.console.utils.signup_credential_validation import invalid_password, invalid_mailadress, invalid_username


app = Flask(__name__)
mongo_client = MongoDBClient()


@app.route('/')
def index():
    return render_template('front-page.html')


@app.route('/authenticate', methods=['POST', 'GET'])
def login():
    global mongo_client
    html_file_path = 'login-page.html'

    if request.method == 'GET':
        return render_template(html_file_path)
    else:
        user, password = map(request.form.get, ['usr', 'pwd'])
        if user in mongo_client.usernames:
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

        if invalid_mailadress(mailadress):
            error_code = 1
        elif mailadress in mongo_client.mail_addresses:
            # TODO
            error_code = 2
        elif invalid_username(username):
            error_code = 3
        elif invalid_password(password):
            error_code = 4

        if error_code is not None:
            return render_template(html_file_path, error_code=error_code)
        else:
            mongo_client.initialize_user(mailadress, password)
            return render_template(html_file_path)


if __name__ == '__main__':
    app.run(debug=True)
