from types import SimpleNamespace
from unittest import mock

from django.test import RequestFactory, TestCase, override_settings

from website import newsletter


def _page(list_name=""):
    return SimpleNamespace(list_name=list_name)


@override_settings(
    MAILBLAST_API_URL="https://mailblast.example/api/subscribe/",
    MAILBLAST_API_KEY="test-key",
)
class HandleSubscribeTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def _post(self, **data):
        return self.rf.post("/newsletter/", data)

    @mock.patch("website.newsletter.requests.post")
    def test_honeypot_short_circuits_without_calling_api(self, post):
        result = newsletter.handle_subscribe(
            self._post(email="a@x.com", hp="i am a bot"), _page()
        )
        self.assertEqual(result, {"submitted": True, "success": True, "message": ""})
        post.assert_not_called()

    @mock.patch("website.newsletter.requests.post")
    def test_invalid_email_rejected_without_calling_api(self, post):
        result = newsletter.handle_subscribe(self._post(email="nope"), _page())
        self.assertFalse(result["success"])
        self.assertEqual(result["email"], "nope")  # echoed back for re-render
        post.assert_not_called()

    @mock.patch("website.newsletter.requests.post")
    def test_valid_signup_posts_expected_payload(self, post):
        post.return_value = mock.Mock(status_code=200)
        result = newsletter.handle_subscribe(
            self._post(email="a@x.com", first_name="Ann"), _page(list_name="News")
        )
        self.assertTrue(result["success"])
        _, kwargs = post.call_args
        self.assertEqual(
            kwargs["json"], {"email": "a@x.com", "first_name": "Ann", "list": "News"}
        )
        self.assertEqual(kwargs["headers"], {"X-API-Key": "test-key"})

    @mock.patch("website.newsletter.requests.post")
    def test_api_400_maps_to_invalid_email_message(self, post):
        post.return_value = mock.Mock(status_code=400, text="bad")
        result = newsletter.handle_subscribe(self._post(email="a@x.com"), _page())
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], newsletter._ERR_INVALID)

    @mock.patch("website.newsletter.requests.post")
    def test_api_500_maps_to_generic_message(self, post):
        post.return_value = mock.Mock(status_code=500, text="boom")
        result = newsletter.handle_subscribe(self._post(email="a@x.com"), _page())
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], newsletter._ERR_GENERIC)

    @mock.patch("website.newsletter.requests.post", side_effect=newsletter.requests.ConnectionError)
    def test_network_error_maps_to_generic_message(self, post):
        result = newsletter.handle_subscribe(self._post(email="a@x.com"), _page())
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], newsletter._ERR_GENERIC)

    @override_settings(MAILBLAST_API_URL="", MAILBLAST_API_KEY="")
    @mock.patch("website.newsletter.requests.post")
    def test_unconfigured_reports_unavailable_without_calling_api(self, post):
        result = newsletter.handle_subscribe(self._post(email="a@x.com"), _page())
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], newsletter._ERR_UNAVAILABLE)
        post.assert_not_called()
