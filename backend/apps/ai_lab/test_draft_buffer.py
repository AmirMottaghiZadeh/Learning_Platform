from django.test import SimpleTestCase
from .draft_buffer import DraftBuffer


class DraftBufferTests(SimpleTestCase):
    def test_many_token_callbacks_become_one_lossless_checkpoint(self):
        events=[];buffer=DraftBuffer(events.append,clock=lambda:0)
        for text in ["متن", " ", "فارسی", "."]*20:
            buffer.add({"type":"answer_delta","part_index":0,"text":text})
        self.assertEqual(events,[])
        buffer.flush()
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]["text"],"متن فارسی."*20)

    def test_interval_flushes_and_reset_cannot_reorder_or_duplicate_text(self):
        events=[];now=[0]
        buffer=DraftBuffer(events.append,clock=lambda:now[0])
        buffer.add({"type":"answer_delta","part_index":0,"text":"first"})
        now[0]=.11
        buffer.add({"type":"answer_delta","part_index":0,"text":" second"})
        self.assertEqual(events[0]["text"],"first second")
        buffer.add({"type":"answer_delta","part_index":0,"text":"third"})
        buffer.add({"type":"answer_reset","part_index":0})
        buffer.flush()
        self.assertEqual([event["type"] for event in events],["answer_delta","answer_delta","answer_reset"])
        self.assertEqual(events[1]["text"],"third")

    def test_failed_or_cancelled_work_can_discard_an_unpublished_tail(self):
        events=[];buffer=DraftBuffer(events.append,clock=lambda:0)
        buffer.add({"type":"answer_delta","part_index":0,"text":"unverified tail"})
        buffer.discard();buffer.flush()
        self.assertEqual(events,[])
