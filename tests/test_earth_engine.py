import pytest
import os

try:
    from uae_hydrology.earth_engine import get_surface_water, get_rainfall
except ImportError:
    from uae_hydrology.uae_hydrology.earth_engine import get_surface_water, get_rainfall


@pytest.mark.skip_earth_engine_conditional
def test_get_surface_water():
    collection_path = 'LANDSAT/LC09/C02/T1_L2'
    small_test = [24.62415, 55.68418, 24.657, 55.74139, "2024-04-16", "small_test"]
    for parameters in [small_test]:
        latitude_1, longitude_1, latitude_2, longitude_2, search_date, label = parameters
        polygon = [[
            [longitude_1, latitude_1],
            [longitude_1, latitude_2],
            [longitude_2, latitude_2],
            [longitude_2, latitude_1],
            [longitude_1, latitude_1],
        ]]
        get_surface_water(polygon, collection_path, search_date, label)


@pytest.mark.skip_earth_engine_conditional
@pytest.mark.skip
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
    output_directory = get_rainfall(start_date, end_date, polygon)
    assert len(os.listdir(output_directory)) == 97
