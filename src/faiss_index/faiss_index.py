import faiss
import numpy as np

from database import docs_add_id, insert_bulk 

class Index(object):
    def __init__(self, ix, conf):
        self.col = conf['MONGODB'][ix]
        self.fname = '%s/%s.index' % (conf['INDEX_DIR'], ix)
        self.index = faiss.read_index(self.fname)

        self.is_adding = False

    def query_keys(self, keys):
        ret = list(self.col.find({'key': {'$in': keys}}, {'key': 1, 'vec': 1}))

        d = dict()
        for r in ret:
            d[r['key']] = r['vec']

        return d

    def search_by_keys(self, ks, k):
        d = self.query_keys(ks)
        keys = list(d.keys())
        vecs = list(d.values())

        results = self.__search__(keys, vecs, k)

        return results

    def search_by_vecs(self, keys, vecs, k):
        results = self.__search__(keys, vecs, k)

        return results

    def add(self, keys, vecs):
        doc = []
        for i in range(len(keys)):
            doc.append({'key': keys[i], 'vec': vecs[i]})

        docs = docs_add_id(self.col, doc)
        insert_bulk(self.col, docs)

        ids = list(map(lambda x: x['id'], docs))
        ids = np.ascontiguousarray(ids)
        xb = np.ascontiguousarray(vecs, dtype=np.float32)

        self.index.add_with_ids(xb, ids)
        faiss.write_index(self.index, self.fname)

    def calc_sim(self, metric, v1, v2):
        if metric == 'ip':
            dis = np.dot(v1, v2)
        elif metric == 'l2':
            dis = np.linalg.norm(v1-v2)

        return dis

    def re_rank(self, results, metric):
        for result in results:
            v1 = result['vec']
            neighbors = result['neighbors']
            for neighbor in neighbors:
                neighbor['similarity'] = self.calc_sim(metric, v1, neighbor['vec'])
            sorted_neighbors = sorted(neighbors, key=lambda x: x['similarity'], reverse=True)
            result['neighbors'] = sorted_neighbors

        return results

    def __search__(self, keys, vecs, k):
        xq = np.ascontiguousarray(vecs, np.float32)

        results = []
        if xq.size and k > 0:
            D, I = self.index.search(xq, k)
            ids = list(map(lambda x: int(x), np.unique(I.flatten())))
            id_2_key, id_2_vec = self.__id_to_key__(ids)

            for key, vec, i in zip(keys, vecs, I):
                neighbors = [i_ for i_ in i if i_ in id_2_key]
                neighbors = [self.__knn_dict__(id_2_key, id_2_vec, i_) for i_ in neighbors]

                results.append(self.__result_dict__(key, vec, neighbors))
        else:
            for key, vec in zip(keys, vecs):
                results.append(self.__result_dict__(key, vec, []))

        return results

    def __id_to_key__(self, ids):
        ret = list(self.col.find({'id': {'$in': ids}}, {'id': 1, 'key': 1, 'vec': 1}))

        keys = dict()
        vecs = dict()

        for r in ret:
            keys[r['id']] = r['key']
            vecs[r['id']] = r['vec']

        return keys, vecs

    def __knn_dict__(self, keys, vecs, i):
        return {'neighbor': keys[i], 'vec': vecs[i]}

    def __result_dict__(self, key, vec, ns):
        return {'key': key, 'vec': vec, 'neighbors': ns}

class FaissIndex(object):
    def __init__(self, conf):
        self.conf = conf
        self.indexes = self.init_indexes()
        
    def init_indexes(self):
        indexes = {}

        for ix in self.conf['INDEX']:
            indexes[ix] = Index(ix, self.conf)

        return indexes

    def update(self, ix):
        self.indexes[ix] = Index(ix, self.conf)

    def delete(self, ix):
        self.indexes.pop(ix, None)
