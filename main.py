from flask import Flask
from flask import render_template, url_for, redirect
from flask import request, session
from flask_pymongo import PyMongo
from hashlib import md5
from os import getenv
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret_key'

    mongo_uri = 'mongodb+srv://{u}:{p}@{h}/{d}'.format(
        u=getenv('MONGO_USER'),
        p=getenv('MONGO_PASS'),
        h=getenv('MONGO_HOST'),
        d=getenv('MONGO_DATABASE'))
    print(mongo_uri)
    app.config['MONGO_URI'] = mongo_uri
    mongo = PyMongo(app)

    @app.route('/')
    def index():
        goals = mongo.db.Goals.find({
            'user': session.get('user'),
            'hash': session.get('hash')
        })

        short_term = []
        long_term = []
        for goal in goals:
            item = {'content': goal['content'],
                    'date': goal['deadline'],
                    'complete': goal['complete'],
                    'comp_url': url_for('complete', Goal=goal['_id']),
                    'incomp_url': url_for('incomplete', Goal=goal['_id']),
                    'del_url': url_for('delete', Goal=goal['_id'])
                    }

            if goal['term'] == 'short':
                short_term.append(item)
            else:
                long_term.append(item)

        return render_template('index.html',
                               s_items=short_term,
                               l_items=long_term,
                               add_url=url_for('add'),
                               login_url=url_for('login'),
                               logout_url=url_for('logout'),
                               username=session.get('user'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        session['user'] = request.form['username']
        raw_pass = request.form['password']
        session['hash'] = md5(bytes(raw_pass, 'utf-8')).hexdigest()
        return redirect(url_for('index'))

    @app.route('/logout', methods=['GET', 'POST'])
    def logout():
        session['user'] = None
        session['hash'] = None
        return redirect(url_for('index'))

    @app.route('/add', methods=['POST'])
    def add():
        mongo.db.Goals.insert_one({
            'deadline': request.form['deadline'],
            'content': request.form['content'],
            'term': request.form['term'],
            'complete': False,
            'user': session.get('user'),
            'hash': session.get('hash')
        })
        return redirect(url_for('index'))

    @app.route('/delete/<ObjectId:Goal>')
    def delete(goal):
        mongo.db.Goals.delete_one({
            '_id': goal,
            'user': session.get('user'),
            'hash': session.get('hash')})
        return redirect(url_for('index'))

    @app.route('/complete/<ObjectId:Goal>')
    def complete(goal):
        mongo.db.Goals.update_one({
            '_id': goal,
            'user': session.get('user'),
            'hash': session.get('hash')},
            {'$set': {'complete': True}})

        return redirect(url_for('index'))

    @app.route('/incomplete/<ObjectId:Goal>')
    def incomplete(goal):
        mongo.db.Goals.update_one({
            '_id': goal,
            'user': session.get('user'),
            'hash': session.get('hash')},
            {'$set': {'complete': False}})

        return redirect(url_for('index'))

    return app


app = create_app()
app.run('0.0.0.0')