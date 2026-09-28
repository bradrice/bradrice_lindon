import datetime
import shutil
import tempfile
from decimal import Decimal

from django.test import TestCase
from django.test import override_settings
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page
from wagtail.models import Site

from figures.models import FigureDetail
from figures.models import FigureIndex
from figures.models import MyPageGalleryImage


_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=_MEDIA_ROOT)
class FigureDetailRenderTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        root = Page.get_first_root_node()
        cls.index = root.add_child(
            instance=FigureIndex(title="Artwork", slug="artwork")
        )
        Site.objects.update_or_create(
            is_default_site=True,
            defaults={"hostname": "localhost", "root_page": cls.index},
        )
        cls.image = get_image_model().objects.create(
            title="Test image", file=get_test_image_file()
        )

    def _figure(self, **fields):
        fields.setdefault("title", "Blue Heron")
        fields.setdefault("slug", "blue-heron")
        fields.setdefault("image", self.image)
        figure = self.index.add_child(instance=FigureDetail(**fields))
        figure.save_revision().publish()
        return figure

    def _get(self, figure):
        response = self.client.get(figure.url)
        self.assertEqual(response.status_code, 200)
        return response

    def test_renders_title_and_back_link(self):
        response = self._get(self._figure())
        self.assertContains(response, "<h1>Blue Heron</h1>", html=True)
        self.assertContains(response, f'href="{self.index.url}"')
        self.assertTemplateUsed(response, "figures/figure_detail.html")

    def test_blank_subtitle_renders_no_empty_heading(self):
        response = self._get(self._figure(subtitle=""))
        self.assertNotContains(response, "<h2></h2>")

    def test_subtitle_renders_as_heading(self):
        response = self._get(self._figure(subtitle="Oil on panel"))
        self.assertContains(response, "<h2>Oil on panel</h2>", html=True)

    def test_social_meta_uses_absolute_urls(self):
        figure = self._figure()
        response = self._get(figure)
        self.assertEqual(
            response.context["weburl"], f"http://testserver{figure.url}"
        )
        image_url = response.context["image_url"]
        self.assertTrue(image_url.startswith("http://testserver/"))
        self.assertContains(response, f'content="{image_url}"', count=2)

    def test_for_sale_shows_price_and_posts_only_product_id(self):
        figure = self._figure(for_sale=True, price=Decimal("1250.00"))
        response = self._get(figure)
        self.assertContains(response, "Price: $1,250.00")
        self.assertContains(
            response,
            f'<input type="hidden" name="product_id" value="{figure.pk}"/>',
        )
        # The price must come from the database, never a client-editable input.
        self.assertNotContains(response, 'name="price"')
        self.assertNotContains(response, "not for sale")

    def test_sold_shows_badge_and_no_purchase_or_not_for_sale(self):
        response = self._get(self._figure(for_sale=True, sold=True))
        self.assertContains(response, "badge bg-danger")
        self.assertNotContains(response, "Purchase")
        self.assertNotContains(response, "not for sale")

    def test_not_for_sale(self):
        response = self._get(self._figure())
        self.assertContains(response, "This piece is not for sale.")
        self.assertNotContains(response, "Purchase")
        self.assertNotContains(response, "badge bg-danger")

    def test_dimensions_in_inches_and_cm(self):
        response = self._get(self._figure(width=10, height=20))
        self.assertContains(
            response,
            "Dimensions: 10.00&quot; (25.40 cm) width x "
            "20.00&quot; (50.80 cm) height",
        )

    def test_dimensions_hidden_unless_both_set(self):
        response = self._get(self._figure(width=10))
        self.assertNotContains(response, "Dimensions:")

    def test_date_painted_shows_month_and_year_only(self):
        response = self._get(
            self._figure(date_painted=datetime.date(2024, 3, 17))
        )
        self.assertContains(response, "Painted: March 2024")
        self.assertNotContains(response, "March 17")

    def test_date_painted_hidden_when_blank(self):
        response = self._get(self._figure())
        self.assertNotContains(response, "Painted:")

    def test_gallery_images_render_additional_views(self):
        figure = self._figure()
        MyPageGalleryImage.objects.create(page=figure, image=self.image)
        response = self._get(figure)
        self.assertContains(response, "Additional views")
        self.assertEqual(len(response.context["gallery_images"]), 1)

    def test_no_gallery_heading_without_gallery_images(self):
        response = self._get(self._figure())
        self.assertNotContains(response, "Additional views")

    def test_template_comments_do_not_leak(self):
        response = self._get(self._figure())
        self.assertNotContains(response, "{#")
        self.assertNotContains(response, "{% comment")
