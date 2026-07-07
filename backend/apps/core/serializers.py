from rest_framework import serializers


class HealthChecksSerializer(serializers.Serializer):
    database = serializers.CharField()
    database_latency_ms = serializers.FloatField(required=False, allow_null=True)


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()
    service = serializers.CharField()
    version = serializers.CharField()
    environment = serializers.CharField()
    release_sha = serializers.CharField()
    time = serializers.DateTimeField()
    checks = HealthChecksSerializer()
