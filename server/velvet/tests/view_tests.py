import json
from unittest import mock
from model_mommy import mommy

from django.test import (
    Client,
    TestCase,
)


class GetScoresTest(TestCase):
    def test_invalid_body(self):
        with mock.patch('velvet.views.logger') as p_logger:
            Client().post('/get_scores/', 'nop', content_type="application/json")
            p_logger.exception.assert_called_once()

        with mock.patch('velvet.views.logger') as p_logger:
            Client().post('/get_scores/', '', content_type="application/json")
            p_logger.exception.assert_called_once()

        with mock.patch('velvet.views.logger') as p_logger:
            Client().post('/get_scores/', '[]', content_type="application/json")
            p_logger.exception.assert_not_called()

    @mock.patch('velvet.views.cache')
    def test_cache_hit(self, p_cache):
        p_cache.get.return_value = {'a': 'b'}
        response = Client().post(
            '/get_scores/', '[]', content_type='application/json')
        self.assertEqual(response.json(), {'a': 'b'})

    @mock.patch('velvet.views.cache')
    def test_no_cache_hit_in_db(self, p_cache):
        p_cache.get.return_value = None

        mommy.make('velvet.Article', url='a_1')
        mommy.make('velvet.Article', url='a_2')

        response = Client().post(
            '/get_scores/', '["a_1", "a_2"]', content_type='application/json')

        self.assertEqual({
            'a_1': 0.0,
            'a_2': 0.0,
        },response.json())
        p_cache.set.assert_called_once_with(mock.ANY, mock.ANY, timeout=600)


    @mock.patch('velvet.views.cache')
    def test_no_cache_hit_not_in_db(self, p_cache):
        p_cache.get.return_value = None

        mommy.make('velvet.Article', url='a_1')

        response = Client().post(
            '/get_scores/', '["a_1", "a_2"]', content_type='application/json')

        self.assertEqual({
            'a_1': 0.0,
        },response.json())
        p_cache.set.assert_called_once_with(mock.ANY, mock.ANY, timeout=15)
