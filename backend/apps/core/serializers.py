from rest_framework import serializers


class HealthChecksSerializer(serializers.Serializer):
    database = serializers.CharField()


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()
    service = serializers.CharField()
    version = serializers.CharField()
    time = serializers.DateTimeField()
    checks = HealthChecksSerializer()
