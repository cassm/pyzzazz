import queue
from threading import Lock


class SharedState (queue.SimpleQueue):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mut = Lock()

    def set(self, item):
        self.put(item)

        # atomically drop all old versions
        self.mut.acquire()

        while self.qsize() > 1:
            self.get()

        self.mut.release()

    def get_if_available(self):
        if self.qsize() > 0:
            return self.get()
        else:
            return None
