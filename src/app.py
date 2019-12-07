from faiss_index.blueprint import blueprint as faiss_index_blueprint
from flask import Flask

app = Flask(__name__)
app.config.from_object('config')
app.register_blueprint(faiss_index_blueprint)

if __name__ == '__main__':
    app.run('0.0.0.0')
