from fastapi import FastAPI
from pymongo import MongoClient
from enum import Enum
import time
import requests
from typing import List

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

    result = client[database][table].find(filter=filter)

    r:List = []
    for n in result:
        r.append(n)

    print('Rows in collection:',len(r))
    return str(r)

if __name__ == '__main__':
    client = MongoClient('mongodb://localhost:27017/')
    filter = {}
    result = client['3dobject']['objects'].find(filter=filter)
    print(result)
    r = []
    for n in result:
        r.append(n)
        print(r)