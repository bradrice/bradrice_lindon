from types import SimpleNamespace
from unittest import mock

from coderedcms.models.page_models import CoderedFormMixin
from django.test import RequestFactory
from django.test import SimpleTestCase
from django.test import TestCase

from website.models import FormPage
from website.models import FormPageField
from website.spam import find_spam_reason


SITE = "example.org"


def _check(
    email="visitor@gmail.com",
    name="Pat Doe",
    subject="Hello",
    message="I have a question about your collection.",
):
    return find_spam_reason(
        [email], [name, subject, message], SITE, name=name, subject=subject
    )


class FindSpamReasonTests(SimpleTestCase):
    def test_ordinary_message_passes(self):
        self.assertIsNone(_check())

    def test_sender_on_site_domain(self):
        self.assertIn("own domain", _check(email="sales@example.org"))

    def test_site_domain_with_www_prefix(self):
        reason = find_spam_reason(["a@example.org"], [], "www.example.org")
        self.assertIn("own domain", reason)

    def test_blocked_sender_domain_including_subdomains(self):
        self.assertIn("blocked sender", _check(email="x@couchhq.com"))
        self.assertIn("blocked sender", _check(email="x@vera.bangeshop.com"))

    def test_lookalike_domain_is_not_blocked(self):
        self.assertIsNone(_check(email="x@notcouchhq.com"))

    def test_link_to_blocked_domain(self):
        reason = _check(message="Try it: https://blastleadgeneration.com/demo")
        self.assertIn("blocked domain", reason)

    def test_too_many_links(self):
        links = " ".join(f"https://site{i}.example.com" for i in range(3))
        self.assertIn("too many links", _check(message=links))

    def test_a_couple_of_links_is_fine(self):
        self.assertIsNone(
            _check(message="See https://a.example.com and www.b.example.com")
        )

    def test_blocked_phrase_is_case_and_whitespace_insensitive(self):
        reason = _check(message="Check out our new Dog\r\nHarness today")
        self.assertIn("blocked phrase", reason)

    def test_curly_apostrophes_are_normalized(self):
        with mock.patch("website.spam._PHRASE_RE") as phrase_re:
            phrase_re.search.return_value = None
            _check(message="it’s")
        (body,), _ = phrase_re.search.call_args
        self.assertIn("it's", body)

    def test_phrases_match_whole_words_only(self):
        # "bange" is blocked; "exchange" must not trip it.
        self.assertIsNone(_check(message="An exchange of old photographs"))

    def test_subject_is_first_name_plus_surname(self):
        reason = _check(name="Chance", subject="Chance Bamford")
        self.assertEqual(reason, "subject is the sender's name")

    def test_full_name_in_subject_is_fine(self):
        self.assertIsNone(_check(name="Pat Doe", subject="Pat Doe"))
        self.assertIsNone(_check(name="Pat", subject="Pat has a question"))


class FormPageContainsSpamTests(TestCase):
    def setUp(self):
        self.page = FormPage(title="Contact", spam_protection=True)
        self.page.form_fields = [
            FormPageField(clean_name="full_name", field_type="singleline"),
            FormPageField(clean_name="email", field_type="email"),
            FormPageField(clean_name="subject", field_type="singleline"),
            FormPageField(clean_name="message", field_type="multiline"),
        ]
        site = SimpleNamespace(hostname=SITE)
        patcher = mock.patch.object(FormPage, "get_site", return_value=site)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _post(self, **overrides):
        data = {
            "full_name": "Pat Doe",
            "email": "pat@gmail.com",
            "subject": "Hello",
            "message": "A question about your collection.",
            **overrides,
        }
        return RequestFactory().post("/contact/", data)

    @mock.patch.object(CoderedFormMixin, "contains_spam", return_value=False)
    def test_clean_submission_is_accepted(self, _):
        self.assertFalse(self.page.contains_spam(self._post()))

    @mock.patch.object(CoderedFormMixin, "contains_spam", return_value=False)
    def test_content_filter_rejects_spam(self, _):
        with self.assertLogs("website.models", "WARNING") as logs:
            spam = self.page.contains_spam(self._post(email="x@example.org"))
        self.assertTrue(spam)
        self.assertIn("own domain", logs.output[0])

    @mock.patch.object(CoderedFormMixin, "contains_spam", return_value=True)
    def test_codered_check_still_runs_first(self, _):
        self.assertTrue(self.page.contains_spam(self._post()))

    @mock.patch.object(CoderedFormMixin, "contains_spam", return_value=False)
    def test_disabled_spam_protection_skips_filter(self, _):
        self.page.spam_protection = False
        post = self._post(email="x@example.org")
        self.assertFalse(self.page.contains_spam(post))
