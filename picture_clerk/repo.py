"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import copy
import logging
import os

import config
import index


log = logging.getLogger('pic.repo')


# constants
PIC_DIR = ".pic"    # PictureClerk repo directory
CONFIG_FILE = os.path.join(PIC_DIR, "config")
INDEX_FILE = os.path.join(PIC_DIR, "index")
INDEX_FORMAT_VERSION = 1

# @todo: remove these deprecated options
SHA1_SIDECAR_ENABLED = 1
SHA1_SIDECAR_DIR = os.path.join(PIC_DIR, "sha1")
THUMB_SIDECAR_DIR = "jpg"
XMP_SIDECAR_DIR = os.path.join(PIC_DIR, "xmp")


def new_repo_config():
    """Return default repo configuration (Config instance)."""

    config_defaults = {

        'index.file': INDEX_FILE,
        'index.format_version': INDEX_FORMAT_VERSION,

        'recipes.default':
            'HashDigestWorker, ThumbWorker, AutorotWorker, MetadataWorker',

        'thumbnails.sidecar_dir': THUMB_SIDECAR_DIR,

        'checksums.sidecar_enabled': SHA1_SIDECAR_ENABLED,
        'checksums.sidecar_dir': SHA1_SIDECAR_DIR,

        'logging.file': os.path.join(PIC_DIR, "log.txt"),
        'logging.level': logging.DEBUG,
        'logging.format':
            '%%(asctime)s %%(name)-15s %%(levelname)-8s %%(message)s',

        'viewer.prog': "qiv -m -t"

    }

    return config.Config(config_defaults)


class NotFoundError(Exception):
    def __init__(self, url):
        Exception.__init__(self)
        self.url = url
    def __str__(self):
        return "No repository found at %s" % self.url.geturl()


class VersionMismatchError(Exception):
    def __init__(self, actual, expected):
        Exception.__init__(self)
        self.actual = actual
        self.expected = expected
    def __str__(self):
        s = "Repository version mismatch: "
        s += "detected %i, " % self.actual
        s += "expected %i" % self.expected
        return s


class Repo(object):

    def __init__(self, index, config, connector):
        """A repository contains and manages a picture index.
        
        There are methods for creating a new repository directory structure,
        loading an existing repository from disk, loading and saving index &
        configuration and cloning an existing repository.
        
        index      -- PictureIndex instance
        config    -- repository specific configuration (type ConfigParser)
        connector -- Connector instance pointing to index's location
        
        """
        self.index = index
        self.config = config
        self.connector = connector

    def save_config_to_disk(self):
        """Save configuration to disk."""
        log.info("Saving repository configuration.")
        with self.connector.open(CONFIG_FILE, 'w') as config_fh:
            self.config.write(config_fh)

    def load_config_from_disk(self):
        """Load configuration from disk."""
        log.info("Loading repository configuration.")
        self.config = new_repo_config()
        with self.connector.open(CONFIG_FILE, 'r') as config_fh:
            self.config.read(config_fh)

    def save_index_to_disk(self):
        """Save picture index to disk."""
        log.info("Saving repository picture index, version %i" % INDEX_FORMAT_VERSION)
        index_filename = self.config['index.file']
        with self.connector.open(index_filename, 'wb') as index_fh:
            self.index.write(index_fh)

    def load_index_from_disk(self, version=INDEX_FORMAT_VERSION):
        """Load picture index from disk."""
        if version > INDEX_FORMAT_VERSION:
            raise VersionMismatchError(version, INDEX_FORMAT_VERSION)
        else:
            log.info("Loading repository picture index, version %i" % version)
            index_filename = self.config['index.file']
            index_loader = {1: self._load_index_v1} # mapping version vs. method
            with self.connector.open(index_filename, 'rb') as index_fh:
                self.index = index_loader[version](index_fh)

    def _load_index_v1(self, fh):
        pi = index.PictureIndex()
        pi.read(fh)
        return pi

    @classmethod
    def create_on_disk(cls, connector, conf, pi=None):
        """Create repo and necessary dirs according to config. Return repo.
        
        connector -- connector to index's base dir (created if necessary)
        conf      -- repository specific configuration
        pi        -- picture index (optional)
        
        """
        if not pi:
            pi = index.PictureIndex()
        try:
            connector.connect()
            if not connector.exists('.'):
                connector.mkdir('.')
            connector.mkdir(PIC_DIR)
            with connector.open(CONFIG_FILE, 'w') as config_fh:
                conf.write(config_fh)
            repo = Repo(pi, conf, connector)
            repo.save_index_to_disk()
        finally:
            connector.disconnect()
        return repo

    @classmethod
    def load_from_disk(cls, connector):
        """Load configuration & repository from disk. Return repo.
        
        connector -- connector to index's base dir
        
        """
        repo = Repo(config={}, index={}, connector=connector)
        try:
            connector.connect()

            # check if dir exists
            if not (connector.exists('.') and connector.exists(PIC_DIR)):
                raise NotFoundError(connector.url)

            repo.load_config_from_disk()
            repo.load_index_from_disk(repo.config['index.format_version'])

        finally:
            connector.disconnect()

        return repo

    @classmethod
    def clone(cls, src, dest):
        """Clone an existing repository to a new location and return it.
        
        src  -- connector pointing to source repo's location
        dest -- connector pointing to location of new clone-index
        
        """
        
        #@fixme: src & dest connectors are connected/disconnected many times:
        #        src: 1x load_from_disk, 1x src.connect
        #        dest: 1x create_on_disk, 1x dest.connect
        
        # clone repo
        src_repo = Repo.load_from_disk(src)
        repo = Repo.create_on_disk(connector=dest,
                                   conf=src_repo.config,
                                   pi=copy.deepcopy(src_repo.index))

        # clone pictures
        try:
            src.connect()
            dest.connect()
            for picture in src_repo.index.iterpics():
                for fname in picture.get_filenames():
                    src.copy(fname, dest, dest_path=fname)
        finally:
            src.disconnect()
            dest.disconnect()

        return repo
