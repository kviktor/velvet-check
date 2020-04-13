from hashlib import sha1
import json
import logging

from flask import Flask, request, jsonify, render_template
from flask_redis import FlaskRedis

from models import Article
from settings import BROKER_URL
from tasks import get_article_score

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['REDIS_URL'] = BROKER_URL
redis_store = FlaskRedis(app)


@app.route('/get_scores/', methods=['GET', 'POST', ])
def get_scores():
    article_urls = request.get_json() or []
    key = sha1(("".join(article_urls)).encode()).hexdigest()
    result = redis_store.get(key)
    if not result:
        logger.info("%s not found in cache", key)
        scores = {
            article_url: get_article_score(article_url)
            for article_url in article_urls
        }
        redis_store.set(key, json.dumps(scores))
        redis_store.expire(key, 60 * 60 if all_w_dict(scores) else 30)
    else:
        scores = json.loads(result)

    return jsonify(**scores)


@app.route('/list_articles/', methods=['GET'])
def list_articles():
    try:
        page = int(request.args.get('page'))
    except (ValueError, TypeError):
        page = 0

    articles = Article.list_paginated(page)
    return render_template('list_articles.html', articles=articles, page=page)


def all_w_dict(iterable_dict):
    for i in iterable_dict.values():
        if i is None:
            return False
    return True
