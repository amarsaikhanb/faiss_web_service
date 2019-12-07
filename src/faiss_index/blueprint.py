from flask import Blueprint, jsonify, request
from jsonschema import validate, ValidationError
from werkzeug.exceptions import BadRequest

from .faiss_index import FaissIndex

blueprint = Blueprint('faiss_index', __name__)

schema = {
        'type': 'object',
        'required': ['k', 'keys'],
        'properties': {
            'k': {'type': 'integer', 'minimum': 0},
            'keys': {'type': 'array', 'items': {'type': 'string'}},
            'vecs': {'type': 'array', 'items': {'type': 'array', 'items': {'type': 'number'}}},
            'metric': {'type': 'string', 'enum': ['ip', 'l2']}
        }
    }

@blueprint.record_once
def record(setup_state):
    conf = setup_state.app.config
    blueprint.faiss_index = FaissIndex(conf)

@blueprint.route('/search/<string:ix>/', methods=['GET', 'POST'])
def search(ix):
    try:
        if ix in blueprint.faiss_index.indexes:
            index = blueprint.faiss_index.indexes[ix]
        else:
            raise BadRequest('No index named: %s.' % ix)

        if request.method == 'POST':
            req = request.get_json(force=True)
        elif request.method == 'GET':
            req = {}
            req['k'] = request.args.get('k', default=0, type=int)
            req['keys'] = request.args.get('keys', default='', type=str).split(';')
            req['metric'] = request.args.get('metric', default='ip', type=str)

        validate(req, schema)

        k = req.get('k')
        keys = req.get('keys')
        vecs = req.get('vecs')
        metric = req.get('metric', 'ip')

        if vecs:
            results = index.search_by_vecs(keys, vecs, k)
        else:
            results = index.search_by_keys(keys, k)

        results = index.re_rank(results, metric)

        return jsonify(results)

    except (BadRequest, ValidationError) as e:
        return jsonify('Bad Request: %s' % str(e)), 400
    except Exception as e:
        return jsonify('Server Error: %s' % str(e)), 500

@blueprint.route('/add/<string:ix>/', methods=['POST'])
def add(ix):
    try:
        if ix in blueprint.faiss_index.indexes:
            index = blueprint.faiss_index.indexes[ix]
        else:
            raise BadRequest('No index named: %s.' % ix)

        if index.is_adding:
            raise BadRequest('Other process is adding, please waiting')
        else:
            index.is_adding = True

            schema = {
                'type': 'object',
                'required': ['keys', 'vecs'],
                'properties': {
                    'keys': {'type': 'array', 'items': {'type': 'string'}},
                    'vecs': {'type': 'array', 'items': {'type': 'array', 'items': {'type': 'number'}}}
                }
            }

            req = request.get_json(force=True)
            validate(req, schema)

            keys = req.get('keys')
            vecs = req.get('vecs')

            if len(keys) == len(vecs):
                results = index.add(keys, vecs)
            else:
                raise BadRequest('keys & vecs not agreement, %s' % req)

            index.is_adding = False
            return jsonify('add index [%s] successfully.' % ix)

    except (BadRequest, ValidationError) as e:
        index.is_adding = False
        return jsonify('Bad Request: %s' % str(e)), 400
    except Exception as e:
        index.is_adding = False
        return jsonify('Server Error: %s' % str(e)), 500

@blueprint.route('/update/<string:ix>/', methods=['GET'])
def update(ix):
    try:
        blueprint.faiss_index.update(ix)
        return jsonify('update index [%s] successfully.' % ix)

    except Exception as e:
        return jsonify('Server Error: %s' % str(e)), 500

@blueprint.route('/delete/<string:ix>/', methods=['GET'])
def delete(ix):
    try:
        if ix in blueprint.faiss_index.indexes:
            index = blueprint.faiss_index.indexes[ix]
        else:
            raise BadRequest('No index named: %s.' % ix)

        blueprint.faiss_index.delete(ix)
        return jsonify('delete index [%s] successfully.' % ix)

    except (BadRequest, ValidationError) as e:
        return jsonify('Bad Request: %s' % str(e)), 400
    except Exception as e:
        return jsonify('Server Error: %s' % str(e)), 500

@blueprint.route('/ping', methods=['GET'])
def ping():
    ixs = list(blueprint.faiss_index.indexes.keys())

    return jsonify(ixs)
