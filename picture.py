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
        filename (string)       :   filename of the picture file
    """
    def __init__(self, filename):
        # TODO: Maybe use descriptors for this
        # TODO: Maybe test if two pictures are the same file using os.path.samefile
        # FIXME: filename checking shouldn't be done here. for all Picture
        #        object cares it doesn't matter if the file actually exists.
#        assert os.path.isfile(filename), "invalid path: %s" % filename
        self.filename = filename
        # ensure that filename has no directory component
        assert not os.path.dirname(filename) and os.path.dirname(filename) != '.', \
            "path has directory component: %s" % filename
        # file basename and extension (e.g. DSC_9352 and NEF)
        # FIXME: ensure that these are always updated when path changes and make
        #        read-only
        # FIXME: or lazy evalution: execute split() when attribute is accessed.
        # FIXME: note: self.extension also includes the dot (e.g. ".NEF")
        (self.basename, self.extension) = os.path.splitext(self.filename)
        # FIXME: extract file type from given filename
        self.filetype = PictureFileType.RAW
        # checksum
        # TODO: type of checksum (CRC32, MD5, SHA1, SHA256, etc.) should also be saved
        self.checksum = None
        # sidecar files
        self._sidecars = set([])
        # metadata
        self.metadata = dict()
        # history
        self.history = []
                    
    def __str__(self):
        rtn = self.filename
        for s in self._sidecars:
            rtn += ('\n  %s: %s' % (s.content_type, s.filename))
        return rtn
        
    def __cmp__(self, other):
        return cmp(self.filename, other.filename)
               
    def get_filenames(self):
        return [self.filename] + [sidecar.filename for sidecar in self._sidecars]
        
    def add_sidecar(self, filename, content_type):
        # TODO: Maybe use descriptors for this
        sidecar = Sidecar(filename, content_type)
        sidecar.picture = self
        self._sidecars.add(sidecar)
        # if sidecar is a thumbnail, replace the existing thumbnail with this one.
        if content_type == "Thumbnail":
            self.thumbnail = filename
        
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
        filename (string)       :   filename of sidecar file
        content_type (string)   :   content type (e.g. checksum, thumbnail, xmp, ...)
    """
    def __init__(self, filename, content_type):
        # FIXME: filename checking shouldn't be done here. for all Picture
        #        object cares it doesn't matter if the file actually exists.
#        assert os.path.isfile(filename), "invalid path: %s" % filename
        self.filename = filename
        # ensure that filename has no directory component
        assert not os.path.dirname(filename) and os.path.dirname(filename) != '.', \
            "path has directory component: %s" % filename
        self.content_type = content_type
        self.picture = None
        
    def __str__(self):
        return '%s: %s' % (self.content_type, self.filename)
        

#class Thumbnail(Sidecar):
#    """
#    Thumbnail object
#    
#    Constructor arguments:
#        filename (string)       :   filename of sidecar file
#    """
#    def __init__(self, filename):
#        Sidecar.__init__(self, filename, content_type="Thumbnail")      
