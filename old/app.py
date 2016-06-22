from flask import Flask, Response, render_template
from singmasterMath import product

import threading
import time
import math
import Queue
import atexit
import json

# import thread_manager
import singmasterMath
import pascalDB


# SSE
class ServerSentEvent(object):

    def __init__(self, data, event=None):
        self.data = data
        self.event = event
        self.id = None
        self.desc_map = {
            self.data: "data",
            self.event: "event",
            self.id: "id"
        }

    def encode(self):
        if not self.data:
            return ""
        lines = ["%s: %s" % (v, k)
                 for k, v in self.desc_map.iteritems() if k]
        return "%s\n\n" % "\n".join(lines)


class ProcessThread(threading.Thread):
    def __init__(self, thread_id, function, on=True, counter=1):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.function = function
        self.on = on
        self.counter = counter

    def run(self):
        while self.on and self.counter > 0:
            self.counter -= 1
            # print('process run', self.counter)
            # self.function()

    def close(self):
        self.on = False


db_queue_lock = threading.Lock()
db_queue = Queue.Queue(0)

app = Flask(__name__)
status_queue = Queue.Queue(0)


def search():
    # Loop
    centers = 500
    center = 3
    starting_points = list(range(centers + 1))
    while active_search['on'] and center < centers:
        # print(center)
        t = singmasterMath.pascalTriCenter(center)
        data = {'center': {'diagonal': center, 'value': t},
                'results': []}
        running_time = 0
        for i in range(2, center + 1):
            target = t * math.factorial(i)
            try:
                starting_points[i]
            except IndexError:
                starting_points.append(i)
            b = singmasterMath.binarySearch(starting_points[i], target, lambda x: product(singmasterMath.Pascal(i, x).integers))
            a = singmasterMath.Pascal(diagonal=i, n=b['result'])
            while product(a.integers) < target:
                a.incrementIndex()
            data['results'].append({'diagonal': i,
                                    'n': a.n,
                                    'match': (product(a.integers) == target),
                                    'bin_search_inc': b['inc_count'],
                                    'bin_search_mid': b['mid_count'],
                                    'run_time': b['time']})
            starting_points[i] = a.n - 1
            running_time += b['time']
            try:
                status_queue.put({'center': center, 'progress': (i-2.0)/(center-2.0)}, False)
            except Queue.Full:
                pass
        data['center'].update({'run_time': running_time})
        pascalDB.uploadResult(data)
        center += 1
        # print(center)

# Control variables
active_search = {'on': False, 'thread': ProcessThread(3003, search)}


@app.route('/')
def main():
    return render_template('index.html', title='Pascal')


@app.route('/reset')
def data_reset():
    if not active_search['on']:
        pascalDB.recreateTables()
    return 'reset: '+time.asctime()


@app.route('/reload')
def data_reload():
    if not active_search['on']:
        pascalDB.resumeSearch()
    return '0'


@app.route('/start')
def start_search():
    active_search.update({'on': True})
    try:
        active_search['thread'].start()
    except RuntimeError:
        active_search['thread'] = ProcessThread(9009, search)
        active_search['thread'].start()
    active_search['thread'].on = True
    return 'start: '+time.asctime()


@app.route('/stop')
def stop_search():
    status_queue.put({'data': 'close', 'event': 'close'})
    active_search.update({'on': False})
    active_search['thread'].close()
    return 'stop: '+time.asctime()


@app.route('/status_stream')
def status_stream():
    def gen():
        try:
            while active_search['on'] and not status_queue.empty():
                status = status_queue.get()
                ev = ServerSentEvent(str(json.dumps(status)), event=status.get('event', None))
                yield ev.encode()
        except GeneratorExit:
            print('generator error, huh?')
    return Response(gen(), mimetype='text/event-stream')

if __name__ == "__main__":
    app.debug = True
    app.run(threaded=True, use_reloader=False)


@atexit.register
def goodbye():
    print('exiting')
    # pascal_db.print_results()
    if not pascalDB.db.is_closed():
        pascalDB.db.close()
