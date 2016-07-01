from flask import Flask, Response, render_template, jsonify, request
from datetime import date, datetime

import threading
import Queue
import atexit
import json

import singmasterMath as math
import pascalDB as db


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
    def __init__(self, thread_id, function, on=True):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.function = function
        self.on = on

    def run(self):
        pushStreamEvent(data={'message': 'Process Thread {!s} has started'.format(self.thread_id),
                          'header': 'control',
                          'flag': db.SUCCESS_FLAG},
                        log=True, event='message', blocking=True)
        while self.on:
            self.function()
        pushStreamEvent(data={'message': 'Process Thread {!s} has terminated'.format(self.thread_id),
                          'header': 'control',
                          'flag': db.WARNING_FLAG},
                        log=True, event='message', blocking=True)

    def close(self):
        pushStreamEvent(data={'message': 'Process Thread {!s} is stopping...'.format(self.thread_id),
                              'header': 'control',
                              'flag': db.WARNING_FLAG},
                        log=True, event='message', blocking=True)
        self.on = False


def pushStreamEvent(data, log=True, event='message', blocking=True):
    if 'ts' not in data:
        data.update({'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
    if log:
        db.logLine(message=data['message'], header=data['header'], flag=data['flag'])
        #data.update({'logline': '[ {!s} ] == {!s}'.format(data['ts'], data['msg'])})
    for sub in subscriptions[:]:
        try:
            data.update({'event': event})
            sub.put(data, blocking)
        except Queue.Full: # Or maybe use flask signals
            pass

app = Flask(__name__)

# Control variables
streamQueueLock = threading.Lock()
steamQueue = Queue.Queue(0)
process = {'thread': None,
           'initial': None,
           'on': False,
           'threadCount': 1000}
progress = {'center': 0, 'p': 0.0}
subscriptions = []
buttons = {'start-btn': {'state': True},
           'stop-btn': {'state': False},
           'reset-btn': {'state': False}}


def searchProcess():
    # main process code
    # centers = 200
    if process['initial']:
        centerIndex= process['initial']['lastCenterIndex']
        searchStartIndices = process['initial']['searchStartIndices']
    else:
        centerIndex = 3
        searchStartIndices = list(range(centerIndex + 1))
    while process['on']:  # and center < centers:
        pushStreamEvent(data={'message': 'Searching for {!s}{!s} center ...'.format(centerIndex,ordinal(centerIndex)),
                          'header': 'info',
                          'flag': db.INFO_FLAG},
                        log=True, event='message', blocking=True)
        centerValue = math.pascalTriCenter(centerIndex)
        data = {'center': {'diagonal': centerIndex, 'value': centerValue, 'matchCount': 0},
                'results': []}
        centerSearchTime = 0
        for diagonalIndex in range(2, centerIndex + 1):
            target = centerValue * math.factorial(diagonalIndex)
            try:
                searchStartIndices[diagonalIndex]
            except IndexError:
                searchStartIndices.append(diagonalIndex)
            binarySearchResults = math.binarySearch(searchStartIndices[diagonalIndex],
                                           target,
                                           lambda x: math.product(math.Pascal(diagonalIndex, x).integers))
            incrementSearch = math.Pascal(diagonal=diagonalIndex, n=binarySearchResults['result'])
            while math.product(incrementSearch.integers) < target:
                incrementSearch.incrementIndex()
            matchFound = (math.product(incrementSearch.integers) == target)
            if matchFound:
                trivialResult = (incrementSearch.n == centerIndex)
                pushStreamEvent(data={'message': 'Match found! Diagonal: {!s}; Position: {!s}'.format(str(diagonalIndex), str(incrementSearch.n)),
                                  'header': 'info' if trivialResult else 'success',
                                  'flag': db.INFO_FLAG if trivialResult else db.SUCCESS_FLAG}, log=True, event='message', blocking=True)
                data['center']['matchCount'] += 1
            data['results'].append({'diagonal': diagonalIndex,
                                    'index': incrementSearch.n,
                                    'match': matchFound,
                                    'binarySearchExpandCount': binarySearchResults['expandCount'],
                                    'binarySearchNarrowCount': binarySearchResults['narrowCount'],
                                    'searchTime': binarySearchResults['searchTime']})
            searchStartIndices[diagonalIndex] = incrementSearch.n - 1
            centerSearchTime += binarySearchResults['searchTime']
            pushStreamEvent(data={'center': centerIndex,
                              'p': (diagonalIndex-2.0)/(centerIndex-2.0)},
                            log=False, event='progress', blocking=False)
        data['center'].update({'centerSearchTime': centerSearchTime})
        db.uploadResult(data)
        pushStreamEvent(data={'center': centerIndex,
                          'centerSearchTime': centerSearchTime,
                          'matchCount': data['center']['matchCount']},
                        log=False, event='data', blocking=True)
        centerIndex += 1
        progress.update({'center': centerIndex, 'p': 0.0})
    process['initial'] = db.resumeSearch()
    process['on'] = False


def ordinal(n):
    return {1: 'st', 2: 'nd', 3: 'rd'}.get(4 if 10 <= n % 100 < 20 else n % 10, "th")


@app.route('/')
def main():
    return render_template('index.html',
                           title='Singmaster''s Conjecture',
                           year=date.today().year,
                           progress=progress,
                           terminal_text='Loading status terminal...\n',
                           buttons=buttons)


@app.route('/start')
def start():
    buttons.update({'start-btn': {'state': False},
                    'stop-btn': {'state': False},
                    'reset-btn': {'state': False}})
    process['threadCount'] += 1
    process['on'] = True
    process['thread'] = ProcessThread(process['threadCount'], searchProcess)
    process['thread'].start()
    buttonStates = {'start-btn': {'state': False},
                   'stop-btn': {'state': True},
                   'reset-btn': {'state': False}}
    buttons.update(buttonStates)
    return jsonify({'log': 'Starting process',
                    'buttons': buttonStates,
                    'alert': {'title': 'Start: ',
                              'body': 'The search is beginning.',
                              'flag': db.SUCCESS_FLAG}})
                              #'class': 'alert-success'}})


@app.route('/stop')
def stop():
    buttons.update({'start-btn': {'state': False},
                    'stop-btn': {'state': False},
                    'reset-btn': {'state': False}})
    process['on'] = False
    process['thread'].close()
    buttonStates = {'start-btn': {'state': True, 'label': 'Resume'},
                   'stop-btn': {'state': False},
                   'reset-btn': {'state': True}}
    buttons.update(buttonStates)
    return jsonify({'log': 'Stopping process',
                    'buttons': buttonStates,
                    'alert': {'title': 'Stop: ',
                              'body': 'The search has stopped.',
                              'flag': db.WARNING_FLAG}})
                              #'class': 'alert-warning'}})


@app.route('/reset')
def reset():
    buttons.update({'start-btn': {'state': False},
                    'stop-btn': {'state': False},
                    'reset-btn': {'state': False}})
    pushStreamEvent(data={'message': 'Resetting progress', 'header': 'reset', 'flag': db.DANGER_FLAG}, log=True, event='message', blocking=True)
    process['thread'].join()  # Wait for process to terminate
    process['initial'] = None
    db.recreateTables()  # Reset function
    buttonStates = {'start-btn': {'state': True, 'label': 'Start'},
                   'stop-btn': {'state': False},
                   'reset-btn': {'state': False}}
    buttons.update(buttonStates)
    return jsonify({'log': 'Resetting progress',
                    'buttons': buttonStates,
                    'alert': {'title': 'Reset: ',
                              'body': 'The search results have been reset.',
                              'flag': db.DANGER_FLAG}})
                              #'class': 'alert-danger'}})


@app.route('/dataStream')
def dataStream():
    def gen():
        try:
            q = Queue.Queue(5)
            subscriptions.append(q)
            while True:
                status = q.get(True)
                ev = ServerSentEvent(str(json.dumps(status)), event=status.get('event', None))
                yield ev.encode()
        except GeneratorExit:
            subscriptions.remove(q)
    return Response(gen(), mimetype='text/event-stream')


@app.route('/reload')
def reload():
    return jsonify({'logs': db.pullLog(), 'viz': db.pullVizData()})


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'


@app.route('/initalize_test')
def initial():
    return str(process['initial']['lastCenterIndex'])+'--'+str(db.resumeSearch()['lastCenterIndex'])


if __name__ == "__main__":
    app.debug = True
    #db.recreateTables()
    #db.createLog()
    process['initial'] = db.resumeSearch()
    progress.update({'center': process['initial']['lastCenterIndex']})
    app.run(threaded=True, use_reloader=False)

@atexit.register
def goodbye():
    print('Exiting Flask app')
    if process['thread']:
        process['thread'].close()
    db.db.close()