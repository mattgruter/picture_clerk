import os
import fnmatch

#import Queue

from recipe import *
#from job import *
from worker import *
#from stage import *
from pipeline import *
from picture import *


path = '../test_album'
dirlist = os.listdir(path)
files = fnmatch.filter(dirlist, "*.NEF")
#files = [ os.path.join(path, f) for f in files ]
pics = [ Picture(f) for f in files ]

#inbuf = Queue.Queue()
#outbuf = Queue.Queue()

#inbuf.put((pic, 1))
#inbuf.put((pic2, 2))

#class Pool():
#    isactive = True
#pool = Pool()
    
#dw = DCRawThumbWorker(pool, inbuf, outbuf, './')
#ew = Exiv2MetadataWorker(pool, inbuf, outbuf, './')
    
#s = Stage('stage', DCRawThumbWorker, 3, 'pipeline', inbuf, outbuf, 1)

instructions = [Exiv2MetadataWorker, DCRawThumbWorker, HashDigestWorker, AutorotWorker]
recipe = Recipe(instructions)

pl = Pipeline('TestPipe', recipe)

for pic in pics:
    pl.put(pic)
        
print pl.get_progress()








