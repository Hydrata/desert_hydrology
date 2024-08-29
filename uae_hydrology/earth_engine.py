import dotenv
import ee
import os
import geemap
import pathlib
import shutil


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


def get_surface_water():
    initialize_earth_engine()
    print("get_surface_water code here")


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