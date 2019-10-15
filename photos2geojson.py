# -*- coding: UTF-8 -*-


import os, sys
import exiftool
import json
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
    p = argparse.ArgumentParser(description='Move images to folder with his date')
    p.add_argument('path', help='Path to folder containing JPG files')
    return p.parse_args()
    
def _get_if_exist(data, key):
    if key in data:
        return data[key]
		
    return None
    
    
geojsonHeader='''    
{
"type": "FeatureCollection",
"crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
                                                                                
"features": [
'''
geojsonFooter='''
]
}
'''

if __name__ == '__main__':
    args = get_args()




    file_list = []
    for root, sub_folders, files in os.walk(args.path):
        for name in files:
            file_list += [os.path.join(root, name)  ]

    
    
    fs = open('photos.geojson','w')
    fs.write(geojsonHeader+"\n")
    fs.close()
    fs = open('photos.geojson','a')

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
                
                if _get_if_exist(record,'EXIF:GPSLatitude') and _get_if_exist(record,'EXIF:GPSLongitude'):
                    fs.write(exportString+"\n")
                
        
        index = index+IterationStep
        if index > total:
            index=total
        progress(index, len(file_list), status='Create geojson with photo locations, total = '+str(total))
        
    fs = open('photos.geojson','a')
    fs.write(geojsonFooter+"\n")
    fs.close()


        
        
    '''
        cmd = ['exiftool', filepath]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           stdin=subprocess.PIPE)
        out, err = p.communicate('-GPSLongitude')
        print out
    '''

    '''
        mt = mimetypes.guess_type(filepath)[0]
        if mt:
            f = open(filepath, 'rb')
            tags = exifread.process_file(f) 
            lat,lon = get_lat_lon(tags)
            
            #print filepath.ljust(50),str(lat).ljust(20), str(lon).ljust(20)
            exiftool E:\PHOTO\z_bat\geo\test1\IMG_20150228_231555.jpg"" -GPSLongitude -GPSLatitude --n  -json
            exiftool -stay_open True -@
            
    '''
        
     #python geo3.py "E:\PHOTO\z_bat\geo\test1"
