import json
import time

import redis
from flask import Flask, render_template
# from flask_cors import CORS

from services import get_obj_data


app = Flask(__name__)
# CORS(app)



@app.route('/')
def main():
    return render_template('main.html')


@app.route('/objects/<string:cadnum>')
def get_obj(cadnum):
    # return {'cadnum': cadnum}
    return get_obj_data(r, cadnum)


if __name__ == '__main__':
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    p = r.pubsub()
    p.subscribe('tasks-channel')
    app.run(debug=True, host='0.0.0.0', port=5000)
