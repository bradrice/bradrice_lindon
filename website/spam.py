"""
Content-based spam filter for contact form submissions.

reCAPTCHA and honeypots stop bots, but most contact-form spam now comes from
paid services that solve captchas (or use real people) and paste in a canned
sales pitch. Those only show up in *what* is submitted, so this module looks
at the submitted values themselves.

Every rule here was drawn from spam that actually reached bradrice.com or
lodiharrisvillehistorical.org. This file is kept identical in both repos —
if you add a phrase or domain in one, copy the file to the other.
"""

import re


# Sender domains that have only ever sent spam. Subdomains match too, which
# covers senders that rotate a fresh subdomain per message
# (sales@<name>.bangeshop.com). Also checked against links in the message.
BLOCKED_DOMAINS = {
    "anwarcapitalllc.com",
    "bangeshop.com",
    "blastleadgeneration.com",
    "buyantibiotic.com",
    "caredogbest.com",
    "couchhq.com",
    "easerelief.net",
    "getdandynow.com",
    "hiring.biz",
    "lustrouslivingclean.com",
    "medicopostura.com",
    "polarisjanitorial.com",
    "premierwindowcleaner.com",
    "tidbuy.com",
}

# Matched case-insensitively on word boundaries against every text field.
# Keep these specific enough that a real visitor would never write them.
BLOCKED_PHRASES = [
    # Mailing-list boilerplate a person writing to you would never include.
    # ("unsubscribe" is deliberately absent: a newsletter subscriber might
    # use the contact form to ask for exactly that.)
    "optout",
    "respond with stop",
    # Marketing and SEO pitches.
    "com owner",
    "web visitors into leads",
    "generate more leads",
    "guest post",
    "your blog could feature",
    "featuring it on your site",
    "video promotion",
    "promotional tool",
    "ranking low in search",
    "losing 10 customers",
    # Local-services cold pitches.
    "complimentary cleaning",
    "cleaning bid",
    "cleaning quote",
    "window cleaning",
    # Loans and advance-fee scams.
    "loan offer",
    "instant approval",
    "no collateral",
    "charity mission",
    # Product spam.
    "antibiotics",
    "bange",
    "dog harness",
    "pawsafer",
    "medico postura",
    "posture corrector",
    "fitrx",
    "muscle massager",
    "elitenook",
    "airluxe",
]

# Real visitors rarely paste more than a link or two.
MAX_LINKS = 2

_PHRASE_RE = re.compile(
    r"\b(?:"
    + "|".join(re.escape(p).replace(r"\ ", r"\s+") for p in BLOCKED_PHRASES)
    + r")\b",
    re.IGNORECASE,
)
_URL_RE = re.compile(r"(?:https?://|www\.)([^\s/<>\"']+)", re.IGNORECASE)


def _normalize(text):
    return text.replace("’", "'").replace("‘", "'")


def _domain_matches(domain, domains):
    domain = domain.lower().rstrip(".")
    return any(domain == d or domain.endswith("." + d) for d in domains)


def find_spam_reason(emails, texts, site_domain="", name="", subject=""):
    """
    Return a short reason string if the submission looks like spam, else None.

    * ``emails`` — values of the form's email fields.
    * ``texts`` — values of every other text field (name, subject, message…).
    * ``site_domain`` — this site's own domain, e.g. ``bradrice.com``.
    * ``name`` / ``subject`` — the name and subject fields, when present.
    """
    site_domain = site_domain.lower().removeprefix("www.")

    for email in emails:
        domain = email.rpartition("@")[2].strip()
        if not domain:
            continue
        # Nobody writes to a site from that site's own address; spammers
        # spoof it constantly (sales@lodiharrisvillehistorical.org).
        if site_domain and _domain_matches(domain, {site_domain}):
            return f"sender uses the site's own domain ({email})"
        if _domain_matches(domain, BLOCKED_DOMAINS):
            return f"blocked sender domain ({email})"

    body = _normalize(" \n".join(texts))

    link_domains = _URL_RE.findall(body)
    for domain in link_domains:
        if _domain_matches(domain, BLOCKED_DOMAINS):
            return f"link to blocked domain ({domain})"
    if len(link_domains) > MAX_LINKS:
        return f"too many links ({len(link_domains)})"

    match = _PHRASE_RE.search(body)
    if match:
        return f"blocked phrase ({match.group(0)!r})"

    # Rotating product spam fills the name field with a first name and the
    # subject with that same first name plus a surname: "Chance" /
    # "Chance Bamford". People don't title a message with their own name.
    name, subject = name.strip(), subject.strip()
    if (
        name
        and " " not in name
        and re.fullmatch(re.escape(name) + r"\s+\S+", subject, re.IGNORECASE)
    ):
        return "subject is the sender's name"

    return None
