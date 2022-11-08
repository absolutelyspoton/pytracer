from fastapi import FastAPI
from pymongo import MongoClient
from enum import Enum

app = FastAPI()

DEV_MONGODB_ADDRESS = 'mongodb://localhost:27017/'

class PingTypes(str, Enum):
    ws = "webserver"
    db = "database"
    g = "google"

@app.get('/ping/{pingtype}')
async def ping(pingtype:PingTypes):

    if pingtype == PingTypes.db:
        print('db ping')
    else:
        print(pingtype)

    return



@app.get('/db/{database}/{table}/{id}')
async def get_data(database:str,table:str,id:int):
    client = MongoClient(DEV_MONGODB_ADDRESS)
    if id == 0:
        filter = {}
    else:
        filter = {'id':id}

    result = client[database][table].find(filter=filter)
    r = []
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