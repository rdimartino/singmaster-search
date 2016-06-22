from __future__ import division
from math import factorial
import time


def product(integers):
    value = 1
    for i in integers:
        value *= i
    return value


def combin(n, r):
    return factorial(n) // factorial(r) // factorial(n - r)


def pascalTriCenter(x):
    return combin(2 * x, x)


def midpoint(a, b):
    return int((a + b) // 2)


class Pascal:

    def __init__(self, diagonal=0, n=0):
        try:
            self.diagonal = int(diagonal)
        except ValueError:
            self.diagonal = 0

        try:
            self.n = int(n)
        except ValueError:
            self.n = 0

        self.integers = list(range(n + 1, n + diagonal + 1))

    def value(self):
        return product(self.integers) // factorial(self.diagonal)

    def check(self):
        val1 = self.value()
        val2 = combin(self.diagonal + self.n, self.diagonal)
        return val1, val2, val1 == val2

    def incrementIndex(self):
        self.n += 1
        if self.diagonal == 0:
            self.integers = [1]
        elif self.diagonal == 1:
            self.integers = [self.n + 1]
        else:
            self.integers.pop(0)
            self.integers.append(self.integers[-1] + 1)

    def decrementIndex(self):
        self.n -= 1
        if self.diagonal == 0:
            self.integers = [1]
        elif self.diagonal == 1:
            self.integers = [self.n + 1]
        else:
            self.integers.pop()
            self.integers.insert(0, self.integers[0] - 1)


def binarySearch(start, target, function):
    startTime = time.time()
    f = function
    low, high = start, start * 2
    expandSearchCount = 0
    narrowSearchCount = 0
    while f(high) < target:
        low = high
        high *= 2
        expandSearchCount += 1
    while 3 < high - low:
        mid = midpoint(low, high)
        narrowSearchCount += 1
        if f(mid) <= target:
            low = mid
        elif f(mid) > target:
            high = mid
        else:
            break
    return {'result': low, 'expandCount': expandSearchCount, 'narrowCount': narrowSearchCount, 'searchTime': (time.time() - startTime)}
