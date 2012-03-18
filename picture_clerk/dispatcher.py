"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import threading
import time


class Dispatcher(threading.Thread):
    """
    The dispatcher thread activates and holds the worker threads depending
    on waiting jobs in the input queue.
    """

    # FIXME: dispatcher should maybe also create and start worker threads?
    def __init__(self, pool):
        threading.Thread.__init__(self)
        self.pool = pool
        self.workersOnHold = True

    def _activate_workers(self):
        self.pool.wakeSignal.set()
#        for worker in self.pool.workers:
#            worker.hold = False
        self.workersOnHold = False

    def _hold_workers(self):
        self.pool.wakeSignal.clear()
#        for worker in self.pool.workers:
#            worker.hold = True
        self.workersOnHold = True

    def _stop_workers(self):
        # let workers finish the jobs they are working on and wait for them
        # TODO: this method should probably be called _finish_workers or some-
        #       thing to make it clear that workers are not directly terminated
        if self.workersOnHold: self._activate_workers()
        for worker in self.pool.workers:
            worker.join()

    def run(self):
        # hold all workers (shouldn't be necessary if workers were just created)
        self._hold_workers()
        while self.pool.isactive:
            if self.pool.input.qsize == 0:
                # No work in input queues. Hold workers
                if not self.workersOnHold: self._hold_workers()
            else:
                if self.workersOnHold: self._activate_workers()
                else: self.pool.progress = self.pool.output.qsize()
            # only run once a second
            time.sleep(1)
        else:
            self._stop_workers()


# Unit test       
def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

