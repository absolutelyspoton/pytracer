# Author: Dominic Williams
# Date created: 
# 
# Service Layer - Generic API Access Layer to MongoDB

from fastapi import FastAPI
from pymongo import MongoClient
from enum import Enum
import time
import requests
from typing import List
import credentials
import logging

from bson.json_util import dumps, loads
from fastapi.responses import PlainTextResponse

app = FastAPI()

DEV_MONGODB_ADDRESS = 'mongodb://localhost:27017/'
DEV_MONGODB_ADDRESS = 'mongodb+srv://{}:{}@cluster0.iyzootc.mongodb.net/test'
GOOGLE_ADDRESS = 'http://www.google.com'

class PingTypes(str, Enum):
    ws = "webserver"
    db = "database"
    g = "google"

@app.get('/ping/{pingtype}',response_class=PlainTextResponse)
async def ping(pingtype:PingTypes):

    t:float = time.perf_counter()

    connection_string =DEV_MONGODB_ADDRESS.format(credentials.MONGODB_ADMIN_USERNAME,credentials.MONGODB_ADMIN_PASSWORD)

    if pingtype == PingTypes.db:
        client = MongoClient(connection_string)
        client.close()
    elif pingtype == PingTypes.ws:
        pass
    elif pingtype == PingTypes.g:
        r = requests.get(GOOGLE_ADDRESS)
        print(r.text)
    else:
        print(pingtype)

    t2 = time.perf_counter() - t
    t3 = str(t2)
    t4 = 'my_metric{label="a"}' + ' ' + t3 + "\n"
    print(t4)
    return t4

@app.get('/db/{database}/{table}/{id}')
async def get_data(database:str,table:str,id:int):

    connection_string =DEV_MONGODB_ADDRESS.format(credentials.MONGODB_ADMIN_USERNAME,credentials.MONGODB_ADMIN_PASSWORD)
    client = MongoClient(connection_string)
    if id == 0:
        filter = {}
    else:
        filter = {'id':id}

    projection = {'id':0,'_id':0}
    result = client[database][table].find(filter=filter,projection=projection)

    # Return as json object / coding hack to force type
    d = dumps(result)
    l = loads(d)
    
    print('Rows in collection:',len(l))
    return (l)

if __name__ == '__main__':
    connection_string =DEV_MONGODB_ADDRESS.format(credentials.MONGODB_ADMIN_USERNAME,credentials.MONGODB_ADMIN_PASSWORD)
    client = MongoClient(connection_string)
    filter = {'id':1}

    projection = {'id':0,'_id':0}
    result = client['3dObjects']['vertices'].find(filter=filter,projection=projection)

    j = dumps(result)
    print(j)

    p = loads(j)
    print(p)

    for i in p:
        print(i)