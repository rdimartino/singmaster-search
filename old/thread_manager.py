import threading
import time
import Queue


class ExitThread(threading.Thread):
    def __init__(self, thread_id):
        threading.Thread.__init__(self)
        self.thread_id = thread_id

    def run(self):
        print(self.thread_id + ' is listening')
        raw_input("Press Enter to stop loop...")
        print(self.thread_id + ' has stopped listening')


class DBThread(threading.Thread):
    def __init__(self, thread_id, queue, function, on=True):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.queue = queue
        self.f = function
        self.on = on

    def run(self):
        process_data(self.queue, self.f)

    def close(self):
        self.on = False


class ProcessThread(threading.Thread):
    def __init__(self, thread_id, function, on=True):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.function = function
        self.on = on

    def run(self):
        self.function()

    def close(self):
        self.on = False


def process_data(queue, f):
    queueLock.acquire()
    if not workQueue.empty():
        data = queue.get()
        f(data)
        queueLock.release()
    else:
        queueLock.release()
    time.sleep(5)

queueLock = threading.Lock()
workQueue = Queue.Queue(0)
