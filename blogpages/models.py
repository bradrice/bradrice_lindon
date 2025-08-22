from django.db import models
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.images import get_image_model
from wagtail.images.models import Image
from wagtail.images.blocks import ImageChooserBlock
from wagtail.blocks import RichTextBlock
from modelcluster.fields import ParentalKey
from wagtail.snippets.blocks import SnippetChooserBlock

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
        all_posts = BlogPost.objects.live().descendant_of(self)
        # Pagination
        paginator = Paginator(all_posts, 2)
        page = request.GET.get('page')
        try:
            # If the page exists and the ?page=x is an int
            posts = paginator.page(page)
        except PageNotAnInteger:
            # If the ?page=x is not an int; show the first page
            posts = paginator.page(1)
        except EmptyPage:
            # If the ?page=x is out of range (too high most likely)
            # Then return the last page
            posts = paginator.page(paginator.num_pages)

        context['blog_posts'] = posts
        return context


class BlogPost(Page):
    template = 'blogpages/blog_post.html'
    parent_page_types = ['BlogIndex']
    subpage_types = []
    subtitle = models.CharField(max_length=255, blank=True)
    author = models.ForeignKey(
          'blogpages.Author',
          null=True,
          blank=True,
          on_delete=models.SET_NULL,
          related_name='+'
      )

    body = StreamField(
        [
        ('text', RichTextBlock()),
        ('image', ImageChooserBlock()),
    ],
        block_counts = {
            'text': {'min_num': 1},
            'image': {'max_num': 2},
        },
        use_json_field=True,
        blank=True,
        null=True,
    )
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
        FieldPanel('author'),
        FieldPanel('image'),
        FieldPanel('body'),
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


class Author(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField()

    def __str__(self):
        return self.name
