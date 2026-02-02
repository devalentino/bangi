from flask import Flask
from flask_cors import CORS
from flask_smorest import Api

from src.auth.routes import blueprint as auth_blueprint
from src.core.exceptions import ApplicationError
from src.core.logging import configure_logging
from src.core.routes import blueprint as core_blueprint
from src.facebook_pacs.routes import blueprint as facebook_pacs_blueprint
from src.health.routes import blueprint as health_blueprint
from src.reports.routes import blueprint as reports_blueprint
from src.tracker.routes import blueprint as track_blueprint
from src.tracker.routes import process_blueprint

configure_logging()

app = Flask(__name__)
CORS(app)

app.config['API_TITLE'] = 'Tracker API'
app.config['API_VERSION'] = 'v2'
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
app.config['OPENAPI_VERSION'] = '3.0.2'
app.config['OPENAPI_URL_PREFIX'] = '/openapi'
app.config['OPENAPI_SWAGGER_UI_PATH'] = '/swagger-ui'
app.config['OPENAPI_SWAGGER_UI_URL'] = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'

api = Api(app)
api.register_blueprint(auth_blueprint, url_prefix='/api/v2/auth')
api.register_blueprint(core_blueprint, url_prefix='/api/v2/core')
api.register_blueprint(facebook_pacs_blueprint, url_prefix='/api/v2/facebook/pacs')
api.register_blueprint(reports_blueprint, url_prefix='/api/v2/reports')
api.register_blueprint(track_blueprint, url_prefix='/api/v2/track')
api.register_blueprint(process_blueprint, url_prefix='/process')
api.register_blueprint(health_blueprint, url_prefix='/api/v2/health')


@app.errorhandler(ApplicationError)
def handle_exception(e):
    return {'message': e.message}, e.http_status_code
