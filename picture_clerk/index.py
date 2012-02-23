"""
Created on 2011/08/09

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""

import collections
import cPickle as pickle
import logging


log = logging.getLogger('pic.index')

class PictureAlreadyIndexedError(Exception):
    def __init__(self, pic):
        Exception.__init__(self, pic)
        self.pic = pic
    def __str__(self):
        return "%s already in index" % self.pic
    def __repr__(self):
        return "PictureAlreadyIndexedError(%s)" % self.pic

class IndexParsingError(Exception):
    def __init__(self, exp):
        Exception.__init__(self)
        self.orig_exp = exp
    def __str__(self):
        return "Error parsing index: %s" % str(self.orig_exp)


class PictureIndex(collections.MutableMapping):
    """
    PictureClerk repository
    """
    def __init__(self, d=None):
        if not d:
            d = dict()
        self._index = d

    def __repr__(self):
        return "PictureIndex(%s)" % self._index

    def __str__(self):
        return repr(self)

    def __getitem__(self, key):
        return self._index[key]

    def __setitem__(self, key, value):
        self._index[key] = value

    def __delitem__(self, key):
        del self._index[key]

    def __len__(self):
        return len(self._index)

    def __iter__(self):
        yield self._index

    def __contains__(self, key):
        return key in self._index

    def __eq__(self, o):
        if isinstance(o, PictureIndex):
            return self._index == o._index
        else:
            return False

    def __ne__(self, o):
        return not self == o

    def add(self, pic):
        """Add supplied pic to index. Raises PictureAlreadyIndexedError"""
        key = pic.filename
        if key in self._index:
            raise PictureAlreadyIndexedError(pic.filename)
        log.info("Adding %s.", pic.filename)
        self._index[key] = pic

    def add_many(self, pics):
        """Add list of pictures to index."""
        for pic in pics:
            self.add(pic)


    def iterpics(self):
        """Return iterator over all pictures."""
        return self._index.itervalues()

    def pics(self):
        """Return list over all pictures sorted by filename."""
        return sorted(self.iterpics())

    def replace(self, pic):
        """Update index with pic. Raise KeyError if pic not already in index."""
        key = pic.filename
        if key not in self._index:
            raise KeyError(pic.filename)
        log.info("Replacing %s.", pic.filename)
        self._index[key] = pic

    def read(self, fh):
        """Load picture _index from supplied file handle.
        
        Arguments:
        fh -- readable file handle pointing_indexndex file
        
        Raises:
        IndexParsingError_indexndex can not be unpickled
        
        """
        try:
            self._index = pickle.load(fh)
        except (pickle.UnpicklingError, EOFError, KeyError) as e:
            raise IndexParsingError(e)

    def write(self, fh):
        """Dump picture _index to supplied file handle.
        
        Arguments:
        fh -- writable file handle

        """
        pickle.dump(self._index, fh)
