from wagtail import hooks
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from .models import Author, BlogPost


@register_snippet
class AuthorSnippet(SnippetViewSet):
    model = Author
    add_to_main_manu = False
    panels = [
        FieldPanel("name"),
        FieldPanel("bio"),
    ]
