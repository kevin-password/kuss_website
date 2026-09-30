from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Event, NewsPost, Announcement, Product


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
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Event.objects.all()

    def lastmod(self, obj):
        # Event model has no updated_at field,
        # so use the event date.
        return obj.date

    def location(self, obj):
        return reverse(
            "event_detail",
            kwargs={"event_id": obj.pk}
        )


class NewsPostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return NewsPost.objects.all()

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        # News currently has no individual public detail URL.
        # Therefore the news listing is the canonical public page.
        return reverse("news")


class AnnouncementSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Announcement.objects.all()

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        # Announcements currently have no individual public detail URL.
        return reverse("announcements")


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse(
            "product_detail",
            kwargs={"product_id": obj.pk}
        )
