from master import app, db, app
from config import config

if __name__ == "__main__":
    app.config.update(config)
    app.app_context().push()
    db.create_all()
    db.session.commit()
    app.run(debug=True)

