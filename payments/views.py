from django.conf import settings  # new
from django.http.response import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView
import stripe

from dotenv import load_dotenv
import os

load_dotenv() # Load environment variables from .env
# Create your views here.

if (os.getenv('DJANGO_ENV') == "production"):
    default_irpin_book_price_id = os.getenv('IRPIN_BOOKLET_PRICE_PROD')
else:
    default_irpin_book_price_id = os.getenv('IRPIN_BOOKLET_PRICE_DEV')


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
       price_id = request.POST.get('price_id')
       product_id = request.POST.get('product_id')
       domain_url = 'https://dev.bradrice.com/'
       stripe.api_key = settings.STRIPE_SECRET_KEY
       return HttpResponse(staus=200)



@csrf_exempt
def create_checkout_session(request):
    # print("inside checkout session")
    if request.method == 'POST':
        price_id = request.POST.get('price_id')
        product_id = request.POST.get('product_id')
        unit_price = request.POST.get('price')
        title = request.POST.get('title')
        domain_url = 'https://dev.bradrice.com/'
        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            # Create new Checkout Session for the order
            # Other optional params include:
            # [billing_address_collection] - to display billing address details on the page
            # [customer] - if you have an existing Stripe Customer ID
            # [payment_intent_data] - capture the payment later
            # [customer_email] - prefill the email input in the form
            # For full details see https://stripe.com/docs/api/checkout/sessions/create

            # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
            if (price_id == default_irpin_book_price_id):
                checkout_session = stripe.checkout.Session.create(
                    success_url=domain_url + 'payments/success?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=domain_url + 'payments/cancelled/',
                    payment_method_types=['card'],
                    mode='payment',
                    line_items=[
                        {
                            'quantity': 1,
                            'price': price_id,
                        }
                    ]
                )

                return HttpResponseRedirect(checkout_session.url)

            else:
                unit_price = int(float(unit_price))
                checkout_session = stripe.checkout.Session.create(
                    success_url=domain_url + 'payments/success?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=domain_url + 'payments/cancelled/',
                    payment_method_types=['card'],
                    mode='payment',
                    line_items = [
                        {
                        'price_data' : {
                            'product': product_id,
                            'unit_amount': unit_price * 100,
                            'currency': 'usd',
                            'product_data': {
                            'name': title,
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
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
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

    return HttpResponse(status=200)
