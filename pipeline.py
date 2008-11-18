"""pipeline.py

PictureClerk - The little helper for your picture workflow.
This file contains the Pipeline class
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2008/11/18 $"
__copyright__ = "Copyright (c) 2007 Matthias Grueter"
__license__ = "GPL"

import Queue

from worker import Worker, WorkerType


# TODO: unit tests
# TODO: implement some sort of dispatcher to dynamically create or kill threads
#       in each stage to optimize performance (e.g. workers are only started if
#       something is in its input queue, number of workers is adapted according
#       to workload and worker performance.)
class Pipeline():
    """Pipeline is the container for jobs that have to be executed in sequence.
    """
    
    def __init__(self, name='UnamedPipeline', workers)
        self.name = name
        self.workers = workers
        # append a default finalizer Worker if non was given
#        if self.workers[-1].type != worker_types.FINALIZER
#            workers.append = Worker.Worker()
        self.num_workers
        # The input queue for the pipeline.
        self.queue = Queue.Queue()
        # Create a queue for each worker's output as hand-off points between them (buffers)
        self.handoff_queues = [Queue.Queue() for i in range(1, self.num_workers-1)]
        # Assign each worker its input and output queues
        self.workers[1].set_input_queue(self.queue)
        [self.workers[i+1].set_input_queue(self.handoff_queue(i)) for i in range(1, self.num_workers-1)]
        [self.workers[i].set_output_queue(self.handoff_queue(i)) for i in range(1, self.num_workers-1)]
        self.workers[-1].set_output_queue(None)
        self.isactive = False
        
    def put(self, job)
        """Put a Job object into the pipeline"""
        
        self.queue.put(job)
        
    def get_progress(self)
        """Returns a list of the number of jobs in each queue"""
        
        return [queue.qsize() for queue in self.handoff_queues]
    
    def start(self, timeout)
        """Start all workers"""
        
        [worker.start() for queue in self.workers]
        self.isactive = True
        
    def pause(self)
        """Stops all workers without flushing the buffers"""
        # FIXME: worker should check if its pipelines isactive is True or not
        self.isactive = False
        [worker.join() for queue in self.workers]

        
    def stop(self)
        """Stops all workers and flushes the queues"""
        # FIXME: worker should check if its pipelines isactive is True or not
        self.isactive = False
        [worker.join() for queue in self.workers]
        # FIXME: flush queues
        
    def abort(self)
        """Immediately terminate all worker threads and flush queues"""
        # FIXME: Is it possible to kill threads?
        print('Aborting is not implemented yet. Stopping instead.')
        self.stop()  
        
    

# Unit test       
def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
