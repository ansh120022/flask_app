from flask import Flask, render_template, request, send_file
import os
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_autoindex import AutoIndex
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from flask_prometheus_metrics import register_metrics


UPLOAD_FOLDER = 'storage'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

files_index = AutoIndex(app, os.path.abspath(UPLOAD_FOLDER),
                        add_url_rules=False)


auth = HTTPBasicAuth()

users = {
    "John": generate_password_hash("hello"),
    "Susan": generate_password_hash("bye")
}

full_path = os.path.abspath(UPLOAD_FOLDER)


@app.route('/files', methods=['GET'])
def autoindex(path=full_path):
    if request.method == 'GET':
        return files_index.render_autoindex(path)


@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username


@app.route('/')
@auth.login_required
def index():
    return "Hello, %s!" % auth.current_user()


@app.route('/upload')
@auth.login_required
def show_upload_page():
    return render_template('upload.html')


@app.route('/uploader', methods=['GET', 'POST'])
@auth.login_required
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        with open(os.path.join(UPLOAD_FOLDER, f.filename), "wb") as fp:
            fp.write(request.data)
        return 'file uploaded successfully'


@app.route("/files/<path:path>")
@auth.login_required
def download_file(path):
    return send_file(os.path.join(full_path, path), as_attachment=True)


if __name__ == '__main__':
    register_metrics(app)
    dispatcher = DispatcherMiddleware(app.wsgi_app, {"/metrics": make_wsgi_app()})
    run_simple(hostname="0.0.0.0", port=5000, application=dispatcher)
    #app.run()
