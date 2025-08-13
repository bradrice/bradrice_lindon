from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.images import get_image_model
from wagtail.images.models import Image
from wagtail.images.blocks import ImageChooserBlock
from wagtail import blocks
from modelcluster.fields import ParentalKey

class BlogIndex(Page):
    template = 'blogpages/blog_index.html'
    max_count = 1
    # parent_page_types = ['wagtailcore.Page']
    subpage_types = ['blogpages.BlogPost']
    subtitle = models.CharField(max_length=255, blank=True)
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("subtitle"),
        FieldPanel("body"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context['blog_posts'] = BlogPost.objects.live().descendant_of(self)
        return context


class BlogPost(Page):
    template = 'blogpages/blog_post.html'
    parent_page_types = ['BlogIndex']
    subpage_types = []
    subtitle = models.CharField(max_length=255, blank=True)
    body = RichTextField(blank=True)
    image = models.ForeignKey(
        get_image_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    # categories = models.ManyToManyField("Category", related_name="blog_post")

    content_panels = Page.content_panels + [
        FieldPanel('subtitle'),
        FieldPanel('body'),
        FieldPanel('image'),
        # FieldPanel('categories'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        image_url = Image.get_rendition(self.image, 'width-360').url if self.image else None
        context['image_url'] = domain_url = request.build_absolute_uri(image_url) if image_url else None
        context['weburl'] = request.build_absolute_uri(request.path)
        return context

    def __str__(self):
        return self.title
