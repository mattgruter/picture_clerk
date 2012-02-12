"""
Created on 2011/08/09

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""

import logging

log = logging.getLogger('pic.repo')

class PictureAlreadyIndexedError(Exception):
    def __init__(self, pic):
        Exception.__init__(self, pic)
        self.pic = pic
    def __str__(self):
        return "%s already in index" % self.pic
    def __repr__(self):
        return "PictureAlreadyIndexedError(%s)" % self.pic

class PictureNotIndexedError(KeyError):
    def __init__(self, pic):
        KeyError.__init__(self, pic)
        self.pic = pic
    def __str__(self):
        return "%s not in index" % self.pic
    def __repr__(self):
        return "PictureNotIndexedError(%s)" % self.pic


class Repo(object):
    """
    PictureClerk repository
    """
    def __init__(self, index=dict()):
        self.index = index

    def __repr__(self):
        return "Repo(%s)" % self.index

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        return self.index == other.index

    def __ne__(self, other):
        return not self.__eq__(other)

    def add_picture(self, pic):
        key = pic.filename
        if key in self.index:
            raise PictureAlreadyIndexedError(pic.filename)
        log.info("Adding %s.", pic.filename)
        self.index[key] = pic

    def add_pictures(self, pics):
        for pic in pics:
            try:
                self.add_picture(pic)
            except PictureAlreadyIndexedError as paie:
                log.info("%s already in index", paie.pic)

    def get_pictures_iter(self):
        return self.index.itervalues()

    def get_pictures(self):
        return list(self.get_pictures_iter())

    def get_picture_by_filename(self, filename):
        log.info("Fetching %s from repository.", filename)
        try:
            return self.index[filename]
        except KeyError:
            raise PictureNotIndexedError(filename)

    def update_picture(self, pic):
        key = pic.filename
        if key not in self.index:
            raise PictureNotIndexedError(pic.filename)
        log.info("Updating %s.", pic.filename)
        self.index[key] = pic
