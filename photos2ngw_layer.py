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


    URL = 'http://example.nextgis.com'
    AUTH = ('administrator', 'admin')
    GRPNAME = "photos"

    import requests
    from json import dumps
    from datetime import datetime


    # Пока удаление ресурсов не работает, добавим дату и время к имени группы
    GRPNAME = datetime.now().isoformat() + " " + GRPNAME

    s = requests.Session()


    def req(method, url, json=None, **kwargs):
        """ Простейшая обертка над библиотекой requests c выводом отправляемых
        запросов в stdout. К работе NextGISWeb это имеет малое отношение. """

        jsonuc = None

        if json:
            kwargs['data'] = dumps(json)
            jsonuc = dumps(json, ensure_ascii=False)

        req = requests.Request(method, url, auth=AUTH, **kwargs)
        preq = req.prepare()

        print ""
        print ">>> %s %s" % (method, url)

        if jsonuc:
            print ">>> %s" % jsonuc

        resp = s.send(preq)

        print resp.status_code
        assert resp.status_code / 100 == 2

        jsonresp = resp.json()

        for line in dumps(jsonresp, ensure_ascii=False, indent=4).split("\n"):
            print "<<< %s" % line

        return jsonresp

    # Обертки по именам HTTP запросов, по одной на каждый тип запроса

    def get(url, **kwargs): return req('GET', url, **kwargs)            # NOQA
    def post(url, **kwargs): return req('POST', url, **kwargs)          # NOQA
    def put(url, **kwargs): return req('PUT', url, **kwargs)            # NOQA
    def delete(url, **kwargs): return req('DELETE', url, **kwargs)      # NOQA

    # Собственно работа с REST API

    iturl = lambda (id): '%s/api/resource/%d' % (URL, id)
    courl = lambda: '%s/api/resource/' % URL

    # Создаем группу ресурсов внутри основной группы ресурсов, в которой будут
    # производится все дальнешние манипуляции.
    grp = post(courl(), json=dict(
        resource=dict(
            cls='resource_group',   # Идентификатор типа ресурса
            parent=dict(id=0),      # Создаем ресурс в основной группе ресурсов
            display_name=GRPNAME,   # Наименование (или имя) создаваемого ресурса
        )
    ))

    # Поскольку все дальнейшие манипуляции будут внутри созданной группы,
    # поместим ее ID в отдельную переменную.
    grpid = grp['id']
    grpref = dict(id=grpid)


    # Метод POST возвращает только ID созданного ресурса, посмотрим все данные
    # только что созданной подгруппы.
    get(iturl(grpid))


    # Проходим по файлам, ищем geojson

    filename = 'photos.geojson'    
    print "uploading "+filename
            
            # Теперь создадим векторный слой из geojson-файла. Для начала нужно загрузить
            # исходный ZIP-архив, поскольку передача файла внутри REST API - что-то
            # странное. Для загрузки файлов предусмотрено отдельное API, которое понимает
            # как обычную загрузку из HTML-формы, так загрузку методом PUT. Последнее
            # несколько короче.
    with open(filename, 'rb') as fd:
        shpzip = put(URL + '/api/component/file_upload/upload', data=fd)


        srs = dict(id=3857)


        vectlyr = post(courl(), json=dict(
                resource=dict(cls='vector_layer', parent=grpref, display_name=os.path.splitext(filename)[0]),
                vector_layer=dict(srs=srs, source=shpzip)
            ))

        #Создание стиля
        vectstyle = post(courl(), json=dict(
                resource=dict(cls='mapserver_style', parent=vectlyr, display_name=os.path.splitext(filename)[0]),
                mapserver_style=dict(xml='''<map><symbol><type>ellipse</type><name>circle</name><points>1 1</points> 
  <filled>true</filled>  </symbol><layer><class><style><symbol>circle</symbol><color red="255" green="0" blue="189"/><outlinecolor red="255" green="0" blue="0"/></style></class></layer></map>''')
            ))



            
