from django.db.models import (
    DateTimeField,
    FloatField,
    ForeignKey,
    Manager,
    Max,
    Model,
    URLField,
    Value,
    CASCADE,
)
from django.db.models.functions import Coalesce


class UpdatedCreatedModel(Model):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ArticleManager(Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(
            score=Coalesce(Max('images__score'), Value(0)),
        )


class Article(UpdatedCreatedModel):
    url = URLField(max_length=255, db_index=True, unique=True)

    objects = ArticleManager()

    class Meta:
        ordering = ('-created_at', )

    def __str__(self):
        return '{url}'.format(url=self.url)


class Image(UpdatedCreatedModel):
    article = ForeignKey(
        Article,
        related_name='images',
        on_delete=CASCADE,
    )
    url = URLField(max_length=511, db_index=True)
    score = FloatField(null=True, default=None)

    class Meta:
        unique_together = (('article', 'url'), )
        ordering = ('-created_at', )

    def __str__(self):
        return '{article_url} - {url} - {score}'.format(
            article_url=self.article.url,
            url=self.url,
            score=self.score,
        )
