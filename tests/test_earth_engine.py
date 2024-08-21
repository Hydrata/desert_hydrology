import pytest
try:
    from uae_hydrology.earth_engine import get_surface_water
except ImportError:
    from uae_hydrology.uae_hydrology.earth_engine import get_surface_water


@pytest.mark.skip_earth_engine_conditional
def test_get_surface_water():
    result_placeholder = get_surface_water()
