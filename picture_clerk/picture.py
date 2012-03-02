"""picture.py

PictureClerk - The little helper for your picture workflow.
This file contains the Picture class
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2008/11/18 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"


import hashlib
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

    def _str_sidecars(self):
        rtn = str()
        for s in self._sidecars:
            rtn += ('\n   %s: %s' % (s.content_type, s.path))
        return rtn

    def _str_metadata(self):
        rtn = str()
        for k, v in sorted(self.metadata.iteritems()):
            rtn += ('\n   %s: %s' % (k, v))
        return rtn

    def __str__(self):
        rtn = self.filename
        if self.metadata:
            rtn += ('\n  Metadata:')
            rtn += self._str_metadata()
        if self._sidecars:
            rtn += ('\n  Sidecar files:')
            rtn += self._str_sidecars()
        return rtn

    def __repr__(self):
        return "Picture('%s')" % self.filename

    def __eq__(self, o):
        if isinstance(o, Picture):
            return self.filename == o.filename
        return False

    def __ne__(self, o):
        return not self == o

    def __lt__(self, o):
        return self.filename < o.filename

    def __le__(self, o):
        return self.filename <= o.filename

    def __gt__(self, o):
        return self.filename > o.filename

    def __ge__(self, o):
        return self.filename >= o.filename

    def get_filenames(self):
        return [self.filename] + [sidecar.path for sidecar in self._sidecars]

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

    # FIXME: rename to get_sidecars
    def list_sidecars(self):
        return self._sidecars

    def get_sidecar_filenames(self):
        return [sidecar.path for sidecar in self.list_sidecars()]

    def get_thumbnails(self):
        return [sidecar for sidecar in self.list_sidecars()
                    if sidecar.content_type.lower() == "thumbnail"]

    def get_thumbnail_filenames(self):
        return [thumbnail.path for thumbnail in self.get_thumbnails()]


class Sidecar(object):
    """
    A Sidecar object holds the path and the type of content of a sidecar file.
    In addition it stores a reference to the picture object it is associated to.
    
    Constructor arguments:
        path (string)           :   path of sidecar file
        content_type (string)   :   content type (e.g. checksum, thumbnail, xmp, ...)
    """
    def __init__(self, path, content_type):
        self.path = path
        self.content_type = content_type
        self.picture = None

    def __str__(self):
        return '%s: %s' % (self.content_type, self.path)


#class Thumbnail(Sidecar):
#    """
#    Thumbnail object
#    
#    Constructor arguments:
#        path (string)   :   path of sidecar file
#    """
#    def __init__(self, path):
#        Sidecar.__init__(self, path, content_type="Thumbnail") 

def get_sha1(buf):
    return hashlib.sha1(buf).hexdigest()
