import Queue

from job import *
from worker import *
from stage import *
from picture import *

inbuf = Queue.Queue()
outbuf = Queue.Queue()

class Pool():
    isactive = True
pool = Pool()

pic = Picture('test/DSC_9285.NEF')
pic2 = Picture('test/DSC_9290.NEF')

inbuf.put((pic, 1))
inbuf.put((pic2, 2))

#j = Job('sleep', [ '3' ], './', 'Sleeping for 3s')
#for i in range(12):
#    inbuff.put(j)
    
#s = Stage('stage', GenericWorker, 3, 'pipeline', inbuff, outbuff, 1)

w = DCRawThumbWorker('worker', pool, inbuf, outbuf, './')



