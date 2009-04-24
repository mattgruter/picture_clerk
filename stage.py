"""stage.py

PictureClerk - The little helper for your picture workflow.
This file contains Stage class
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2008/11/18 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"


import Queue

import config


#class StageState():
#    INACTIVE = 0   # stage is empty, no workers created
#    PAUSED = 1  # workers are idle
#    ACTIVE = 2  # workers are busy


class Stage():
    """
    A stage is a segment in a pipeline defining the type of workers it employs.
    """

    def __init__(self, name, WorkerClass, num_workers, in_buffer,
                 out_buffer, seq_number, pipeline, path, logdir):
        self.name = name
        self.WorkerClass = WorkerClass
        self.num_workers = num_workers
        self.pipeline = pipeline
        self.input = in_buffer
        self.output = out_buffer
        self.seq_number = seq_number
        self.worker_environ = dict(pool=self, path=path, logdir=logdir)
        self.isactive = False

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
        self.isactive = True
        # create worker threads
        self.workers = self._create_worker(self.num_workers)
        # start threads
        [worker.start() for worker in self.workers]


    def stop(self):
        """
        Block until all workers have finished current job. Input queue does not
        have to be empty.
        """
        self.isactive = False
        [worker.join() for worker in self.workers]
        
        
    def join(self):
        """
        Block until the input queue is empty.    
        """
        self.input.join()
        self.isactive = False
        
        
# Unit test       
def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

