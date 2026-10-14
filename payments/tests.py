from unittest import mock

from django.test import TestCase


CHECKOUT_URL = "/payments/create-checkout-session/"


@mock.patch("payments.views.stripe.checkout.Session.create")
class CreateCheckoutSessionInvalidProductTests(TestCase):
    """Bad artwork ids must 404 without reaching Stripe.

    A 5xx here makes Django email the admins, and scanners post junk to this
    endpoint routinely.
    """

    def _post(self, **data):
        with self.assertLogs("payments.views", level="WARNING"):
            return self.client.post(CHECKOUT_URL, data)

    def test_injection_probe_id_is_404(self, create):
        response = self._post(product_id="46'tMPdSa<'\">)PprpRI")
        self.assertEqual(response.status_code, 404)
        create.assert_not_called()

    def test_unknown_numeric_id_is_404(self, create):
        response = self._post(product_id="999999")
        self.assertEqual(response.status_code, 404)
        create.assert_not_called()

    def test_missing_id_is_404(self, create):
        response = self._post()
        self.assertEqual(response.status_code, 404)
        create.assert_not_called()
