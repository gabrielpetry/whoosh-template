# -*- coding: utf-8 -*-
# Imports
from flask import Flask, render_template, request, jsonify
import os
import pymysql

from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
from whoosh.analysis import StemmingAnalyzer
from whoosh import index, spelling, query, qparser, scoring
from whoosh.qparser import QueryParser,MultifieldParser

from flask_cors import CORS

# Contants
DB_HOST = ""
DB_NAME = ""
DB_USER = DB_NAME
DB_PASS = ""
DB_CHARSET = "utf8"

INDEX_NAME = "myIndex"

# Flask App configuration
app = Flask(__name__)
CORS(app)
app.config['DEBUG'] = True


@app.route('/')
def home():
    return render_template('index.html')


@app.route("/search")
def search():
    """ Required arguments in the get url
        term, the term to the search, which alsa can be a user query
        correct, if the user want the query to be corrected
        limit, how many entries to recover
        example request:
            /search?term=http%20error&limit=10&correct=false
    """
    # Validade if termm is in the request
    try:
        term = request.args['term']
        if (len(term) < 2):
            return jsonify({
                "status": 500,
                "err": "Type a full search, please"})
    except:
        return jsonify(
            status=500,
            err="Searching for nothing, returns nothing")

    # Scoring method, TD_IDF is slight faster, but not as acurated
    # SCORE_METHOD = scoring.TF_IDF()
    # BM25F is the most acurated
    # as long as my test went, this is the best config
    SCORE_METHOD = scoring.BM25F(B=0.75, K1=1.2)
    ix = index.open_dir(INDEX_NAME)
    sh = ix.searcher(weighting=SCORE_METHOD)
    # Here we configure the field that should be searched
    queryy = MultifieldParser(['title', 'content'], ix.schema)
    limitt = int(request.args['limit'])
    qparser = queryy.parse(term)
    # Deals with the correction, we check if the correction makes sense and
    # then correct the entry, probably not the best solution, but permits
    # that non corrected queries return as fast as possible
    if request.args['correct'] == 'true':
        corrected = sh.correct_query(qparser, term)
        if corrected.query != qparser:
            result = sh.search(corrected.query, limit=limitt)
            corrected = corrected.string
            was_corrected = True
        else:
            result = sh.search(qparser, limit=limitt)
            was_corrected = False
            corrected = False
    else:
        result = sh.search(qparser, limit=limitt)
        was_corrected = False
        corrected = False

    runtime = result.__dict__["runtime"]
    # print(result.__dict__)
    representation = result.__dict__["q"]

    # Parse the results to a friendly key value for vue.js
    lista_posts = []
    for i in result:
        lista_posts.append({
         "title": i['title'],
         "permalink": i['permalink'],
         "author": i['author'],
        })

    # Return a jsonify list of posts, runtime and the correction info
    return jsonify({
                    "runtime": runtime,
                    "representation": str(representation),
                    "was_corrected": was_corrected,
                    "corrected": corrected,
                    "posts": lista_posts})


@app.route('/createindex')
def createindex():
    # Connect to a database
    connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME,
            charset=DB_CHARSET,
            cursorclass=pymysql.cursors.DictCursor)

    # This is a sample schema for indexing and storing some useful info
    schema = Schema(
        id=ID(unique=True, stored=True),
        title=TEXT(stored=True, analyzer=StemmingAnalyzer()),
        content=TEXT(stored=True, analyzer=StemmingAnalyzer()),
        author=TEXT(stored=True),
        permalink=TEXT(stored=True))

    # If the index folder exists we will update
    if os.path.isdir(INDEX_NAME):
        ix = index.open_dir(INDEX_NAME)
    # Else we create a new index
    else:
        os.makedirs(INDEX_NAME)
        ix = index.create_in(INDEX_NAME, schema)

    # More memory, because we gotta go fast
    writer = ix.writer(limitmb=512)

    # Wordpress query to get the posts
    sql = """
    SELECT CONCAT(
            wpoo.option_value,
            REPLACE(
                REPLACE( wpo.option_value, '%%postname%%', wpp.post_name),
                    '%%category%%', 'post')
            ) as 'permalink',
            wpp.ID,
            wpp.post_title,
            wpp.post_content,
            wp_users.display_name
      FROM wp_posts wpp
      JOIN wp_options wpo
        ON wpo.option_name = 'permalink_structure'
      JOIN wp_options as wpoo
        ON wpoo.option_name = 'siteurl'
      JOIN wp_users
        ON wp_users.ID = wpp.post_author
     WHERE wpp.post_type = 'post'
       AND post_status = 'publish';
    """

    # Fetch all posts from database
    cursor = connection.cursor()
    cursor.execute(sql)
    resultq = cursor.fetchall()
    # For each post we will update the index document
    for row in resultq:
        writer.update_document(id=str(row["ID"]),
                               title=row["post_title"],
                               content=row["post_content"],
                               permalink=row['permalink'],
                               author=row['display_name'])
    writer.commit()
    connection.close()
    return jsonify({"status": 200, "message": "All posts indexed"})


if __name__ == '__main__':
    # app.run(debug=True, host="10.8.0.37")
    app.run(debug=True)
