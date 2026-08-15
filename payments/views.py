import json
import logging
import os
from urllib.parse import urljoin

import stripe
from django.conf import settings  # new
from django.http.response import (HttpResponse, HttpResponseNotFound,
                                  HttpResponseRedirect, JsonResponse)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView
from dotenv import load_dotenv
from wagtail.images.models import Image

from figures.models import FigureDetail

ENV = os.getenv('DJANGO_ENV', 'development')

load_dotenv(dotenv_path=f'.env.{ENV}') # Load development environment variables from .env
# Create your views here.

logger = logging.getLogger(__name__)

# A Stripe Price already belongs to a Product, so passing the price is enough for
# the booklet — there is no product id to send. IRPIN_PRODUCT_ID and ART_PRODUCT_ID
# are read by nothing.
default_irpin_book_price_id = os.getenv('IRPIN_BOOKLET_PRICE')
irpin_shipping_id = os.getenv('IRPIN_BOOKLET_SHIPPING_ID')


class PaymentsPageView(TemplateView):
    template_name = 'payments.html'


# new
@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)

@csrf_exempt
@require_POST
def create_checkout_session(request):
    # print("inside checkout session")
    if request.method == 'POST':
        # The booklet has a fixed Stripe Price, set in the environment; artwork
        # prices come from the database in the branch below. `price`, `title`
        # and `image` are also posted by the artwork form but deliberately
        # ignored — they are client-controlled and the DB is authoritative.
        product_type = request.POST.get('product_type')
        domain_url = request.build_absolute_uri('/')
        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            # return HttpResponse(product_type)
            # Create new Checkout Session for the order
            # Other optional params include:
            # [billing_address_collection] - to display billing address details on the page
            # [customer] - if you have an existing Stripe Customer ID
            # [payment_intent_data] - capture the payment later
            # [customer_email] - prefill the email input in the form
            # For full details see https://stripe.com/docs/api/checkout/sessions/create

            # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
            if product_type == "irpin":
                # Both IDs come from the environment, and until now this branch
                # had never run in production — nothing posted `product_type`,
                # so its configuration has never actually been exercised. A
                # blank value would reach Stripe as None and come back as an
                # opaque parameter error, so fail here with a legible log line.
                missing = [
                    name
                    for name, value in (
                        ('IRPIN_BOOKLET_PRICE', default_irpin_book_price_id),
                        ('IRPIN_BOOKLET_SHIPPING_ID', irpin_shipping_id),
                    )
                    if not value
                ]
                if missing:
                    logger.error(
                        "booklet checkout misconfigured: %s not set in .env.%s",
                        ", ".join(missing), ENV,
                    )
                    return HttpResponse(
                        "Sorry — the booklet is not available for purchase right now.",
                        status=503,
                    )

                checkout_session = stripe.checkout.Session.create(
                    success_url=domain_url + 'payments/success?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=domain_url + 'payments/cancelled/',
                    payment_method_types=['card'],
                    mode='payment',
                    shipping_address_collection={"allowed_countries": ["US", "CA"]},
                    shipping_options=[
                        {
                            'shipping_rate': irpin_shipping_id, # Replace with your shipping rate ID
                        },
                    ],
                    line_items=[
                        {
                            'quantity': 1,
                            'price': default_irpin_book_price_id,
                            "adjustable_quantity": {"enabled": True, "minimum": 1, "maximum": 10},
                        }
                    ]
                )

                return HttpResponseRedirect(checkout_session.url)

            else:
                try:
                    product = FigureDetail.objects.get(id=request.POST.get('product_id'))
                except FigureDetail.DoesNotExist:
                    logger.warning(
                        "artwork checkout: no FigureDetail with id=%r",
                        request.POST.get('product_id'),
                    )
                    return HttpResponseNotFound("That artwork could not be found.")

                # Price comes from the database, never from the form. It used to be
                # read from `request.POST['price']`, a hidden input — so a client
                # could edit it and pay any amount for any piece.
                #
                # `price` is a DecimalField(decimal_places=2), so multiplying by 100
                # gives exact cents. The previous `int(float(price))` truncated to
                # whole dollars, silently dropping the cents.
                unit_amount = int(product.price * 100)

                # There is no Stripe Price object per artwork (the model has no
                # stripe_price_id — the template's hidden `price_id` input always
                # rendered empty), so the amount is passed inline via `price_data`.
                # NOTE: `price` is not a valid key inside `price_data` — it belongs on
                # the line item itself, and the two are mutually exclusive. Passing it
                # here is what made Stripe reject every artwork checkout.
                price_data = {
                    'unit_amount': unit_amount,
                    'currency': 'usd',
                    'product_data': {'name': product.title},
                }
                if product.image:
                    # urljoin, not concatenation: domain_url ends in "/" and the
                    # rendition URL begins with one, which produced "https://host//media/...".
                    rendition_url = Image.get_rendition(product.image, 'width-360').url
                    price_data['product_data']['images'] = [urljoin(domain_url, rendition_url)]

                checkout_session = stripe.checkout.Session.create(
                    success_url=domain_url + 'payments/success?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=domain_url + 'payments/cancelled/',
                    payment_method_types=['card'],
                    metadata={
                        'product_id': product.id,
                        'product_name': product.title,
                    },
                    payment_intent_data = {
                        'metadata':{
                        'product_name': product.title,
                        'product_id': product.id,
                        }
                    },
                    mode='payment',
                    shipping_address_collection={"allowed_countries": ["US", "CA"]},
                    line_items = [
                        {
                            'quantity': 1,
                            'price_data': price_data,
                        },
                    ],
                )

                return HttpResponseRedirect(checkout_session.url)

        except Exception:
            # Was: swallowed silently and returned 405 "This method is not allowed.",
            # so a failing checkout looked like a routing problem and left no trace.
            logger.exception(
                "checkout session failed (product_type=%r, product_id=%r)",
                request.POST.get('product_type'), request.POST.get('product_id'),
            )
            return HttpResponse("Sorry — we could not start checkout. Please try again.", status=502)


class SuccessView(TemplateView):
    template_name = 'success.html'


class CancelledView(TemplateView):
    template_name = 'cancelled.html'
