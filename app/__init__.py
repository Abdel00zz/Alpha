import os
from flask import Flask
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

def create_app(test_config=None):
    app = Flask(__name__)
    CORS(app)
    csrf = CSRFProtect(app)

    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
            UPLOAD_FOLDER=os.path.join(app.root_path, 'uploads'),
            GENERATED_FOLDER=os.path.join(app.root_path, 'generated'),
            MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max file size
        )
    else:
        app.config.update(test_config)

    # Créer les dossiers nécessaires
    for folder in [app.config['UPLOAD_FOLDER'], app.config['GENERATED_FOLDER']]:
        os.makedirs(folder, exist_ok=True)

    # Enregistrer le blueprint
    from . import routes
    app.register_blueprint(routes.bp)

    return app
