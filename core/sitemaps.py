from django.http import HttpResponse


def sitemap_view(request):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

    <url>
        <loc>https://kabsurgicalsociety.com/</loc>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>

    <url>
        <loc>https://kabsurgicalsociety.com/about/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>

    <url>
        <loc>https://kabsurgicalsociety.com/news/</loc>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>

    <url>
        <loc>https://kabsurgicalsociety.com/announcements/</loc>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>

    <url>
        <loc>https://kabsurgicalsociety.com/leadership/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>

    <url>
        <loc>https://kabsurgicalsociety.com/join/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.9</priority>
    </url>

    <url>
        <loc>https://kabsurgicalsociety.com/research/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>

    <url>
        <loc>https://kabsurgicalsociety.com/privacy/</loc>
        <changefreq>yearly</changefreq>
        <priority>0.3</priority>
    </url>

    <url>
        <loc>https://kabsurgicalsociety.com/marketplace/</loc>
        <changefreq>weekly</changefreq>
        <priority>0.6</priority>
    </url>

</urlset>
"""

    return HttpResponse(
        xml,
        content_type="application/xml"
    )
