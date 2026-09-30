from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Event, Product


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
        return reverse(item)


class EventSitemap(Sitemap):
    priority = 0.9
    changefreq = "weekly"

    def items(self):
        return Event.objects.all()

    def location(self, obj):
        return reverse(
            "event_detail",
            kwargs={"event_id": obj.pk}
        )


class ProductSitemap(Sitemap):
    priority = 0.6
    changefreq = "weekly"

    def items(self):
        return Product.objects.filter(is_active=True)

    def location(self, obj):
        return reverse(
            "product_detail",
            kwargs={"product_id": obj.pk}
        )


sitemaps = {
    "static": StaticViewSitemap,
    "events": EventSitemap,
    "products": ProductSitemap,
}
