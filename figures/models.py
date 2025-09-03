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

    # def post(self, request):
    #     if request.method == "POST":
    #         print("POST request received")
    #         media_type = request.POST.get("media_type")
    #         print (media_type)
    #         pass

    def get_context(self, request):
        context = super().get_context(request)
        if request.method == "GET":
            context['selected_media'] = request.GET.get('media_type', None)
        else:
            context['selected_media'] = None

        all_figures = FigureDetail.objects.live().descendant_of(self)
        media_array = all_figures.values_list('media', flat=True).distinct().order_by('media')
        context['media_array'] = media_array
        if context['selected_media']:
            print("Filtering by media:", context['selected_media'])
            figures = all_figures.filter(media=context['selected_media'])
            print(figures)
        else:
            print("No media filter applied")
            figures = all_figures

        # filter_param = request.GET.get('media', None)
        # if filter_param:
        #     Filter figures by media type if provided in the query parameters
        #     all_figures = all_figures.filter(media=filter_param)

        # Pagination
        paginator = Paginator(figures, 6)
        page = request.GET.get('page')
        try:
            # If the page exists and the ?page=x is an int
            figures = paginator.page(page)
        except PageNotAnInteger:
            # If the ?page=x is not an int; show the first page
            figures = paginator.page(1)
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

    # CHOICE_A = 'Acrylic'
    # CHOICE_B = 'Oil'
    # CHOICE_C = 'Watercolor'
    # CHOICE_D = 'Print'
    # CHOICE_E = 'Graphite'
    # CHOICE_F = 'Pastel'

    MY_CHOICES = [
        ('Acrylic', 'Acrylic'),
        ('Oil', 'Oil'),
        ('Watercolor', 'Watercolor'),
        ('Print', 'Print'),
        ('Graphite', 'Graphite'),
        ('Pastel', 'Pastel'),
    ]

    media = models.CharField(
        max_length=24,
        choices=MY_CHOICES,
        default=None
    )

    content_panels = Page.content_panels + [
        FieldPanel('subtitle'),
        FieldPanel('weight'),
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
