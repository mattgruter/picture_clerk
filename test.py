import Queue

from job import *
from worker import *
from stage import *

inbuff = Queue.Queue()
outbuff = Queue.Queue()

j = Job('sleep', [ '3' ], './', 'Sleeping for 3s')
for i in range(12):
    inbuff.put(j)
    
s = Stage('stage', GenericWorker, 3, 'pipeline', inbuff, outbuff, 1)


