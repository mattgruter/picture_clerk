"""pipeline.py

PictureClerk - The little helper for your picture workflow.
This file contains the Pipeline class
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2008/11/18 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"

import Queue

import config
from stage import Stage


#class PipelineState():
#    EMPTY = 0       # all stages and buffers are empty
#    ACTIVE  = 5     # one or more stages are active and one or more buffers are not empty
#    PAUSED = 4      # all stages are paused and one or more buffers are not empty
#    IDLE = 1        # all stages are paused and all buffers are empty
#    FINISHING = 2   # one or more stages are active and all buffers are empty
#    CLOGGED = 3     # one or more stage with non-empty buffer is unstaffed    
    
    

# TODO: unit tests
# TODO: implement some sort of dispatcher to dynamically create or kill threads
#       in each stage to optimize performance (e.g. workers are only started if
#       something is in its input queue, number of workers is adapted according
#       to workload and worker performance.)
class Pipeline():
    """
    Pipeline defines the stages of the workflow.
    """
    
    def __init__(self, name, recipe):
        self.name = name
        # recipe defining the sequence of jobs to be performed
        self.recipe = recipe
        self.num_stages = self.recipe.num_stages
        self.num_stageworkers = config.DEFAULT_NUM_STAGEWORKERS
        # Create buffers before and after each stage (hand-off points)
        self.buffers = [Queue.Queue() for i in range(self.num_stages+1)]
        # The input buffer of the pipeline.
        self.input = self.buffers[0]
        # The output buffer of the pipeline
        self.output = self.buffers[-1]
        # Create stages and connect them to the buffers
        self.stages = [Stage(name=self.recipe.stage_names[i],
                             WorkerClass=self.recipe.stage_types[i],
                             num_workers=self.num_stageworkers,
                             pipeline=self,
                             in_buffer=self.buffers[i],
                             out_buffer=self.buffers[i+1],
                             seq_number=i) for i in range(self.num_stages)]
        # jobnr is a simple counter of jobs that have been or still are processed
        self.jobnr = 0
        # Set state to inactive
        self.isactive = False

        
    def put(self, picture):
        """Put a Job object into the pipeline"""
        # FIXME: make access to self.jobnr thread-safe (locking)
        self.jobnr += 1
        self.input.put((picture, self.jobnr))
        
    def get_progress(self):
        """Returns a list of the number of jobs in each queue"""
        return [b.qsize() for b in self.buffers]
    
    def start(self):
        """Start all workers"""
        [s.start() for s in self.stages]
        self.isactive = True

    def flush(self):
        """Flushes all queues"""
        # TODO: How to flush queues?
        raise(NotImplementedError('Queue flushing'))
        
    def stop(self):
        """Stops all workers"""
        [s.stop() for s in self.stages]
        self.isactive = False
        
    def abort(self):
        """Immediately terminate all worker threads and flush queues"""
        # FIXME: Is it possible to kill threads?
#        raise(NotImplementedError('Aborting pipline'))
        print('Aborting is not implemented yet. Stopping instead.')
        self.stop()
        self.flush()
    

# Unit test       
def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

