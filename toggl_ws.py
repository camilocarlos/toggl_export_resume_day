#!/usr/bin/env python

from flask import Flask
from flask import jsonify
from flask import request
from toggl_consume import get_toggl_time_entries

app = Flask(__name__)

entries = [
    {
        'start' : '1',
        'stop' : '2',
        'duration' : '3'
    }
]

@app.route('/toggl_api/api/v1.0/time_entries', methods=['POST'])
def get_time_entries():
    api_token =  request.form['api_token']
    start = request.form['start']
    stop = request.form['stop']
    get_toggl_time_entries(api_token, start, stop)
    return jsonify({'time_entries': entries})

if __name__ == '__main__':
    app.run(debug=True)
