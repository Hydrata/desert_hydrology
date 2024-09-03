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


def get_surface_water(country_name, collection_path, start_date, end_date):
    initialize_earth_engine()
    landsat_map = geemap.Map()
    boundaries = ee.FeatureCollection("FAO/GAUL/2015/level0")
    boundaries_level1 = ee.FeatureCollection("FAO/GAUL/2015/level1")
    landsat_map.addLayer(boundaries, {}, "Country Boundaries")
    # https://developers.google.com/earth-engine/datasets/catalog/FAO_GAUL_2015_level0
    country = boundaries.filter(f"ADM0_NAME == '{country_name}'")
    landsat_map.addLayer(country, {}, country_name)
    landsat_map.center_object(country)

    collection_1 = (
        ee.ImageCollection(collection_path)
        .filterDate(start_date, end_date)
        .filterBounds(country)
        .filterMetadata("CLOUD_COVER", "less_than", 25)
        .filter(ee.Filter.eq("WRS_PATH", 160))
        .filter(ee.Filter.eq("WRS_ROW", 43))
        .sort("CLOUD_COVER")
    )

    def apply_scale_factors(image):
        optical_bands = image.select("SR_B.").multiply(0.0000275).add(-0.2)
        thermal_bands = image.select("ST_B.*").multiply(0.00341802).add(149.0)
        return image.addBands(optical_bands, None, True).addBands(thermal_bands, None, True)

    def customRemap(image, lowerLimit, upperLimit, newValue):
        mask = image.gte(lowerLimit).And(image.lt(upperLimit))
        return image.where(mask, newValue)

    collection_1 = collection_1.map(apply_scale_factors)

    image_map = geemap.Map()
    image = collection_1.first()

    # Compute the Normalized Difference Vegetation Index (NDVI).
    nir = image.select("SR_B5")
    red = image.select("SR_B4")
    green = image.select("SR_B3")
    ndvi = nir.subtract(red).divide(nir.add(red)).rename("NDVI")
    ndwi = green.subtract(nir).divide(green.add(nir)).rename("NDWI")
    ndvi_params = {"min": -1, "max": 1, "palette": ["blue", "white", "green"]}

    vis_param = {"min": 0, "max": 0.3, "bands": ["SR_B4", "SR_B3", "SR_B2"], "gamma": 1.5}
    ndwi_clipped = ndwi.clip(country)

    image_map.addLayer(image, vis_param, "First mage")
    image_map.addLayer(ndwi_clipped, ndviParams, "NDWI image")
    image_map.centerObject(image, 8)

    floodmask = ndwi_clipped.select("NDWI").gt(0.2)
    image_map.addLayer(floodmask, {"palette": ["blue", "lightgreen"]}, "Flood mask")
    floodMasked = ndwi_clipped.updateMask(floodmask)
    image_map.addLayer(floodMasked, {"palette": ["blue"]}, "Flood masked")
    flood_remaped = customRemap(floodMasked, 0, 2, 1)
    image_map.addLayer(flood_remaped, {"palette": ["red"]}, "Flood remapped 19 April")

    geemap.ee_export_image_to_drive(
        # floodMasked, filename='floodMasked_19April2024.tif', scale=30, file_per_band=True
        flood_remaped,
        description="Dubai flood inundation 19 April",
        folder="share",
        fileNamePrefix="flood_dubai_19April",
        scale=30,
    )

    #
    # collection2 = (
    #     ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
    #     .filterDate("2023-04-08", "2023-04-11")
    #     .filterBounds(country)
    #     .filterMetadata("CLOUD_COVER", "less_than", 25)
    #     .filter(ee.Filter.eq("WRS_PATH", 160))
    #     .filter(ee.Filter.eq("WRS_ROW", 43))
    #     .sort("CLOUD_COVER")
    # )
    #
    # print(collection2.size().getInfo())
    #
    # collection2 = collection2.map(apply_scale_factors)
    #
    # ap = geemap.Map()
    # image = collection2.first()
    #
    # # Compute the Normalized Difference Vegetation Index (NDVI).
    # nir = image.select("SR_B5")
    # red = image.select("SR_B4")
    # green = image.select("SR_B3")
    # ndvi = nir.subtract(red).divide(nir.add(red)).rename("NDVI")
    # ndwi = green.subtract(nir).divide(green.add(nir)).rename("NDWI")
    # ndviParams = {"min": -1, "max": 1, "palette": ["blue", "white", "green"]}
    #
    # vis_param = {"min": 0, "max": 0.3, "bands": ["SR_B4", "SR_B3", "SR_B2"], "gamma": 1.5}
    # ndvi_clipped = ndwi.clip(country)
    #
    # Map.addLayer(image, vis_param, "First mage")
    # Map.addLayer(ndvi_clipped, ndviParams, "NDVI image")
    # Map.centerObject(image, 8)
    #
    # floodmask = ndvi_clipped.select("NDWI").gt(0.2)
    # Map.addLayer(floodmask, {"palette": ["blue", "lightgreen"]}, "Flood mask")
    # floodMasked = ndvi_clipped.updateMask(floodmask)
    # Map.addLayer(floodMasked, {"palette": ["blue"]}, "Flood masked")
    # flood_remaped = customRemap(floodMasked, 0, 2, 1)
    # Map.addLayer(flood_remaped, {"palette": ["red"]}, "Before Flood remapped")
    #
    # geemap.ee_export_image_to_drive(
    #     # floodMasked, filename='floodMasked_19April2024.tif', scale=30, file_per_band=True
    #     flood_remaped,
    #     description="Dubai water surface",
    #     folder="share",
    #     fileNamePrefix="Dubai_Before_flood",
    #     scale=30,
    # )


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