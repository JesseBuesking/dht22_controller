
import Queue

class CappedQueue(object):
    """
    A queue that only holds the last ``cap`` items that were added.
    """

    def __init__(self, cap=10):
        self.cap = cap
        self.queue = Queue.Queue()

    def put(self, item):
        self.queue.put(item)
        if self.queue.qsize() > self.cap:
            self.queue.get()

    def tolist(self):
        return list(self.queue.queue)
