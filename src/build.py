#!/usr/bin/env python

# Include
import faiss
import numpy as np
import sys
import time

from argparse import ArgumentParser, RawTextHelpFormatter
from config import INDEX_DIR
from database import mongo_connect

# Basic IO
def parse_arguments():
    parser = ArgumentParser(description='a tool to build vector index based on Faiss.', formatter_class=RawTextHelpFormatter)

    parser.add_argument('-d', '--description', dest='description', required=True, help='index factory description:\nformat: xxx[,xxx][,xxx];\nexample: "PCA80,Flat", "OPQ16_64,IMI2x8,PQ8+16";\nrefer: https://github.com/facebookresearch/faiss/wiki/The-index-factory')
    parser.add_argument('-i', '--index', dest='index', required=True, help='index name: same as your mongo collection name.')
    parser.add_argument('-m', '--metric', dest='metric', choices=['ip', 'l2'], default='ip', help="distance metric, default: ip [inner product].")
    #parser.add_argument('-t', '--train', dest='train', help="if your don't need train all data, please input your train file location:\nfile format: .csv;\nline format: key,d1,d2,d3,...,dN.")

    return parser.parse_args()

def get_col(ix):
    db = mongo_connect()
    col_list = db.list_collection_names()

    if ix in col_list:
        return db[ix]
    else:
        raise Exception('please create collection firstly.')

def dump_vector(col):
    ids = []
    vecs = []

    cursor = col.find({}, {'_id': 0, 'id': 1, 'vec': 1})
    for cur in cursor:
        ids.append(cur['id'])
        vecs.append(cur['vec'])
    
    ids = np.ascontiguousarray(ids)
    vecs = np.ascontiguousarray(vecs, dtype=np.float32)

    return ids, vecs

# Build Index
def build_index(args):
    col = get_col(args.index)
    ids, xb = dump_vector(col)

    print('# Your index factory description:\n  %s\n' % args.description)

    dim = xb.shape[-1]
    if args.metric == 'ip':
        index = faiss.index_factory(dim, args.description, faiss.METRIC_INNER_PRODUCT)
    elif args.metric == 'l2':
        index = faiss.index_factory(dim, args.description, faiss.METRIC_L2)
    else:
        raise Exception('not supported metric: %s.' % args.metric)
    index = faiss.IndexIDMap(index)
   
    print('# Begin training index.')
    tbeg_train = time.time()

    index.train(xb)

    tend_train = time.time()
    print('# Finish training index.\n# Time cost %.3fs.\n' % (tend_train - tbeg_train))

    assert index.is_trained

    print('# Begin adding vector.')
    tbeg_add = time.time()

    index.add_with_ids(xb, ids)

    tend_add = time.time()
    print('# Total %s vectors.' % len(ids))
    print('# Finish adding vector.\n# Time cost %.3fs.\n' % (tend_add - tbeg_add))

    return index

def main():
    args = parse_arguments()

    index = build_index(args)

    fname = '%s/%s.index' % (INDEX_DIR, args.index)
    faiss.write_index(index, fname)
    print('# Finish writing index.\n# Location: %s' % fname)
    
if __name__ == '__main__':
    main()
