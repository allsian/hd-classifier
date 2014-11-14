from flask import Flask
from flask import request
from flask import render_template
from flask import jsonify
import requests
import bs4
import random
import numpy as np
import pickle
import pandas as pd
import datetime
from bson import ObjectId
from pymongo import MongoClient
import pymongo
from flask.ext.restful import Resource, fields, reqparse

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/flag', methods = ['POST'])
def flag():
    mutually_exclusive_labels = ['bug','feature','uncategorized']
    flag = request.form['flag']
    event_id = request.form['id']
    a = coll.find({"_id": ObjectId(event_id)}).next()
    labels = a['labels']
    labels = [l for l in labels if l.lower() not in mutually_exclusive_labels]
    if flag.lower() in mutually_exclusive_labels:
      labels.append({'name': flag.lower()})
    a['labels']= labels
    b =  coll.update({"_id": a['_id']},a)
    return str(a)

@app.route('/data', methods = ['GET'])
def data():
    return jsonify(get_data())

def get_data():
    results = {'children': []}
    for entry in coll.find().sort([("created_at", pymongo.DESCENDING)]).limit(100):
        result = {'_id' : str(entry['_id']),
                  'title': entry['title'],
                  'guesses': entry['guesses'],
                  'url': '/get_ticket?raw=true&tid=' + str(entry['_id']),
                  'text': entry['title'] if entry['title'] else '' + entry['body'] if entry['body'] else '',
                  'created_at': entry['created_at'],
                  'priority': entry['severity']}
        results['children'].append(result)
    return results

@app.route('/get_ticket', methods = ['GET'])
def get_ticket():
    parser = reqparse.RequestParser()
    parser.add_argument('tid',type=str, help='please provide ticket ID (tid)')
    parser.add_argument('pure_json', type=bool)
    parser.add_argument('raw',type=bool)
    args = parser.parse_args()
    tid = args['tid']
    tickets = list(coll.find({'_id': ObjectId(tid)}))
    if args['raw']:
        return render_template('ticket_details.html', data=tickets)
    if args['pure_json']:
        return '\n'.join(str(t) for t in tickets)
    if len(tickets) < 1:
        return 'please specify a valid ticket ID'
    return render_template('show_ticket.html',data=tickets)


@app.context_processor
def utility_processor():
    def equals(a,b,c):
        if a == b:
            return c
    def has_label(i, labelName):
        for j in i['labels']:
            if labelName == j['name']:
                return True
    return dict(equals=equals,
                has_label=has_label)

if __name__ == '__main__':
    client = MongoClient('mongodb://localhost:27017/')
    db = client['hd-test']
    coll = db['salt']

    app.run(host='0.0.0.0', port=7000, debug=True)