from django.db import models
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.images import get_image_model
from wagtail.images.models import Image
from wagtail.images.blocks import ImageChooserBlock
from wagtail import blocks
from modelcluster.fields import ParentalKey
from dotenv import load_dotenv
import os

load_dotenv() # Load environment variables from .env

default_artwork_price_id = os.getenv('STRIPE_ARTWORK_PRICE')


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
        all_figures = FigureDetail.objects.live().descendant_of(self)
        # Pagination
        paginator = Paginator(all_figures, 1)
        page = request.GET.get('page')
        try:
            # If the page exists and the ?page=x is an int
            figures = paginator.page(page)
        except PageNotAnInteger:
            # If the ?page=x is not an int; show the first page
            figuree = paginator.page(1)
        except EmptyPage:
            # If the ?page=x is out of range (too high most likely)
            # Then return the last page
            figures = paginator.page(paginator.num_pages)

        context['figures'] = figures
        return context


class FigureDetail(Page):
    parent_page_types = ['FigureIndex']
    subtitle = models.CharField(max_length=255, blank=True)
    weight = models.IntegerField(default=0, help_text="Lower number means higher priority in sorting.")
    media_type = models.CharField(max_length=255, blank=True)
    body = RichTextField(blank=True)
    stripe_price_id = models.CharField(blank=True, default=default_artwork_price_id)
    price = models.DecimalField(blank=True, default="20.00", max_digits=10, decimal_places=2)
    for_sale = models.BooleanField(default=False)
    sold = models.BooleanField(default=False)
    image = models.ForeignKey(
        get_image_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    CHOICE_A = 'Acrylic'
    CHOICE_B = 'Oil'
    CHOICE_C = 'Watercolor'
    CHOICE_D = 'Print'
    CHOICE_E = 'Graphite'
    CHOICE_F = 'Pastel'

    MY_CHOICES = [
        (CHOICE_A, 'Acrylic'),
        (CHOICE_B, 'Oil'),
        (CHOICE_C, 'Watercolor'),
        (CHOICE_D, 'Print'),
        (CHOICE_E, 'Graphite'),
        (CHOICE_F, 'Pastel'),
    ]

    media = models.CharField(
        max_length=24,
        choices=MY_CHOICES,
        default=CHOICE_A,
    )

    content_panels = Page.content_panels + [
        FieldPanel('media'),
    ]


    content_panels = Page.content_panels + [
        FieldPanel('subtitle'),
        FieldPanel('weight'),
        FieldPanel('media_type'),
        FieldPanel('body'),
        FieldPanel('image'),
        FieldPanel('price'),
        FieldPanel('stripe_price_id'),
        FieldPanel('for_sale'),
        FieldPanel('sold'),
        InlinePanel('gallery_images', label='Gallery Images'),
        FieldPanel('media'),

    ]
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context['gallery_images'] = self.gallery_images.all()
        image_url = Image.get_rendition(self.image, 'width-360').url if self.image else None
        context['image_url'] = domain_url = request.build_absolute_uri(image_url) if image_url else None
        context['weburl'] = request.build_absolute_uri(request.path)
        return context

    class Meta:
        # Define the default ordering for queries on this model
        # Products with lower 'weight' values will appear first
        ordering = ['weight', 'title'] # You can add other fields for secondary sorting

    def __str__(self):
        return self.title


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
