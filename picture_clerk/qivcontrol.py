#!/usr/bin/env python
from __future__ import with_statement
"""qivcontrol.py

PictureClerk - The little helper for your picture workflow.
QIV control thread
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2008/06/15 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"

import threading
import subprocess
import os
import time
import fnmatch

class QivController(threading.Thread):
    def __init__(self, bin, opts, pics, path):
        threading.Thread.__init__(self)
        self.bin = bin
        self.opts = opts
        self.pics = pics
        self.path = path
        # Trash monitor thread
        self._trashMonitor = QivTrashMonitor(self.path)
        
    def run(self):
        self._trashMonitor.start()
        command = [self.bin] + self.opts + sorted(os.path.join(self.path, pic.thumbnail) for pic in self.pics)
        try:
            viewerProcess = subprocess.Popen(command, shell=False)
            retcode = viewerProcess.wait()
            if retcode < 0:
                print >>sys.stderr, "Child was terminated by signal", -retcode
        except OSError, e:
            print >>sys.stderr, "Execution failed:", e
        self._trashMonitor.stop()
        self._trashMonitor.join()
        
    def getTrashContent(self):
        return self._trashMonitor.getContent()
        
    def getTrashPath(self):
        return self._trashMonitor.path
            
            
class QivTrashMonitor(threading.Thread):
    def __init__(self, path):
        threading.Thread.__init__(self)
        self.path = os.path.join(path, '.qiv-trash')
        self.content = set([])
        self.contentLock = threading.Lock()
        
    def run(self):
        self._stop = False
        while True:
            if self._stop:
                break
            # wait 5 seconds
            time.sleep(1)
            # TODO: use inotify?
            try:
                newContent = os.listdir(self.path)
            except OSError:
                # don't care if qiv-trash directory does not exist yet
                newContent = set([])
            # TODO: only look for files that are pic thumbnails
            newContent = set(fnmatch.filter(newContent, '*.thumb.jpg'))
            
            additions = newContent - self.content
            restorations = self.content - newContent
            with self.contentLock:
                self.content = newContent
            if restorations:
                for restoration in restorations:
                    print '%s restored.' % restoration
            if additions:
                for addition in additions:
                    print '%s deleted.' % addition
                
    def stop(self):
        self._stop = True
        
    def getContent(self):
        with self.contentLock:
            return self.content
        
