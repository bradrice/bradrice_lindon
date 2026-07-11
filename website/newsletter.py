"""Newsletter signup: post subscribers to the Mailblast subscribe API.

The signup form on a ``NewsletterPage`` posts to the page itself; the page's
``serve()`` calls :func:`handle_subscribe`, which validates the input and
forwards it server-side to Mailblast's ``/api/subscribe/`` endpoint. The API
key lives in settings (from .env) and never reaches the browser.
"""

import logging

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

logger = logging.getLogger(__name__)

# User-facing copy for the failure cases (success copy comes from the page).
_ERR_INVALID = "Please enter a valid email address."
_ERR_UNAVAILABLE = "Newsletter signup is temporarily unavailable. Please try again later."
_ERR_GENERIC = "Sorry, something went wrong. Please try again."


def handle_subscribe(request, page) -> dict:
    """Process a signup POST and return template context.

    Returns a dict with ``submitted`` (True), ``success`` (bool), ``message``
    (str, shown on failure), and echoes back ``email`` / ``first_name`` /
    ``last_name`` so a failed form can be re-rendered with the user's input.
    """
    # Honeypot: a hidden field real users never fill. If it has a value, treat
    # the request as a bot and report success without doing anything.
    if request.POST.get("hp"):
        return {"submitted": True, "success": True, "message": ""}

    email = (request.POST.get("email") or "").strip()
    first_name = (request.POST.get("first_name") or "").strip()
    last_name = (request.POST.get("last_name") or "").strip()

    echo = {"email": email, "first_name": first_name, "last_name": last_name}

    try:
        validate_email(email)
    except ValidationError:
        return {"submitted": True, "success": False, "message": _ERR_INVALID, **echo}

    success, message = subscribe(
        email, first_name=first_name, last_name=last_name, list_name=page.list_name
    )
    if success:
        return {"submitted": True, "success": True, "message": ""}
    return {"submitted": True, "success": False, "message": message, **echo}


def subscribe(
    email: str, first_name: str = "", last_name: str = "", list_name: str = ""
) -> tuple[bool, str]:
    """POST one subscriber to Mailblast. Returns (success, user_facing_error)."""
    url = getattr(settings, "MAILBLAST_API_URL", "")
    key = getattr(settings, "MAILBLAST_API_KEY", "")
    if not url or not key:
        logger.error("Mailblast not configured (MAILBLAST_API_URL / MAILBLAST_API_KEY).")
        return False, _ERR_UNAVAILABLE

    payload = {"email": email}
    if first_name:
        payload["first_name"] = first_name
    if last_name:
        payload["last_name"] = last_name
    if list_name:
        payload["list"] = list_name

    try:
        resp = requests.post(url, json=payload, headers={"X-API-Key": key}, timeout=10)
    except requests.RequestException:
        logger.exception("Mailblast request failed")
        return False, _ERR_GENERIC

    if resp.status_code == 200:
        return True, ""
    if resp.status_code == 400:
        return False, _ERR_INVALID
    logger.error("Mailblast returned %s: %s", resp.status_code, resp.text[:200])
    return False, _ERR_GENERIC
