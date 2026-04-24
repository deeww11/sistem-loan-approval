from flask import Flask
from controllers.auth_controller import auth
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

app.register_blueprint(auth)

if __name__ == '__main__':
    app.run(debug=True)