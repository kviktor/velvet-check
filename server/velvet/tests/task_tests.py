from unittest import mock

from django.test import TestCase

from velvet.models import Article
from velvet.tasks import calculate_missing_article_scores


class CalculateMissingArticleScoresTest(TestCase):
    @mock.patch('velvet.tasks.get_image_urls_from_link')
    @mock.patch('velvet.tasks.generate_score_for_images')
    def test(self, p_image, p_link):
        p_link.return_value = ['im_1', 'im_2']
        p_image.return_value = {'im_1': 1, 'im_2': 2}

        requested_urls = [1, 2, 3, 4, 5]
        urls_in_db = {1: 1, 2:2, 5:5}.keys()

        calculate_missing_article_scores(requested_urls, urls_in_db)

        self.assertTrue(Article.objects.filter(url='3').exists())
        self.assertTrue(Article.objects.filter(url='4').exists())

        article = Article.objects.get(url='3')
        self.assertEqual(
            list(article.images.values_list('url', 'score')),
            [('im_2', 2.0), ('im_1', 1.0)],
        )
