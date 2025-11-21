import os
from decimal import Decimal

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from dotenv import load_dotenv
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.images import get_image_model
from wagtail.images.models import Image
from wagtail.models import Orderable, Page
from wagtail.snippets.models import register_snippet

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
        if request.method == "GET" and 'media_type' in request.GET:
            current_media_type = request.GET.get('media_type')
            saved_choice = current_media_type
            request.session['selected_media'] = current_media_type
            request.session.save()
        else:
            saved_choice = request.session.get('selected_media', 'All')

        if request.method == "GET" and 'series_choice' in request.GET:
            current_series_type = request.GET.get('series_choice')
            series_choice = current_series_type
            request.session['series_choice'] = current_series_type
            request.session.save()
        else:
            series_choice = request.session.get('series_choice', 'All')

        all_figures = FigureDetail.objects.live().descendant_of(self)
        # media_array = all_figures.values_list('media_type', flat=True).distinct().order_by('media_type')
        media_array = MediaSnippet.objects.all().distinct().order_by('name')
        context['media_array'] = media_array
        series_array = SeriesName.objects.all().distinct().order_by('text')
        print("Series Array", series_array)
        context['series_array'] = series_array
        if saved_choice and saved_choice != 'All':
            print("Filtering by media:", saved_choice)
            figures = all_figures.filter(media_type__name=saved_choice)
            print(figures)
        else:
            print("No media filter applied")
            figures = all_figures

        if series_choice and series_choice != 'All':
            print("Filtering by series:", series_choice)
            # figures = figures.filter(series_type=series_choice)
            for figure in figures:
                if figure.series_type.filter(snippet__text=series_choice).exists():
                    pass
                else:
                    figures = figures.exclude(id=figure.id)
            print(figures)
        else:
            print("No series filter applied")

        # paginate based on current_media_type
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
        context['saved_choice'] = saved_choice
        context['figures'] = figures
        return context


class FigureDetail(Page):
    parent_page_types = ['FigureIndex']
    subtitle = models.CharField(max_length=255, blank=True)
    weight = models.IntegerField(default=0, help_text="Lower number means higher priority in sorting.")
    body = RichTextField(blank=True)
    stripe_price_id = models.CharField(blank=True, default=default_artwork_price_id)
    price = models.DecimalField(blank=True, default=Decimal(20.00), max_digits=10, decimal_places=2)
    for_sale = models.BooleanField(default=False)
    sold = models.BooleanField(default=False)
    image = models.ForeignKey(
        get_image_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    media_type = models.ForeignKey(
          'MediaSnippet',
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

    # MY_CHOICES = [
    #     ('Acrylic', 'Acrylic'),
    #     ('Oil', 'Oil'),
    #     ('Watercolor', 'Watercolor'),
    #     ('Print', 'Print'),
    #     ('Graphite', 'Graphite'),
    #     ('Pastel', 'Pastel'),
    # ]
    #
    # media = models.CharField(
    #     max_length=24,
    #     choices=MY_CHOICES,
    #     default=None
    # )

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
        FieldPanel('media_type'),
        # FieldPanel('MediaSnippet'),
        InlinePanel('series_type', label='Series Types'),
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

@register_snippet
class SeriesName(models.Model):
    text = models.CharField(max_length=255)

    panels = [
        FieldPanel("text"),
    ]

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Series Name"
        verbose_name_plural = "Series Names"

class MyPageSnippetOrderable(Orderable):
    page = ParentalKey(
        'FigureDetail',  # Replace 'MyPage' with the name of your main page/model
        on_delete=models.CASCADE,
        related_name='series_type' # This related_name is crucial for InlinePanel
    )
    snippet = models.ForeignKey(
        'SeriesName',
        on_delete=models.CASCADE,
        related_name='+' # Use '+' to avoid reverse accessor clashes
    )

    panels = [
        FieldPanel('snippet'), # Use SnippetChooserPanel for selecting snippets
    ]

@register_snippet
class MediaSnippet(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)

    panels = [
        FieldPanel('name'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Media Snippet"
        verbose_name_plural = "Media Snippets"
