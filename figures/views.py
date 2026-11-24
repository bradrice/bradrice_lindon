from django.http import HttpResponse
from wagtail import hooks
from wagtail.models import Site
from wagtail.views import serve as wagtail_serve

from figures.models import FigureIndex


def home(request):
    """Serve the artwork gallery at ``/``.

    The gallery is the front page, but it cannot be the Site's root page: a
    Wagtail page has a URL only inside its Site's root, so rooting the site at
    the gallery left About, Poetry, Contact and the rest with ``None`` for a
    URL. The Site stays rooted at Home and this route shows the gallery in
    Home's place. The gallery keeps its own address, ``/artwork/``, and so do
    its figures.

    Falls back to Wagtail's normal routing (Home) if there is no live gallery
    under the site, so ``/`` never 404s because of this.
    """
    site = Site.find_for_request(request)
    gallery = (
        FigureIndex.objects.live().descendant_of(site.root_page).first()
        if site
        else None
    )
    if gallery is None:
        return wagtail_serve(request, "")

    # The same hooks wagtail.views.serve runs, so view restrictions and the
    # like apply here exactly as they do at /artwork/.
    for fn in hooks.get_hooks("before_serve_page"):
        result = fn(gallery, request, [], {})
        if isinstance(result, HttpResponse):
            return result

    def serve_chain(page, request, args, kwargs):
        return page.serve(request, *args, **kwargs)

    chain = serve_chain
    for fn in reversed(hooks.get_hooks("on_serve_page")):
        chain = fn(chain)
    return chain(gallery, request, [], {})
