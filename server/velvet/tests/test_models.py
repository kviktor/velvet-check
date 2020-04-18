from model_mommy import mommy

from django.test import TestCase

from velvet.models import (
    Article,
    Image,
)


class ArticleModelTest(TestCase):
    def test_score_with_multiple_images(self):
        article = mommy.make(Article)
        image_1 = mommy.make(Image, score=0.5, article=article)
        image_2 = mommy.make(Image, score=0.8, article=article)

        self.assertEqual(list(article.images.all()), [image_2, image_1])

        self.assertIsNone(Article.objects.filter(score__gte=0.90).first())
        self.assertEqual(
            Article.objects.filter(score__gte=0.75).first(),
            article,
        )

    def test_score_without_images(self):
        mommy.make(Article)
        self.assertEqual(0, Article.objects.get().score)
