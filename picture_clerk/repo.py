"""
Created on 2011/08/09

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""

class PictureAlreadyIndexedError(Exception):
    pass

class PictureNotIndexedError(KeyError):
    pass


class Repo(object):
    """
    PictureClerk repository
    """
    def __init__(self, index=dict()):
        self.index = index
        self.config = None
        
    def __repr__(self):
        return "Repo(%s, %s)" % (self.config, self.index)
    
    def __str__(self):
        return repr(self)
    
    def __eq__(self, other):
        return self.index == other.index
        
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def add_picture(self, pic):
        key = pic.filename
        if key in self.index:
            raise PictureAlreadyIndexedError()
        self.index[key] = pic
        
    def get_picture_by_filename(self, filename):
        try:
            return self.index[filename]
        except KeyError:
            raise PictureNotIndexedError()
    
    def update_picture(self, pic):
        key = pic.filename
        if key not in self.index:
            raise PictureNotIndexedError()
        self.index[key] = pic 