from flask import Flask
from routes.auth_routes import auth_bp
from routes.category_routes import category_bp
from routes.task_routes import task_bp

app = Flask(__name__)
app.secret_key = 'cle_secrete'

# 🔗 Enregistrer les routes
app.register_blueprint(auth_bp)
app.register_blueprint(category_bp)
app.register_blueprint(task_bp)

# 🔧 Format date utilisable dans les templates
from datetime import datetime

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d/%m/%Y à %H:%M'):
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return value
    return value.strftime(format)

if __name__ == '__main__':
    app.run(debug=True)
