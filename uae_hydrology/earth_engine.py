import dotenv
import ee
import os


def initialize_earth_engine():
    dotenv.load_dotenv()
    service_account_key_path = os.getenv('EARTH_ENGINE_KEY_PATH')
    earth_engine_project_id = os.getenv('EARTH_ENGINE_PROJECT_ID')
    if service_account_key_path:
        credentials = ee.ServiceAccountCredentials(None, service_account_key_path)
        ee.Initialize(credentials, project=earth_engine_project_id)
    else:
        raise EnvironmentError('EARTH_ENGINE_KEY environment variable not set or invalid.')

def get_surface_water():
    initialize_earth_engine()
    print('get_surface_water code here')
