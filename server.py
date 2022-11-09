from fastapi import FastAPI
from pymongo import MongoClient
from enum import Enum
import time
import requests
from typing import List

from bson.json_util import dumps, loads

app = FastAPI()

DEV_MONGODB_ADDRESS = 'mongodb://localhost:27017/'
GOOGLE_ADDRESS = 'http://www.google.com'

class PingTypes(str, Enum):
    ws = "webserver"
    db = "database"
    g = "google"

@app.get('/ping/{pingtype}')
async def ping(pingtype:PingTypes) -> float:

    t:float = time.perf_counter()

    if pingtype == PingTypes.db:
        client = MongoClient(DEV_MONGODB_ADDRESS)
        client.close()
    elif pingtype == PingTypes.ws:
        pass
    elif pingtype == PingTypes.g:
        r = requests.get(GOOGLE_ADDRESS)
        print(r.text)
    else:
        print(pingtype)

    return (time.perf_counter() - t)

@app.get('/db/{database}/{table}/{id}')
async def get_data(database:str,table:str,id:int):
    client = MongoClient(DEV_MONGODB_ADDRESS)
    if id == 0:
        filter = {}
    else:
        filter = {'id':id}

    projection = {'id':0,'_id':0}
    result = client[database][table].find(filter=filter,projection=projection)

    d = dumps(result)
    l = loads(d)

    print('Rows in collection:',len(l))
    return (l)

if __name__ == '__main__':
    client = MongoClient('mongodb://localhost:27017/')
    filter = {'id':1}
    # projection = {}
    projection = {'id':0,'_id':0}
    result = client['3dobject']['vertices'].find(filter=filter,projection=projection)

    j = dumps(result)
    print(j)

    p = loads(j)
    print(p)

    for i in p:
        print(i)

    pass