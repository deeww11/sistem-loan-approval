from flask import Flask
from controllers.auth_controller import auth
from config import Config
from controllers.form_controller import form_bp

app = Flask(__name__)
app.config.from_object(Config)

app.register_blueprint(auth)
app.register_blueprint(form_bp, url_prefix='/form')


if __name__ == '__main__':
    app.run(debug=True)