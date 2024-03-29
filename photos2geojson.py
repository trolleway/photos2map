# -*- coding: UTF-8 -*-


import os, sys
import exiftool
import json
from geojson import Feature, Point, FeatureCollection, dump 
from fractions import Fraction




def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()  # As suggested by Rom Ruben (see: http://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console/27871113#comment50529068_27871113)


def get_args():
    import argparse
    p = argparse.ArgumentParser(description='Generate geojson file with location of photos in folder')
    p.add_argument('path', help='Path to folder containing JPG files')
    p.add_argument('--o', help='path to geojson', type=str, default='photos.geojson')
    return p.parse_args()
    
def _get_if_exist(data, key):
    if key in data:
        return data[key]
		
    return None
    
    
geojsonHeader='''    
{"type": "FeatureCollection","crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },  "features": [
'''
geojsonFooter='''
]}
'''

if __name__ == '__main__':
    args = get_args()
    
    geojson_path = args.o


    file_list = []
    for root, sub_folders, files in os.walk(args.path):
        for name in files:
            file_list += [os.path.join(root, name)  ]

    
    geojson_features = []

    index = 0
    IterationStep = 200
    total = len(file_list)
    while index < total:
        
        with exiftool.ExifTool() as et:
            metadata = et.get_tags_batch(['EXIF:GPSLongitude','EXIF:GPSLatitude','DateTimeOriginal'],file_list[index:index+IterationStep])
            for record in metadata:
                dict = json.dumps(record)
                #print dict
                geojsonString='{ "type": "Feature", "properties": { "filename": "%(SourceFile)s", "datetime": "%(EXIF:DateTimeOriginal)s" }, "geometry": { "type": "Point", "coordinates": [ %(EXIF:GPSLongitude)s, %(EXIF:GPSLatitude)s ] } }, '
                exportString = geojsonString % {"SourceFile" : record['SourceFile'],'EXIF:DateTimeOriginal' : _get_if_exist(record,'EXIF:DateTimeOriginal'),"EXIF:GPSLatitude" : _get_if_exist(record,'EXIF:GPSLatitude'),"EXIF:GPSLongitude" : _get_if_exist(record,'EXIF:GPSLongitude')}
                new_point = Point((_get_if_exist(record,'EXIF:GPSLongitude'), _get_if_exist(record,'EXIF:GPSLatitude')))
                
                
                if _get_if_exist(record,'EXIF:GPSLatitude') and _get_if_exist(record,'EXIF:GPSLongitude'):

                    geojson_features.append(Feature(geometry=new_point, properties={'filename': record['SourceFile'],'datetime': _get_if_exist(record,'EXIF:DateTimeOriginal')}) )
                
        
        index = index+IterationStep
        if index > total:
            index=total
        progress(index, len(file_list), status='Create geojson with photo locations, total = '+str(total))
    
    feature_collection = FeatureCollection(geojson_features)
    with open(geojson_path, 'w') as f:
        dump(feature_collection, f)



       