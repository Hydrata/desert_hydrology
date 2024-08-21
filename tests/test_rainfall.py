import os
try:
    from uae_hydrology.rainfall import process_rainfall
except ImportError:
    from uae_hydrology.uae_hydrology.rainfall import process_rainfall


def test_process_rainfall():
    output_filepath = process_rainfall()
    assert os.path.isfile(output_filepath)
