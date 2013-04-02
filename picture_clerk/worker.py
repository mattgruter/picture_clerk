"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import os
import threading
import Queue
import subprocess
import time
import hashlib
import logging

import config
import repo

import gi
from gi.repository import GExiv2


log = logging.getLogger('pic.worker')


def read_exif_metdata(filename):
    try:
        metadata = GExiv2.Metadata(filename)
    except gi._glib.GError as gerr:
        ioe = IOError()
        # FIXME: errno=2 is only for "file not found" error. other errors
        #        (e.g. "permissions denied") have a different ioe
        #        --> how should GErrors be translated into native Python errors?
        ioe.errno = 2
        ioe.filename = filename
        ioe.strerror = gerr.message
        raise ioe
    else:
        return metadata


#class WorkerState():
#    IDLE = 0    # worker is waiting for jobs
#    BUSY = 1    # worker is processing a job


# TODO: error/execption handling in thread class or outside?
# TODO: unit tests
# TODO: queue_timeout should be controlled by stage or pipleine resp. workertype
# TODO: implement batch workers: they take several pictures from a queue and
#       process in the same run due to better efficiency (typically subprocess
#       workers to circumvent large process starting overhead).
# TODO: _compile_sidecar_path in Worker and _compile_command in Subprocess class
#       should return dictionaries insteaf of tuples
# FIXME: all write to writable picture attributes has to be thread safe
class Worker(threading.Thread):
    """
    Worker is a thread class who works on jobs coming from a queue.

    Constructor arguments:
        inqueue (Queue.Queue)   :   queue from which worker gets his jobs
        outqueue (Queue.Queue)  :   queue into which worker puts finished jobs
        pool                    :   object to which worker belongs (i.e. Stage)
        path (string)           :   path in which the worker is to base its work
    """

    name = 'Worker'

    def __init__(self, inqueue, outqueue, number, pool, path):
        threading.Thread.__init__(self)
        self.inqueue = inqueue
        self.outqueue = outqueue
        self.number = number
        self.pool = pool
        self.path = path
        self.logger = logging.getLogger("%s-%i" % (self.name, self.number))

    def _work(self, picture, jobnr):
        pass    # Override me in derived class
        return False

    def _compile_sidecar_path(self, picture):
        """
        Returns path and content type of generated sidecar file by the worker
        
        This function has to be overriden by derived class if sidecar files are
        generated.
            Arguments passed    : picture object
            Arguments returned  : tuple of strings (path, content_type)
        """

        pass    # Override me in derived class
        return None

    def run(self):
        self.logger.info("Thread %s starting up...", self.name)

        while True:
            self.pool.wakeSignal.wait()
            if not self.pool.isactive:
                self.logger.info("Thread %s terminating. Bye bye.", self.name)
                break
            try:
                # get next queue item, block for WORKER_TIMEOUT seconds if empty
                (picture, jobnr) = self.inqueue.get(True, config.WORKER_TIMEOUT)
            except Queue.Empty:
                pass    # try again

            else:
                self.logger.info("%s loading %s...",
                                 self.name, picture.filename)
                self.logger.info("%s starting job %i", self.name, jobnr)
                if self._work(picture, jobnr):
                    self.logger.info("%s, job %i done", self.name, jobnr)
                    self.outqueue.put((picture, jobnr))
                    self.logger.info("%s done with %s",
                                     self.name, picture.filename)
                    # TODO: make history more useful: exact job performed, timestamp, etc.
                    # FIXME: this has to be thread safe (it is now because a
                    #        every picture is worked on by only one worker but if
                    #        we introduce parallel stages or piplines then we have
                    #        to fix this.)
                    picture.history.append((self.name, time.ctime()))
                    sidecar = self._compile_sidecar_path(picture)
                    if sidecar:
                        picture.add_sidecar(*sidecar)
                    self.inqueue.task_done()
                else:
                    self.logger.error("%s, job %i failed!", self.name, jobnr)


class ThumbWorker(Worker):
    """
    ThumbWorker extracts the thumbnail/preview file from a raw image file with
    help of pyexiv2.
    """

    name = 'ThumbWorker'

    def _work(self, picture, jobnr):

        # create thumbnail subdir if it doesn't already exist
        # FIXME: this isn't thread-safe!
        if not os.path.exists(repo.THUMB_SIDECAR_DIR):
            os.mkdir(repo.THUMB_SIDECAR_DIR)

        try:
            metadata = read_exif_metdata(picture.filename)
        except IOError as ioe:
            self.logger.error("%s (%i): error reading file %s: %s",
                              self.name, jobnr, picture.filename, ioe)
            return False

        # exiv2 sorts previews by dimensions (ascending), we are only
        # interested in the one with the largest dimensions
        props = metadata.get_preview_properties()[-1]
        thumb = metadata.get_preview_image(props)
        thumb_filename = picture.basename + '.thumb' + thumb.get_extension()
        thumb_path = os.path.join(repo.THUMB_SIDECAR_DIR, thumb_filename)
        # save thumbnail to file
        # FIXME: gexiv2 doesn't support copyting metadata. Therefore we need to
        #        first create the thumbnail and save it to file. We then have
        #        to load its metadata with gexiv2 from file, replace its meta-
        #        data with metadata from the original image and then save it
        #        back to the filesystem. So instead of just 1 write, we need
        #        2 write & 1 read.
        try:
            with open(thumb_path, 'wb') as fh:
                fh.write(thumb.get_data())
        except (IOError, OSError) as err:
            self.logger.error("%s (%i): error writing to file %s: %s",
                              self.name, jobnr, thumb_path, err)
            return False

        # TODO: save MIME type
#        thumb_mime_type = thumb.get_mime_type()

        # copy metadata from RAW file to thumbnail
        try:
            thumb_metadata = read_exif_metdata(thumb_path)
        except IOError as ioe:
            self.logger.error("%s (%i): error reading file %s: %s",
                              self.name, jobnr, thumb_path, ioe)
            return False
        # TODO: Ugly way to copy tags.
        #       Patch GExiv2 to support full dict protocol 
        for key in metadata:
            thumb_metadata[key] = metadata[key]

        # modify EXIF tags for the thumbnail
        # tag: Image Compression (JPEG => 7)
        # TODO: Image Compression should be set according to MIME type
        #       (see http://exiv2.org/tags.html)
        # TODO: should more tags be modified?
        thumb_metadata['Exif.Image.Compression'] = "7"
        thumb_metadata.save_file()
        return True

    def _compile_sidecar_path(self, picture):
        # FIXME: thumb might have different extension than "jpg", see above's
        #        use of pyexiv2's preview object: "... + thum.extension"
        #        sidecar_path should be determined in _work method and somehow
        #        returned by it.
        _filename = picture.basename + '.thumb.jpg'
        _path = os.path.join(repo.THUMB_SIDECAR_DIR, _filename)
        _content_type = 'Thumbnail'
        return (_path, _content_type)


class MetadataWorker(Worker):
    """
    MetadataWorker extracts metadata from an image and stores values of
    interest in a dictionary of the picture instance.
    """

    # FIXME: pyexiv2 doesn't seem to be thread safe...

    name = 'MetadataWorker'

    def _work(self, picture, jobnr):
        path = os.path.join(self.path, picture.filename)
        exif_keys = ['Exif.Photo.ExposureTime', 'Exif.Photo.FNumber',
                 'Exif.Photo.ExposureProgram', 'Exif.Photo.ISOSpeedRatings',
                 'Exif.Photo.DateTimeOriginal', 'Exif.Photo.DateTimeDigitized',
                 'Exif.Photo.ExposureBiasValue',
                 'Exif.Photo.MeteringMode', 'Exif.Photo.WhiteBalance',
                 'Exif.Photo.Flash', 'Exif.Photo.LightSource',
                 'Exif.Photo.FocalLength', 'Exif.Photo.FocalLengthIn35mmFilm',
                 'Exif.Image.Make', 'Exif.Image.Model',
                 'Exif.Photo.UserComment']

        try:
            metadata = read_exif_metdata(path)
        except IOError as ioe:
            self.logger.error("%s (%i): error opening file %s: %s",
                  self.name, jobnr, path, ioe)
            return False

        tags = (metadata.get_tag_interpreted_string(key) for key in exif_keys)
        picture.metadata = {key: val for (key, val) in zip(exif_keys, tags)}
        return True


class HashDigestWorker(Worker):
    """
    HashDigestWorker class derived from Worker calculates hash digests of
    picture files.
    """

    name = 'HashDigestWorker'

    def _work(self, picture, jobnr):
        # TODO: catch exceptions of inaccessible files
        with open(os.path.join(self.path, picture.filename), 'rb') as pic:
            buf = pic.read()
        digest = hashlib.sha1(buf).hexdigest()
        picture.checksum = digest
        if repo.SHA1_SIDECAR_ENABLED:
            # create sha1 subdir if it doesn't already exist
            # FIXME: this isn't thread-safe!
            if not os.path.exists(repo.SHA1_SIDECAR_DIR):
                os.mkdir(repo.SHA1_SIDECAR_DIR)

            # write digest to a sidecar file     
            (hashfile_path, contentType) = self._compile_sidecar_path(picture)
            hashfile_path = os.path.join(self.path, hashfile_path)
            try:
                with open(hashfile_path, 'w') as f:
                    f.write(digest + ' *' + picture.filename + '\n')
            except IOError as err:
                self.logger.error("%s (%i): error writing to file %s (%s)",
                                  self.name, jobnr, hashfile_path, err)
                return False

        return True

    def _compile_sidecar_path(self, picture):
        _filename = picture.basename + '.sha1'
        _path = os.path.join(repo.SHA1_SIDECAR_DIR, _filename)
        _contentType = 'Checksum'
        return (_path, _contentType)


class SubprocessWorker(Worker):
    """
    SubprocessWorker class derived from Worker executes external programs.
    """

    name = 'SubprocessWorker'

    def _compile_commands(self, picture):
        """
        Returns command to be executed together with working directory

        This function has to be overriden by derived classes.
            Arguments passed    : picture object
            Arguments returned  : command line (list of strings)
        """

        pass    # Override me in derived class
        return None

    def _work(self, picture, jobnr):
        commands = self._compile_commands(picture)

        for command in commands:
            try:
                self.process = subprocess.Popen(command,
                                                shell=False, cwd=self.path,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.STDOUT)

                while True:
                    line = self.process.stdout.readline()
                    if not line:
                        break
                    self.logger.info(line.strip())

                retcode = self.process.wait()
                if retcode < 0:
                    self.logger.error("%s (%i): '%s' terminated with signal %s",
                                      self.name, jobnr, command, retcode)
                    return False
            except OSError, e:
                self.logger.error("%s (%i): '%s' execution failed: %s",
                                  self.name, jobnr, command, e)
                return False

        return True


class Exiv2XMPSidecarWorker(SubprocessWorker):
    """
    Exiv2XMPSidecarWorker is a subprocess worker that uses Exiv2 to extract
    metadata to a sidecar XMP file.
    """

    name = 'Exiv2XMPSidecarWorker'
    _bin = config.EXIV2_BIN
    _args = ['-e', 'X', 'ex']

    def _compile_commands(self, picture):
        cmd = [ self._bin ] + self._args + [ picture.filename ]
        return cmd,

    def _compile_sidecar_path(self, picture):
        _filename = picture.basename + '.xmp'
        _path = os.path.join(repo.XMP_SIDECAR_DIR, _filename)
        _content_type = 'XMP Metadata'
        return (_path, _content_type)


class AutorotWorker(SubprocessWorker):
    """
    AutorotWorker is a subprocess worker using the jhead tool to automatically
    rotate thumbnails according to their EXIF header.
    """

    name = 'AutorotWorker'
    _bin = config.JHEAD_BIN
    _args = '-autorot'

    def _compile_commands(self, picture):
        cmd = [ self._bin, self._args, picture.thumbnail ]
        return cmd,
