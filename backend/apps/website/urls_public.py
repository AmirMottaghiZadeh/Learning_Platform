from django.urls import path

from . import views_account, views_drugs, views_public as v

app_name = "site"

urlpatterns = [
    path("", v.home, name="home"),
    path("blog/", v.blog_index, name="blog"),
    path("blog/category/<str:slug>/", v.category, name="category"),
    path("blog/tag/<str:slug>/", v.tag, name="tag"),
    path("blog/<str:slug>/comment/", v.comment_post, name="comment"),
    path("blog/<str:slug>/", v.post_detail, name="post"),
    path("plans/", v.plans, name="plans"),
    path("download/", v.download, name="download"),
    path("dl/<int:pk>/", v.download_click, name="dl"),
    path("announcements/", v.announcements, name="announcements"),
    path("announcements/<str:slug>/", v.announcement_detail, name="announcement"),
    path("drugs/", views_drugs.drug_index, name="drugs"),
    path("drugs/<str:slug>/", views_drugs.drug_detail, name="drug"),
    path("contact/", v.contact, name="contact"),
    path("search/", v.search, name="search"),
    path("newsletter/", v.subscribe, name="subscribe"),
    path("media/<int:pk>/<str:name>", v.media, name="media"),
    path("robots.txt", v.robots, name="robots"),
    path("sitemap.xml", v.sitemap, name="sitemap"),
    path("rss.xml", v.feed, name="feed"),
    path("11601693.txt", v.verification_file, name="enamad"),
    path("site.webmanifest", v.webmanifest, name="webmanifest"),
    # icons at fixed root URLs (see seo.BRAND_FILES)
    path("favicon.ico", v.brand_file, {"name": "favicon.ico"}, name="favicon"),
    path("favicon-48x48.png", v.brand_file, {"name": "favicon-48x48.png"}),
    path("favicon-96x96.png", v.brand_file, {"name": "favicon-96x96.png"}),
    path("apple-touch-icon.png", v.brand_file, {"name": "apple-touch-icon.png"}),
    path("apple-touch-icon-precomposed.png", v.brand_file, {"name": "apple-touch-icon.png"}),
    path("icon-192.png", v.brand_file, {"name": "icon-192.png"}),
    path("icon-512.png", v.brand_file, {"name": "icon-512.png"}),
    path("og-image.png", v.brand_file, {"name": "og-image.png"}),
    # buying
    path("account/", views_account.account, name="account"),
    path("account/login/", views_account.login_phone, name="login"),
    path("account/code/", views_account.login_code, name="login_code"),
    path("account/password/", views_account.set_password, name="set_password"),
    path("account/logout/", views_account.logout_view, name="logout"),
    path("checkout/<int:price_id>/", views_account.checkout, name="checkout"),
    # last: an editor-made page by its slug
    path("<str:slug>/", v.page_detail, name="page"),
]
