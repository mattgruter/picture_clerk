"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import threading

from dispatcher import Dispatcher


#class StageState():
#    INACTIVE = 0   # stage is empty, no workers created
#    PAUSED = 1  # workers are idle
#    ACTIVE = 2  # workers are busy


class Stage():
    """
    A stage is a segment in a pipeline defining the type of workers it employs.
    """

    def __init__(self, name, WorkerClass, num_workers, in_buffer,
                 out_buffer, seq_number, pipeline, path):
        self.name = name
        self.WorkerClass = WorkerClass
        self.num_workers = num_workers
        self.pipeline = pipeline
        self.input = in_buffer
        self.output = out_buffer
        self.seq_number = seq_number
        self.worker_environ = dict(pool=self, path=path)
        self.isactive = False
        self.progress = 0

    def _create_worker(self, num):
        return [ self.WorkerClass(self.input, self.output, i, **self.worker_environ) for i in range(num) ]

    def add_worker(self):
        new_worker = self._create_worker(1)
        self.workers.append(new_worker)
        self.num_workers += 1

    def remove_worker(self):
        self.workers.pop().join()
        self.num_woker -= 1

    def start(self):
        # Global activity flag
        self.isactive = True
        # Dispatcher-controlled Event worker threads wait for before they start
        self.wakeSignal = threading.Event()
        # create worker threads
        self.workers = self._create_worker(self.num_workers)
        # create dispatcher thread
        self.dispatcher = Dispatcher(self)
        # start threads
        [worker.start() for worker in self.workers]
        # start dispatcher thread
        self.dispatcher.start()

    def stop(self):
        """
        Block until all workers have finished current job. Input queue does not
        have to be empty.
        """
        self.isactive = False
        self.dispatcher.join()

    def join(self):
        """
        Block until the input queue is empty.    
        """
        self.input.join()
        self.isactive = False
        self.dispatcher.join()


# Unit test       
def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

