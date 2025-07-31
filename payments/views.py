from django.conf import settings  # new
from django.http.response import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView
from figures.models import FigureDetail
from wagtail.images.models import Image
import stripe

from dotenv import load_dotenv
import os

ENV = os.getenv('DJANGO_ENV', 'development')

load_dotenv(dotenv_path=f'.env.{ENV}') # Load development environment variables from .env
# Create your views here.

default_irpin_book_price_id = os.getenv('IRPIN_BOOKLET_PRICE')
irpin_shipping_id = os.getenv('IRPIN_BOOKLET_SHIPPING_ID')
irpin_product_id = os.getenv('IRPIN_PRODUCT_ID')


class PaymentsPageView(TemplateView):
    template_name = 'payments.html'


# new
@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)

@csrf_exempt
def checkout_view(request):
    if request.method == 'POST':
       # price_id = request.POST.get('price_id')
       price_id = "price_1RjhFyHr3XrGP7sjocSQhToz"
       product_id = request.POST.get('product_id')
       domain_url = request.build_absolute_uri('/')
       stripe.api_key = settings.STRIPE_SECRET_KEY
       return HttpResponse(staus=200)



@csrf_exempt
def create_checkout_session(request):
    product = FigureDetail.objects.get(id=request.POST.get('product_id'))
    # print("inside checkout session")
    image = request.POST.get('image')
    image_url = Image.get_rendition(product.image, 'width-360').url if product.image else None
    if request.method == 'POST':
        price_id = default_irpin_book_price_id
            # price_id = request.POST.get('price_id')
        product_type = request.POST.get('product_type')
        unit_price = request.POST.get('price')
        title = request.POST.get('title')
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
            if (product_type == "irpin"):
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
                            'price': price_id,
                            "adjustable_quantity": {"enabled": True, "minimum": 1, "maximum": 10},
                        }
                    ]
                )

                return HttpResponseRedirect(checkout_session.url)

            else:
                product_id = os.getenv('ART_PRODUCT_ID')
                price_id = os.getenv('STRIPE_ARTWORK_PRICE ')
                unit_price = int(float(unit_price))
                checkout_session = stripe.checkout.Session.create(
                    success_url=domain_url + 'payments/success?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=domain_url + 'payments/cancelled/',
                    payment_method_types=['card'],
                    mode='payment',
                    shipping_address_collection={"allowed_countries": ["US", "CA"]},
                    line_items = [
                        {
                        'price_data' : {
                            'price': price_id,
                            'unit_amount': unit_price * 100,
                            'currency': 'usd',
                            'product_data': {
                            'name': title,
                            'images': [f"{domain_url}{image_url}"],
                            'metadata': {
                                'product_id':  product_id,  # Pass the primary key of the artwork
                            }
                            },
                        },
                        'quantity': 1,
                        },
                    ],
                ),
                # return JsonResponse(checkout_session, safe=False)

                return HttpResponseRedirect(checkout_session[0].url)

            # return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})


class SuccessView(TemplateView):
    template_name = 'success.html'


class CancelledView(TemplateView):
    template_name = 'cancelled.html'


@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    # sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        print("Payment was successful.")
        # TODO: run some custom code here
        # send_mail("artwork sold", "this artwork sold on your website", 'admin@oh-joy.org', ["bradrice1@gmail.com"])

    return HttpResponse(status=200)
