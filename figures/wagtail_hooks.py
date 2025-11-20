from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

# @register_snippet
# class SeriesTypeSnippet(models.Model):
#     name = models.CharField(max_length=255)
#     # Add any other fields your snippet requires
#
#     panels = [
#         FieldPanel("name"),
#     ]
#
#     def __str__(self):
#         return self.name
