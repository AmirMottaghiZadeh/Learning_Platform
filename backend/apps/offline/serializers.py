from rest_framework import serializers


class PackageFileSerializer(serializers.Serializer):
    name = serializers.CharField()
    size = serializers.IntegerField()
    sha256 = serializers.CharField()
    md5 = serializers.CharField()


class PackageManifestSerializer(serializers.Serializer):
    format = serializers.IntegerField()
    dataset = serializers.CharField()
    build = serializers.CharField()
    source_version = serializers.CharField(allow_blank=True)
    created_at = serializers.CharField()
    files = PackageFileSerializer(many=True)
    total_size = serializers.IntegerField()
    index = serializers.ListField(child=serializers.IntegerField(), min_length=3, max_length=3)
    check = serializers.CharField()


class OfflinePackageSerializer(serializers.Serializer):
    dataset = serializers.CharField()
    entitled = serializers.BooleanField()
    license_days = serializers.IntegerField()
    package = PackageManifestSerializer(allow_null=True)


class PackageUrlsRequestSerializer(serializers.Serializer):
    build = serializers.CharField(required=False, allow_blank=True, max_length=80)


class PackageFileUrlSerializer(PackageFileSerializer):
    url = serializers.CharField()


class PackageUrlsSerializer(serializers.Serializer):
    build = serializers.CharField()
    expires_at = serializers.CharField()
    files = PackageFileUrlSerializer(many=True)


class LicenseRequestSerializer(serializers.Serializer):
    build = serializers.CharField(max_length=80)
    # base64 SPKI of the browser's RSA-OAEP key; empty for the native app
    public_key = serializers.CharField(required=False, allow_blank=True, max_length=2048)


class LicenseSerializer(serializers.Serializer):
    build = serializers.CharField()
    server_time = serializers.CharField()
    valid_until = serializers.CharField()
    key = serializers.CharField(required=False)
    wrapped_key = serializers.CharField(required=False)
