import os
import pytest
import dotenv


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "skip_earth_engine_conditional: skip test if earth engine configuration no found"
    )


def pytest_collection_modifyitems(config, items):
    dotenv.load_dotenv()
    if not os.getenv('EARTH_ENGINE_KEY_PATH'):
        skip_earth_engine_conditional = pytest.mark.skip(reason="Skipped because EARTH_ENGINE_KEY_PATH not found")
        for item in items:
            if "skip_earth_engine_conditional" in item.keywords:
                item.add_marker(skip_earth_engine_conditional)