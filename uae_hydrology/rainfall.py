import shutil
from pathlib import Path

# grass needs the session imported before the script library
from grass_session import Session
import grass.script as gs


def process_rainfall():
    # Setup directories
    database_directory = Path.cwd() / 'database'
    output_data_directory = Path.cwd() / 'output_data' / 'rainfall'
    database_directory.mkdir(exist_ok=True)
    output_data_directory.mkdir(parents=True, exist_ok=True)

    # Cleanup old files if they exist
    for directory in [database_directory, output_data_directory]:
        if directory.exists():
            for item in directory.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

    with Session(
        gisdb=database_directory.as_posix(),
        location="uae",
        mapset="PERMANENT",
        create_opts="EPSG:4326"
    ) as session:
        # Import the data to the GRASS database
        boundary_shapefile_path = Path.cwd() / 'input_data' / 'gadm41_ARE_0.shp'
        rainguage_shapefile_path = Path.cwd() / 'input_data' / 'ncm_stations.shp'
        gs.run_command('g.region', flags='s', save='uae_region')
        gs.run_command('v.in.ogr', input=boundary_shapefile_path.as_posix(), output='uae_boundary')
        gs.run_command('v.in.ogr', input=rainguage_shapefile_path.as_posix(), output='ncm_stations')

        # Create a raster to hold our interpolated data, and mask it to the uae_boundary
        gs.run_command('g.region', vect='uae_boundary', res=0.01)
        gs.run_command('r.mask', vect='uae_boundary')

        # run the rainfall interpolation using Inverse Distance Weighted
        gs.run_command('v.surf.idw', input='ncm_stations', column='RF_april_1', output='cumulative_rainfall_interpolated_idw')

        # Write the raster to a geotiff
        output_tif_path = output_data_directory / 'cumulative_rainfall_interpolated_idw.tif'
        gs.run_command('r.out.gdal', input='cumulative_rainfall_interpolated_idw', output=output_tif_path.as_posix(), overwrite=True)
        return output_tif_path.as_posix()
