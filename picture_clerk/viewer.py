"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL
"""
import subprocess
import logging
import os


log = logging.getLogger('pic.viewer')

class Viewer(object):

    def __init__(self, prog):
        self.prog = prog

    def show(self, pics):
        log.info("Starting viewer '%s'" % self.prog)

        thumb2pic = {pic.get_thumbnail_filenames()[0]: list()
                         for pic in pics}
        for pic in pics:
            thumb2pic[pic.get_thumbnail_filenames()[0]].append(pic)

        cmd = self.prog.split() + thumb2pic.keys()
        log.debug("Executing command line '%s'" % cmd)
        try:
            subprocess.check_call(cmd)
            log.debug("'%s' terminated without errors" % self.prog)
        except subprocess.CalledProcessError, e:
            log.exception("Viewer terminated by signal %s:" % e.returncode)
            return []
        except OSError, e:
            log.exception("Exception raised during execution:")
            return []

        # return list over missing pictures (i.e. pics deleted by viewer)
        return [pic
                for k, v in thumb2pic.iteritems() if not os.path.exists(k)
                for pic in v]
