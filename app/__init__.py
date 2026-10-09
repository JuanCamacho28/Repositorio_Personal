import os

from flask import Flask

from app import db as db_module


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-santaclara")
    app.config["DATABASE"] = os.environ.get(
        "DATABASE", os.path.join(app.instance_path, "santaclara.db")
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)
    db_module.init_app(app)
    with app.app_context():
        db_module.init_db()

    from app.routes.auth import auth_bp
    from app.routes.contacto import contacto_bp
    from app.routes.formulario import formulario_bp
    from app.routes.inicio import inicio_bp
    from app.routes.nosotros import nosotros_bp
    from app.routes.productos import productos_bp

    app.register_blueprint(inicio_bp)
    app.register_blueprint(nosotros_bp)
    app.register_blueprint(productos_bp)
    app.register_blueprint(contacto_bp)
    app.register_blueprint(formulario_bp)
    app.register_blueprint(auth_bp)

    @app.get("/sitemap.xml")
    def sitemap():
        return app.send_static_file("sitemap.xml"), 200, {
            "Content-Type": "application/xml"
        }

    return app
