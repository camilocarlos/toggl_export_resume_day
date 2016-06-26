#!/usr/bin/env python

from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS
from toggl_consumer import get_toggl_time_entries

app = Flask(__name__)
cors = CORS(app, resources={r"/toggl_api/*": {"origins": "*"}})

@app.route('/toggl_api/api/v1.0/time_entries', methods=['POST'])
def get_time_entries():
    api_token =  request.form['api_token']
    start = request.form['start']
    stop = request.form['stop']
    entries = get_toggl_time_entries(api_token, start, stop)
    return jsonify({'data': entries})

if __name__ == '__main__':
    app.run(debug=True)
