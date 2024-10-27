import dotenv
import ee
import os
import geemap
import pathlib
import shutil
import rasterio
from datetime import datetime


def initialize_earth_engine():
    dotenv.load_dotenv()
    service_account_key_path = os.getenv("EARTH_ENGINE_KEY_PATH")
    earth_engine_project_id = os.getenv("EARTH_ENGINE_PROJECT_ID")
    if service_account_key_path:
        credentials = ee.ServiceAccountCredentials(None, service_account_key_path)
        ee.Initialize(credentials, project=earth_engine_project_id)
    else:
        raise EnvironmentError(
            "EARTH_ENGINE_KEY environment variable not set or invalid."
        )

def get_mosaic_dates(collection):
    image_list = collection.toList(collection.size())
    dates = []
    for i in range(image_list.size().getInfo()):
        image = ee.Image(image_list.get(i))
        timestamp = image.get('system:time_start').getInfo()
        date = datetime.utcfromtimestamp(timestamp / 1000.0).strftime('%Y-%m-%d')
        dates.append(date)
    return dates


def process_image(image_to_process, tag_to_process, label_to_process, date_string, output_data_directory, region_of_interest=None):
    optical_bands = image_to_process.select("SR_B.").multiply(0.0000275).add(-0.2)
    thermal_bands = image_to_process.select("ST_B.*").multiply(0.00341802).add(149.0)
    image_to_process = image_to_process.addBands(optical_bands, None, True).addBands(thermal_bands, None, True)
    timestamp = image_to_process.get('system:time_start').getInfo()
    nir_image = image_to_process.select("SR_B5")
    green_image = image_to_process.select("SR_B3")
    ndwi_image = green_image.subtract(nir_image).divide(green_image.add(nir_image)).rename("NDWI")
    flood_mask_image = ndwi_image.select("NDWI").gt(0.2)
    flood_masked_image = ndwi_image.updateMask(flood_mask_image)

    base_image_output_filepath = str(output_data_directory / f"{date_string}_{label_to_process}_{tag_to_process}_base_image.tif")
    flood_masked_image_output_filepath = str(output_data_directory / f"{date_string}_{label_to_process}_{tag_to_process}_flood_masked_image.tif")

    for image, image_filepath in [
        (image_to_process, base_image_output_filepath,),
        (flood_masked_image, flood_masked_image_output_filepath,),
    ]:
        geemap.ee_export_image(
            image,
            scale=30,
            region=region_of_interest,
            file_per_band=False,
            filename=image_filepath
        )
    return flood_masked_image_output_filepath


def get_surface_water(polygon, collection_path, search_date, label):
    initialize_earth_engine()
    geom = ee.Geometry.Polygon(polygon)
    feature = ee.Feature(geom, {})
    region_of_interest = feature.geometry()
    output_data_directory = pathlib.Path.cwd() / 'output_data' / 'surface_water' / label
    output_data_directory.mkdir(parents=True, exist_ok=True)
    date_format = "%Y-%m-%d"
    datetime_obj = datetime.strptime(search_date, date_format)

    dry_image_collection = (
        ee.ImageCollection(collection_path)
        .filterDate("1900-01-01", datetime_obj)
        .filterBounds(region_of_interest)
        .filterMetadata("CLOUD_COVER", "less_than", 25)
        .sort('system:time_start', False)
    )

    dry_image_dates = get_mosaic_dates(dry_image_collection)
    print(f"{dry_image_dates=}")
    dry_date = dry_image_dates[0]
    dry_image = dry_image_collection.mosaic()

    wet_image_collection = (
        ee.ImageCollection(collection_path)
        .filterDate(datetime_obj, "2100-01-01")
        .filterMetadata("CLOUD_COVER", "less_than", 25)
        .filterBounds(region_of_interest)
        .sort('system:time_start', True)
    )

    wet_image_dates = get_mosaic_dates(dry_image_collection)
    print(f"{wet_image_dates=}")
    wet_date = wet_image_dates[-1]
    wet_image = wet_image_collection.mosaic()

    count_result = f"Found {dry_date} dry and {wet_date} wet image."
    print(count_result)
    if not dry_image or not wet_image:
        print('Missing Images.')
        raise "Missing images." + count_result

    dry_flood_image_filepath = process_image(dry_image, 'dry', label, dry_date, output_data_directory, region_of_interest)
    wet_flood_image_filepath = process_image(wet_image, 'wet', label, wet_date, output_data_directory, region_of_interest)
    difference_threshold = 0.015

    with rasterio.open(dry_flood_image_filepath, 'r+') as dry_flood:
        dry_flood_tif = dry_flood.read(1)
        nodata_value = dry_flood.nodata if dry_flood.nodata is not None else -9999
        dry_flood_tif[dry_flood_tif == 0] = nodata_value
        dry_flood.nodata = nodata_value
        dry_flood.write(dry_flood_tif, 1)

    with rasterio.open(wet_flood_image_filepath, 'r+') as wet_flood:
        wet_flood_tif = wet_flood.read(1)
        nodata_value = wet_flood.nodata if wet_flood.nodata is not None else -9999
        wet_flood_tif[wet_flood_tif == 0] = nodata_value
        wet_flood.nodata = nodata_value
        wet_flood.write(wet_flood_tif, 1)

    if dry_flood_tif.shape != wet_flood_tif.shape:
        raise ValueError("The input rasters do not have the same dimensions")
    difference = wet_flood_tif - dry_flood_tif
    with rasterio.open(dry_flood_image_filepath) as src:
        metadata = src.meta
    metadata.update(dtype=rasterio.float32, nodata=nodata_value)
    flood_difference_filepath = wet_flood_image_filepath.replace('wet', 'difference')
    with rasterio.open(flood_difference_filepath, 'w', **metadata) as dst:
        difference[difference < difference_threshold] = nodata_value
        dst.write(difference.astype(rasterio.float32), 1)



def get_rainfall(start_date_string, end_date_string, polygon):
    output_data_directory = pathlib.Path.cwd() / 'output_data' / 'gsmap'
    output_data_directory.mkdir(exist_ok=True)

    for item in output_data_directory.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    initialize_earth_engine()
    geom = ee.Geometry.Polygon(polygon)
    feature = ee.Feature(geom, {})
    region_of_interest = feature.geometry()

    start_date = ee.Date(start_date_string)
    end_date = ee.Date(end_date_string)

    number_of_hours = end_date.difference(start_date, "hour").round()
    image_times = ee.List.sequence(0, number_of_hours, 1)

    blank_image = ee.Image(1)
    masked_image = blank_image.updateMask(blank_image.eq(0))

    def make_hourly_time_stamp_list(n):
        return start_date.advance(n, "hour")

    image_times = image_times.map(make_hourly_time_stamp_list)

    gsmap_dataset = (
        ee.ImageCollection("JAXA/GPM_L3/GSMaP/v8/operational")
        .select("hourlyPrecipRateGC")
        .sort("system:time_start", True)
    )

    def get_hourly_image(date_time):
        start = ee.Date(date_time)
        end = start.advance(1, "hour")
        start_str = ee.String(start.format("YYYY-MM-dd-HH"))
        image_file_name = ee.String(start_str).cat("_hourlyPrecip")
        precipitation_image = (
            (gsmap_dataset.filterDate(start, end).select("hourlyPrecipRateGC"))
            .sum()
            .rename(image_file_name)
            .addBands(masked_image.rename(image_file_name))
            .multiply(1)
        )
        return precipitation_image.select(image_file_name).set({"system:time_start": ee.Date(date_time).millis()})

    jaxa_rainfall_collection = ee.ImageCollection.fromImages(image_times.map(get_hourly_image))

    def export_image(earth_image):
        img_date = ee.Date(earth_image.get("system:time_start")).format("YYYY-MM-dd-HH").getInfo()
        filename = f"precip_{img_date}.tif".replace("-", "_")
        geemap.ee_export_image(
            earth_image,
            filename=f"{output_data_directory}/{filename}",
            scale=15000,
            region=region_of_interest,
            file_per_band=False
        )

    image_list = jaxa_rainfall_collection.toList(jaxa_rainfall_collection.size())
    for i in range(image_list.size().getInfo()):
        img = ee.Image(image_list.get(i))
        export_image(img)
    return (output_data_directory)