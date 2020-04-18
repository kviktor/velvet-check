from hashlib import sha1
import json
import logging

from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Article
from .tasks import calculate_missing_article_scores
from .utils import all_w_dict

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def get_scores(request):
    try:
        article_urls = json.loads(request.body)
    except (TypeError, ValueError) as exc:
        logger.exception('Got invalid JSON in body')
        article_urls = []

    key = sha1(("".join(article_urls)).encode()).hexdigest()
    scores = cache.get(key)
    if not scores:
        logger.info("%s not found in cache", key)

        articles = Article.objects.filter(
            url__in=article_urls,
        ).values_list(
            'url', 'score',
        )

        scores = dict(articles)
        calculate_missing_article_scores.send(article_urls, list(scores.keys()))

        timeout = 60 * 60 if all_w_dict(scores) else 1
        cache.set(key, scores, timeout=timeout)

    return JsonResponse(scores)
