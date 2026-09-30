from django.contrib.sitemaps import Sitemap
from django.conf import settings
from django.urls import reverse

from .models import Event, Product


SITE_DOMAIN = getattr(
    settings,
    "SITE_DOMAIN",
    "https://kabsurgicalsociety.com"
).rstrip("/")


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return [
            "home",
            "about",
            "news",
            "announcements",
            "leadership",
            "join",
            "research",
            "privacy",
            "marketplace",
        ]

    def location(self, item):
        return SITE_DOMAIN + reverse(item)


class EventSitemap(Sitemap):
    priority = 0.9
    changefreq = "weekly"

    def items(self):
        return Event.objects.all()

    def location(self, obj):
        return (
            SITE_DOMAIN
            + reverse(
                "event_detail",
                kwargs={"event_id": obj.pk}
            )
        )


class ProductSitemap(Sitemap):
    priority = 0.6
    changefreq = "weekly"

    def items(self):
        return Product.objects.filter(is_active=True)

    def location(self, obj):
        return (
            SITE_DOMAIN
            + reverse(
                "product_detail",
                kwargs={"product_id": obj.pk}
            )
        )


sitemaps = {
    "static": StaticViewSitemap,
    "events": EventSitemap,
    "products": ProductSitemap,
}
