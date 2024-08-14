import os
from uae_hydrology.rainfall import process_rainfall


def test_process_rainfall():
    output_filepath = process_rainfall()
    assert os.path.isfile(output_filepath)
