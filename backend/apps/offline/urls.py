from django.urls import path

from .views import LicenseView, PackageFileView, PackageListView, PackageUrlsView

urlpatterns = [
    path("offline/packages/", PackageListView.as_view(), name="offline-packages"),
    path("offline/packages/<str:dataset>/urls/", PackageUrlsView.as_view(), name="offline-package-urls"),
    path("offline/packages/<str:dataset>/license/", LicenseView.as_view(), name="offline-package-license"),
    path("offline/files/<str:token>/", PackageFileView.as_view(), name="offline-package-file"),
]
