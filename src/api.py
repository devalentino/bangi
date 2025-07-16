from flask import Flask
from flask_smorest import Api

from src.health.routes import blueprint as health_blueprint
from src.tracker.routes import blueprint as track_blueprint

app = Flask(__name__)
app.config['API_TITLE'] = 'Tracker API'
app.config['API_VERSION'] = 'v2'
app.config['OPENAPI_VERSION'] = '3.0.2'
app.config['OPENAPI_URL_PREFIX'] = '/'
app.config['OPENAPI_SWAGGER_UI_PATH'] = '/swagger-ui'
app.config['OPENAPI_SWAGGER_UI_URL'] = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'

api = Api(app)
api.register_blueprint(track_blueprint, url_prefix='/api/v2/track')
api.register_blueprint(health_blueprint, url_prefix='/api/v2/health')
