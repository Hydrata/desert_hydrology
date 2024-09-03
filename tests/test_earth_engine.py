import pytest
import os
try:
    from uae_hydrology.earth_engine import get_surface_water, get_rainfall
except ImportError:
    from uae_hydrology.uae_hydrology.earth_engine import get_surface_water, get_rainfall


@pytest.mark.skip_earth_engine_conditional
def test_get_surface_water():
    country_name = 'United Arab Emirates'
    collection_path = 'LANDSAT/LC09/C02/T1_L2'
    start_date = "2024-04-16"
    end_date = "2024-04-20"
    result_placeholder = get_surface_water(country_name, collection_path, start_date, end_date)


@pytest.mark.skip_earth_engine_conditional
def test_get_rainfall():
    start_date = '2024-04-15'
    end_date = '2024-04-19'
    polygon = [[
        [52.83, 22.76],
        [57.04, 22.76],
        [57.04, 26.97],
        [52.83, 26.97],
        [52.83, 22.76]
    ]]
    ouput_directory = get_rainfall(start_date, end_date, polygon)
    assert len(os.listdir(ouput_directory)) == 97
