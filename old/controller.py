import app
import thread_manager
import singmasterMath
import pascalDB

import math
from singmasterMath import product

website = thread_manager.ProcessThread('web', app.gogogo)
data_based = thread_manager.DBThread(1, thread_manager.workQueue, pascalDB.uploadResult)


def main():
    # Begin Flask app
    website.start()
    data_based.start()
    # Loop
    while True:
        centers = 200
        center = 3
        starting_points = list(range(centers + 1))
        while app.active_search['on'] and center < centers:
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
                app.status_queue.put({'center': center, 'progress': (i-2.0)/(center-2.0)})
                # print('Searching for center:{:,}'.format(center), 'Progress: {:.2%}'.format((i-2.0)/(center-2.0)))
            data['center'].update({'run_time': running_time})
            pascalDB.uploadResult(data)
            thread_manager.queueLock.acquire()
            thread_manager.workQueue.put(data)
            thread_manager.queueLock.release()
            center += 1
            print(center)
        # pascal_db.print_results()


if __name__ == '__main__':
    main()


