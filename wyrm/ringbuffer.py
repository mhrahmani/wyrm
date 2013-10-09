#!/usr/bin/env python

import time

import numpy as np
from matplotlib import pyplot as plt


FS = 1000
BUFFER_TIME = 60
CHANNELS = 128


class RingBuffer(object):
    """Circular Buffer implementation.

    This implementation has a guaranteed upper bound for read and write
    operations as well as a constant memory usage, which is the size of
    the maximum length of the buffer in memory.

    Reading and writing will take at most the time it takes to copy a
    continuous chunk of length ``MAXLEN`` in memory. E.g. for the
    extreme case of storing the last 60 seconds of 64bit data, sampled
    with 1kHz and 128 channels (~60MB), reading a full buffer will take
    ~25ms, as well as writing when storing more than than 60 seconds at
    once. Writing will be usually much faster, as one stores usually
    only a few milliseconds of data per run. In that case writing will
    be a fraction of a millisecond.

    """
    def __init__(self, shape):
        """Initialize the Ringbuffer.

        Parameters
        ----------
        shape : (int, int)
            the shape of the data and maximum length of the buffer

        """
        self.shape = shape
        self.data = np.empty(shape)
        self.full = False
        self.idx = 0

    def append(self, data):
        """Append data to the Ringbuffer, overwriting old data if necessary.

        Parameters
        ----------
        data : ndarray

        """
        if len(data) > self.shape[0]:
            data = data[-self.shape[0]:]
        if len(data) == 0:
            return
        if self.idx + len(data) < self.shape[0]:
            self.data[self.idx:self.idx+len(data)] = data
            self.idx += len(data)
        else:
            self.full = True
            l1 = self.shape[0] - self.idx
            l2 = len(data) - l1
            self.data[-l1:] = data[:l1]
            self.data[:l2] = data[l1:]
            self.idx = l2

    def get(self):
        """Get all buffered data.

        Returns
        -------
        data : ndarray

        """
        if self.full:
            return np.concatenate([self.data[self.idx:], self.data[:self.idx]], axis=0)
        else:
            return self.data[:self.idx].copy()


def profile(rb, shape, iterations):
    times = []
    rb.append(np.empty(rb.shape))
    for i in range(iterations):
        data = np.empty(shape)
        t0 = time.time()
        rb.append(data)
        rb.get()
        times.append(time.time() - t0)
    return np.array(times) * 1000

def pretty_print(times):
    print("Min: {min:7.3f}, Max: {max:7.3f}, Mean: {mean:7.3f}, Std: {std:7.3f}".format(
        min=np.min(times), max=np.max(times), mean=np.mean(times), std=np.std(times)))


def main():
    c = ['#d33682', '#268bd2', '#859900', '#073642']
    for i, rb_cls in enumerate([RingBuffer]):
        print "Testing {cls}".format(cls=rb_cls)
        # test big chunks
        rb = rb_cls((FS * BUFFER_TIME, CHANNELS))
        times = profile(rb, (FS * BUFFER_TIME, CHANNELS), 100)
        plt.plot(times, '-', label='full', color=c[i])
        pretty_print(times)
        # full -1
        rb = rb_cls((FS * BUFFER_TIME -1, CHANNELS))
        times = profile(rb, (FS * BUFFER_TIME, CHANNELS), 100)
        plt.plot(times, '--', label='full-1', color=c[i])
        pretty_print(times)
         # small chunks
        rb = rb_cls((FS * BUFFER_TIME, CHANNELS))
        times = profile(rb, (FS * BUFFER_TIME / 10, CHANNELS), 100)
        plt.plot(times, '*', label='/10', color=c[i])
        pretty_print(times)
        # small chunks
        rb = rb_cls((FS * BUFFER_TIME, CHANNELS))
        times = profile(rb, (FS * BUFFER_TIME / 100, CHANNELS), 100)
        plt.plot(times, 'o', label='/100', color=c[i])
        pretty_print(times)
        # small chunks
        rb = rb_cls((FS * BUFFER_TIME, CHANNELS))
        times = profile(rb, (FS * BUFFER_TIME / 1000, CHANNELS), 100)
        plt.plot(times, 'x', label='/1000', color=c[i])
        pretty_print(times)
        rb = rb_cls((FS * BUFFER_TIME, CHANNELS))
        times = profile(rb, (1, CHANNELS), 10000)
        plt.plot(times, '.', label='1', color=c[i])
        pretty_print(times)
    plt.legend()
    plt.grid()
    plt.show()


if __name__ == '__main__':
    main()
