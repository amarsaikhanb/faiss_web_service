import json
import sys

from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError

def mongo_connect():
    # custom your mongodb connect

    URL = 'mongodb://%s:%s@%s:%s' % (USER, PASS, HOST, PORT)

    client = MongoClient(URL, connect=False)

    return client[DB]

def insert_bulk(col, docs):
    try:
        ret = col.insert_many(docs)
    except BulkWriteError:
        print('WARNING: BulkWriteError found, insert change to upsert.')
        ret = update_bulk(col, docs)

    return ret

def update_bulk(col, docs):
    requests = [UpdateOne({'key': doc['key']}, {'$set': {'id': doc['id'], 'vec': doc['vec']}}, upsert=True) for doc in docs]
    results = col.bulk_write(requests)

    return results

def get_max_id(col):
    max_id = -1

    cursor = col.find({}, {'id': 1}).sort('id', -1).limit(1)
    for cur in cursor:
        max_id = cur['id']

    return max_id

def docs_add_id(col, docs):
    doc_id = get_max_id(col)

    for doc in docs:
        doc_id += 1
        doc['id'] = doc_id

    return docs

if __name__ == '__main__':
    pass
