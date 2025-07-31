from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.images import get_image_model
from wagtail.images.blocks import ImageChooserBlock
from wagtail import blocks
from modelcluster.fields import ParentalKey
from dotenv import load_dotenv
import os

load_dotenv() # Load environment variables from .env

if (os.getenv('DJANGO_ENV') == "production"):
    default_artwork_price_id = os.getenv('STRIPE_ARTWORK_PRICE_PROD ')
else:
    default_artwork_price_id = os.getenv('STRIPE_ARTWORK_PRICE_DEV')


class FigureIndex(Page):
  # Al list of all the iconic figures in the database
    subpage_types = ['figures.FigureDetail']
    subtitle = models.CharField(max_length=255, blank=True)
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("subtitle"),
        FieldPanel("body"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context['figure_entries'] = FigureDetail.objects.live().descendant_of(self)
        return context


class FigureDetail(Page):
    parent_page_types = ['FigureIndex']
    subtitle = models.CharField(max_length=255, blank=True)
    gallery_number = models.IntegerField(blank=True, null=True)
    media_type = models.CharField(max_length=255, blank=True)
    body = RichTextField(blank=True)
    stripe_price_id = models.CharField(blank=True, default=default_artwork_price_id)
    price = models.DecimalField(blank=True, default="20.00", max_digits=10, decimal_places=2)
    for_sale = models.BooleanField(default=False)
    image = models.ForeignKey(
        get_image_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )


    content_panels = Page.content_panels + [
        FieldPanel('subtitle'),
        FieldPanel('gallery_number'),
        FieldPanel('media_type'),
        FieldPanel('body'),
        FieldPanel('image'),
        FieldPanel('price'),
        FieldPanel('stripe_price_id'),
        FieldPanel('for_sale'),
        InlinePanel('gallery_images', label='Gallery Images'),

    ]

class MyPageGalleryImage(models.Model):
    page = ParentalKey(FigureDetail, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ForeignKey(
        get_image_model(), on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        FieldPanel('image'),
        FieldPanel('caption'),
    ]
