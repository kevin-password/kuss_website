from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Event, Product


# ============================================================
# STATIC PUBLIC PAGES
# ============================================================

class StaticViewSitemap(Sitemap):
    """
    Sitemap for KUSS public pages that do not require
    database objects.
    """

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


# ============================================================
# EVENTS
# ============================================================

class EventSitemap(Sitemap):
    """
    Sitemap for individual public KUSS event pages.

    Example:
    /event/1/
    /event/2/
    /event/3/
    """

    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Event.objects.all()

    def lastmod(self, obj):
        """
        Event currently has no updated_at field,
        so use the event date.
        """
        return obj.date

    def location(self, obj):
        return reverse(
            "event_detail",
            kwargs={
                "event_id": obj.pk
            }
        )


# ============================================================
# MARKETPLACE PRODUCTS
# ============================================================

class ProductSitemap(Sitemap):
    """
    Sitemap for active KUSS marketplace products.
    """

    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Product.objects.filter(
            is_active=True
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse(
            "product_detail",
            kwargs={
                "product_id": obj.pk
            }
        )
