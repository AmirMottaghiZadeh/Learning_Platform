import asyncio
import os
from unittest import skipUnless
from unittest.mock import patch
from uuid import uuid4

from django.test import SimpleTestCase
from django.test import override_settings
from django.core.cache.backends.redis import RedisCache
from kombu import Connection
from kombu.exceptions import VersionMismatch

from check_queue_dependencies import check_transport


class QueueDependencyTests(SimpleTestCase):
    def test_real_transport_client_is_checked_without_a_network_connection(self):
        with patch("redis.connection.Connection.connect", side_effect=AssertionError("No network")):
            versions = check_transport()
        self.assertEqual(set(versions), {"redis", "celery", "kombu"})

    def test_transport_version_mismatch_fails_the_check(self):
        with patch("check_queue_dependencies.Channel._get_client",
                   side_effect=VersionMismatch("incompatible client")):
            with self.assertRaises(VersionMismatch):
                check_transport()


@skipUnless(os.environ.get("QUEUE_TEST_REDIS_URL"), "Explicit test Redis connection required")
class RedisTransportIntegrationTests(SimpleTestCase):
    def test_django_cache_read_write_and_atomic_lease_operations(self):
        cache=RedisCache(os.environ["QUEUE_TEST_REDIS_URL"],
                         {"KEY_PREFIX":"cache-probe:"+uuid4().hex,
                          "OPTIONS":{"socket_connect_timeout":3,"socket_timeout":3,
                                     "retry_on_timeout":False}})
        try:
            self.assertTrue(cache.add("lease","owner",timeout=30))
            self.assertFalse(cache.add("lease","other",timeout=30))
            self.assertEqual(cache.get("lease"),"owner")
            cache.set("counter",1,timeout=30)
            self.assertEqual(cache.incr("counter"),2)
        finally:
            cache.delete_many(["lease","counter"])
            cache.close()

    def test_stream_events_are_replayable_with_sync_and_async_clients(self):
        from apps.ai_lab import events
        identifier=uuid4()
        url=os.environ["QUEUE_TEST_REDIS_URL"]
        with override_settings(AI_LAB_EVENT_REDIS_URL=url):
            try:
                sequence=events.append(identifier,{"type":"heartbeat"})
                self.assertEqual(sequence,1)
                expected=[{"type":"heartbeat","sequence":1}]
                self.assertEqual(events.read(identifier,0,block_ms=1),expected)
                async def read():
                    try:
                        return await events.read_async(identifier,0,block_ms=1)
                    finally:
                        await events._async_redis(url).aclose()
                self.assertEqual(asyncio.run(read()),expected)
            finally:
                events._redis(url).delete(events._key(identifier),events._key(identifier)+":sequence")

    def test_actual_broker_publish_consume_and_ack(self):
        identifier=uuid4().hex
        # Independent keys and queue: never consume application tasks or flush
        # a shared Redis database. The probe contains no user/model payload.
        with Connection(os.environ["QUEUE_TEST_REDIS_URL"],connect_timeout=3,
                        transport_options={"global_keyprefix":"queue-probe:"+identifier+":",
                                           "socket_timeout":3,"socket_connect_timeout":3}) as connection:
            queue=connection.SimpleQueue("probe-"+identifier)
            try:
                queue.put({"probe":identifier},serializer="json")
                message=queue.get(block=True,timeout=5)
                self.assertEqual(message.payload,{"probe":identifier})
                message.ack()
            finally:
                try:
                    queue.queue.delete()
                finally:
                    queue.close()
