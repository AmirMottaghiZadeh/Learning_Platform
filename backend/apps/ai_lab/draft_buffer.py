"""Coalesce token callbacks; durable checkpoints do not run per upstream token."""
import time


class DraftBuffer:
    def __init__(self, publish, *, interval=.1, clock=time.monotonic, max_chars=512):
        self.publish, self.interval, self.clock, self.max_chars = publish, max(.02, interval), clock, max_chars
        self.pending = {}
        self.size = 0
        self.last = clock()

    def add(self, event):
        if event["type"] == "answer_reset":
            self.flush()
            self.publish(event)
            return
        self.pending.setdefault(event["part_index"], []).append(event["text"])
        self.size += len(event["text"])
        if self.size >= self.max_chars or self.clock() - self.last >= self.interval:
            self.flush()

    def flush(self):
        for index in list(self.pending):
            parts = self.pending[index]
            self.publish({"type":"answer_delta","part_index":index,"text":"".join(parts)})
            del self.pending[index]
        self.size = 0
        self.last = self.clock()

    def discard(self):
        self.pending.clear()
        self.size = 0
