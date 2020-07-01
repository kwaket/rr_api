import json
import time

from flask import Flask
from flask_restful import Resource, Api
import redis

from services import get_obj_data

app = Flask(__name__)
api = Api(app)


class EGRNService(Resource):
    def get(self, cadnum):
        return get_obj_data(r, cadnum)

api.add_resource(EGRNService, '/api/objects/<string:cadnum>')

if __name__ == '__main__':
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    p = r.pubsub()
    p.subscribe('tasks-channel')
    app.run(debug=True, host='0.0.0.0', port=6000)
