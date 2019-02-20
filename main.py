from master import app, db, app
from config import config
from os import environ

if __name__ == "__main__":
    config_state = environ.get("VIZUALISER_ENV", "dev")
    app.config.update(config[config_state])
    app.app_context().push()
    db.create_all()
    db.session.commit()
    app.run(debug=True)

