import os
import sys
from flask import Flask
from app.routes import finance_routes
from app.auth_routes import auth_routes

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

app.register_blueprint(auth_routes)
app.register_blueprint(finance_routes)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    
if __name__ == "__main__":
    app.run(debug=True)

