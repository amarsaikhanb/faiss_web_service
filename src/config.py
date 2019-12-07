import os

from database import mongo_connect

# in product env
DEBUG = False

# init path
WORK_DIR = os.path.dirname(os.path.realpath(__file__))
INDEX_DIR = '%s/index' % WORK_DIR

# init index
INDEX = list(map(lambda x: '.'.join(x.split('.')[:-1]), os.listdir(INDEX_DIR)))

# config mongodb
MONGODB = mongo_connect()
