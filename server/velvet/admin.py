from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Article,
    Image,
)


class ArticleAdmin(admin.ModelAdmin):
    list_display = ('url', 'score', 'image_count', 'created_at', 'updated_at')
    readonly_fields = ('related_images', )

    def image_count(self, obj):
        return obj.images.count()

    def score(self, obj):
        return ('%0.4lf' % obj.score) if obj.score else None

    def related_images(self, obj):
        return mark_safe(
            '<a href="{}?article={}">Click here for the images.</a>'.format(
                reverse("admin:velvet_image_changelist"),
                obj.id,
            )
        )
    related_images.allow_tags = True
    related_images.short_description = 'Images'


class ImageAdmin(admin.ModelAdmin):
    raw_id_fields = ('article', )
    readonly_fields = ('score', 'img_tag')
    list_display = ('url', 'score', 'created_at', 'updated_at')

    def img_tag(self, obj):
        return mark_safe('<img src="{}"/>'.format(obj.url))


admin.site.register(Article, ArticleAdmin)
admin.site.register(Image, ImageAdmin)
