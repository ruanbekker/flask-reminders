from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from elasticsearch import Elasticsearch
import bcrypt
import datetime
import requests
import json
import time

def connect():
    connection = MongoClient('10.279.87.29', 27017)
    handle = connection["flask_reminders"]
    return handle

app = Flask(__name__)
app.config['ELASTICSEARCH_URL'] = 'http://10.270.87.193:9200/'
es =  Elasticsearch([app.config['ELASTICSEARCH_URL']])
handle = connect()

@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html')
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    users = handle.usersessions
    login_user = users.find_one({'name': request.form['username']})

    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password'].encode('utf-8')) == login_user['password'].encode('utf-8'):
            session['username'] = request.form['username']
            return redirect(url_for('index'))
    return render_template('redirect.html')

@app.route('/register', methods=['POST','GET'])
def register():
    if request.method == 'POST':
        users = handle.usersessions
        existing_user = users.find_one({'name': request.form['username']})
        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert({'name': request.form['username'], 'password': hashpass})
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        return 'Username Already Exists'

    return render_template('register.html')

@app.route('/list')
def get():
    cdata = handle.reminders.find().sort([("date", -1)])
    count = handle.reminders.find().count()
    return render_template('home.html', mydata=cdata, number=count)

@app.route('/search')
def lookup():
    return render_template('search.html')

@app.route('/search/results', methods=['GET', 'POST'])
def search_request():

    search_term = request.form["input"]
    res = es.search(index="flask_reminders", size=20, body={"query": {"multi_match" : { "query": search_term, "fields": ["description", "category", "type", "link"] }}})
    return render_template('results.html', res=res )

@app.route('/add')
def registration():
    return render_template('add.html', pagetitle='Add Item')

@app.route("/post", methods=['POST'])
def write():
    _date = datetime.datetime.now().strftime("%Y-%m-%d")
    _type = request.form.get("ftype")
    _category = request.form.get("fcategory")
    _description = request.form.get("fdescription")
    _link = request.form.get("flink")

# mongodb
    oid = handle.reminders.insert(
        {
        "date": str(_date),
        "type": _type,
        "category": _category,
        "description": _description,
        "link": _link,
        }
    )

# elasticsearch:
    esdata = json.dumps(
        {
        "date": str(_date),
        "type": _type,
        "category": _category,
        "description": _description,
        "link": _link,
        }
    )

    espost = es.index(index="flask_reminders", doc_type="bookmarks", body=esdata)

    return redirect ("/list")

if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run()
