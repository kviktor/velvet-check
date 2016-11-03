import json
import logging
import sha

from flask import Flask, request, jsonify
from flask_redis import FlaskRedis
from tasks import get_article_score, BROKER_URL

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['REDIS_URL'] = BROKER_URL
redis_store = FlaskRedis(app)


@app.route("/")
def home():
    return "pls no"


@app.route('/get_scores/', methods=['GET', 'POST', ])
def get_scores():
    article_urls = request.get_json()
    key = sha.new("".join(article_urls)).hexdigest()
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


def all_w_dict(iterable_dict):
    for i in iterable_dict.values():
        if i is None:
            return False
    return True
