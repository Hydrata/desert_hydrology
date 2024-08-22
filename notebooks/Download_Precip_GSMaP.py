#!/usr/bin/env python
# coding: utf-8
import ee
import geemap
import os
ee.Initialize()

# geom = ee.Geometry.Polygon([[[43.8135,41.3969],
   # [45.7746,41.3969],
   # [45.7746,42.2686],
   # [43.8135,42.2686],
   # [43.8135,41.3969]]])

geom = ee.Geometry.BBox(-180, -80, 180, 80)
feature = ee.Feature(geom, {})
roi = feature.geometry()

Date_Start = ee.Date.fromYMD(2009,1,1)
Date_End = ee.Date.fromYMD(2024,12,31)

# Create list of dates for time series
n_days = Date_End.difference(Date_Start,'day').round()
dates = ee.List.sequence(0,n_days,1)

one_img=ee.Image(1)
masked_img = one_img.updateMask(one_img.eq(0))

def make_datelist(n):
    return Date_Start.advance(n, 'day')
    
dates = dates.map(make_datelist)

dataset = ee.ImageCollection("JAXA/GPM_L3/GSMaP/v8/operational").select('hourlyPrecipRateGC').sort("system:time_start",True)

def dailyCol(dt):
    start = ee.Date(dt)
    # start_tz = start.advance(-2, 'hours')
    end = start.advance(1, 'day')
    # end_tz = end.advance(-2, 'hours')
    start_str = ee.String(start.format('YYYY-MM-dd'))
    fname = ee.String(start_str).cat('_dailyPrecip')
    precImage = (dataset
                 .filterDate(start, end)
                 .select('hourlyPrecipRateGC')).sum().rename(fname)\
            .addBands(masked_img.rename(fname)).multiply(1)
            
    return precImage.select(fname).set({'system:time_start': ee.Date(dt).millis()})

JAXA_rainfall = ee.ImageCollection.fromImages(dates.map(dailyCol))


out_dir = os.path.join(os.path.expanduser('/home/aman/RF_data'), 'gsmap') 
print(JAXA_rainfall.aggregate_array('system:index').getInfo())
geemap.ee_export_image_collection(JAXA_rainfall, region=roi, scale=15000, out_dir=out_dir)

