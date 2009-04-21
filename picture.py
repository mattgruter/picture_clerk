"""picture.py

PictureClerk - The little helper for your picture workflow.
This file contains the Picture class
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2008/11/18 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"


import sys
import os.path


class PictureFileType():
    RAW = 0
    JPEG = 1


class Picture(object):
    """
    A Picture object stores the history, metadata, sidecar files and more for a
    picture file.
    
    Constructor arguments:
        path (string)   :   absolute path to the picture file
    """
    def __init__(self, path):
        # TODO: Maybe use descriptors for this
        # TODO: Maybe test if two pictures are the same file using os.path.samefile
        assert os.path.exists(path), "invalid path: %s" % path
        self.path = os.path.realpath(path)
        # FIXME: what is needed? dir, filename, basename, extension? everything?
        # FIXME: ensure that these are always updated when path changes and make
        #        read-only
        # FIXME: or lazy evalution: execute split() when attribute is accessed.
        # base directory and filename
        (self.dir, self.filename) = os.path.split(self.path)
        # file basename and extension (e.g. DSC_9352 and NEF)
        (self.basename, self.extension) = os.path.splitext(self.filename)
        # FIXME: extract file type from given filename
        self.filetype = PictureFileType.RAW
        # checksum
        # TODO: type of checksum (CRC32, MD5, SHA1, SHA256, etc.) should also be saved
        self.checksum = None
        # sidecar files
        self._sidecars = set([])
        # metadata
        #self.metadata = 
        # history
        self.history = []
                    
    def __str__(self):
        rtn = self.path
        for s in self._sidecars:
            rtn += ('\n  %s: %s' % (s.content_type, s.path))
        return rtn
               
    def get_files(self):
        _sidecar_files = [sidecar.path for sidecar in self._sidecars]
        return [self.path] + _sidecar_files
        
    def add_sidecar(self, path, content_type):
        # TODO: Maybe use descriptors for this
        sidecar = Sidecar(path, content_type)
        sidecar.picture = self
        self._sidecars.add(sidecar)
        # if sidecar is a thumbnail, replace the existing thumbnail with this one.
        if content_type == "Thumbnail":
            self.thumbnail = path
        
    def del_sidecar(self, sidecar):
        self._sidecars.discard(sidecar)
        sidecar.picture = None

    def list_sidecars(self):
        return self._sidecars


class Sidecar(object):
    """
    A Sidecar object holds the path and the type of content of a sidecar file.
    In addition it stores a reference to the picture object it associated to.
    
    Constructor arguments:
        path (string)           :   absolute path to the sidecar file
        content_type (string)   :   content type (e.g. checksum, thumbnail, xmp, ...)
    """
    def __init__(self, path, content_type):
        assert os.path.exists(path), "invalid path: %s" % path
        self.path = os.path.realpath(path)
        # base directory and filename
        (self.dir, self.filename) = os.path.split(self.path)
        self.content_type = content_type
        self.picture = None
        
    def __str__(self):
        return '%s: %s' % (self.content_type, self.path)
        

#class Thumbnail(Sidecar):
#    """
#    Thumbnail object
#    
#    Constructor arguments:
#        path (string)   :   absolute path to the thumbnail file    
#    """
#    def __init__(self, path):
#        Sidecar.__init__(self, path, content_type="Thumbnail")      
