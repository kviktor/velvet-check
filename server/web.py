from flask import Flask, request, jsonify
from tasks import get_article_score

app = Flask(__name__)


@app.route("/")
def home():
    return "pls no"


@app.route('/get_scores/', methods=['GET', 'POST', ])
def get_scores():
    # TODO cache
    article_urls = request.get_json()
    return jsonify(**{
        article_url: get_article_score(article_url)
        for article_url in article_urls
    })
