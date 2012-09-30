"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import os
import logging

import repo

from connector import Connector, LocalConnector
from recipe import Recipe
from picture import Picture, get_sha1
from pipeline import Pipeline
from viewer import Viewer


log = logging.getLogger('pic.app')


class App(object):
    """PictureClerk's application logic."""

    def __init__(self, connector):
        self.connector = connector

    def init_repo(self):
        """Initialize new repository."""
        repo_config = repo.new_repo_config()
        r = repo.Repo.create_on_disk(self.connector, repo_config)
        self.init_repo_logging(repo_config['logging.file'],
                               repo_config['logging.format'])
        log.info("Initialized empty PictureClerk repository")
        return r

    def load_repo(self):
        """Load existing repository from disk."""
        r = repo.Repo.load_from_disk(self.connector)
        self.init_repo_logging(r.config['logging.file'],
                               r.config['logging.format'])
        log.info("Loaded PictureClerk repository from disk")
        return r

    def add_pics(self, r, paths, process_enabled, process_recipe=None):
        """Add pictures to repository.
        
        Arguments:
        r               -- add pictures to this repo
        paths           -- the picture paths to be added
        process_enabled -- boolean flag if added pictures should be processed
        process_recipe  -- recipe to use for picture processing  
        
        """
        pics = [Picture(path) for path in paths if os.path.exists(path)]
        r.index.add(pics)

        # process pictures
        if process_enabled:
            log.info("Processing pictures.")
            # set up pipeline
            if not process_recipe:
                process_recipe = \
                    Recipe.fromString(r.config['recipes.default'])
            pl = Pipeline('Pipeline1', process_recipe,
                          path=self.connector.url.path)
            for pic in pics:
                pl.put(pic)
            # process pictures
            pl.start()
            pl.join()

        log.info("Saving index to file.")
        r.save_index_to_disk()
        return r

    def remove_pics(self, r, files):
        """Remove pictures associated with supplied files from repo & disk.
        
        Arguments:
        r    -- remove pictures from this repo
        file -- file associated to the picture to be removed
        
        """
        pics = [r.index[fname] for fname in files]
        r.index.remove(pics)

        # remove all files associated with above pictures
        picfiles = (picfile for pic in pics
                            for picfile in pic.get_filenames())

        for picfile in picfiles:
            try:
                self.connector.remove(picfile)
            except OSError, e:
                if e.errno == 2: # ignore missing file (= already removed) error
                    log.debug("No such file: %s" % e.filename)
                else:
                    raise   # re-raise all other (e.g. permission error)

        log.info("Saving index to file.")
        r.save_index_to_disk()
        return r

    def list_pics(self, r, mode):
        """Return information on pictures in repository.
        
        Arguments:
        r    -- list information about this repository
        mode -- type of info: "all", "sidecars", "thumbnails", "checksums"
        
        """
        if mode == "all":
            return '\n'.join(('%s' % str(pic)
                              for pic in r.index.pics()))
        elif mode == "sidecars":
            return '\n'.join(('\n'.join(pic.get_sidecar_filenames())
                              for pic in r.index.pics()))
        elif mode == "thumbnails":
            return '\n'.join(('\n'.join(pic.get_thumbnail_filenames())
                              for pic in r.index.pics()))
        elif mode == "checksums":
            return '\n'.join(('%s *%s' % (pic.checksum, pic.filename)
                              for pic in r.index.pics()))

    def view_pics(self, r, prog):
        """Launch viewer program and keep track of pictures deleted within.
                
        Arguments:
        r -- view pictures from this repository
        
        """
        if not prog:
            prog = r.config['viewer.prog']
        v = Viewer(prog)
        deleted_pics = v.show(r.index.pics())
        self.remove_pics(r, [pic.filename for pic in deleted_pics])
        return r

    def migrate_repo(self, r):
        """Migrate repository from an old format to the current one.
        
        Arguments:
        r -- repository to migrate
        
        """
        # only migrate if repo is old
        if r.config['index.format_version'] < repo.INDEX_FORMAT_VERSION:
            log.info("Migrating repository to new format.")
            r.config['index.format_version'] = repo.INDEX_FORMAT_VERSION
            r.save_index_to_disk()
            r.save_config_to_disk()
        return r

    def check_pics(self, r):
        """Verify picture checksums. Return names of corrupt & missing pics.
        
        Arguments:
        r -- verify pictures in this repository
        
        """
        corrupted = []
        missing = []

        for pic in r.index.pics():
            try:
                with self.connector.open(pic.filename, 'r') as buf:
                    checksum = get_sha1(buf.read())
            except (IOError, OSError):
                missing.append(pic.filename)
            else:
                if checksum != pic.checksum:
                    corrupted.append(pic.filename)
                    
        return corrupted, missing
        
    def merge_repos(self, r, others):
        """Merge repositories into one.
        
        Arguments:
        r      -- merge 'others' repositories into this one
        others -- rsitories to merge into 'r'
        
        """
        for url in others:
            log.info("Merging repository '%s'", url)
            connector = Connector.from_string(url)
            try:
                connector.connect()
                other = repo.Repo.load_from_disk(connector)
                
                # copy picture files
                for picture in other.index.iterpics():
                    for fname in picture.get_filenames():
                        connector.copy(fname, self.connector, dest_path=fname)
            finally:
                connector.disconnect()
                    
            # add pictures to index
            r.index.add(other.index.iterpics())
                    
        log.info("Saving index to file.")
        r.save_index_to_disk()
        return r
        
    def clone_repo(self, origin):
        """Clone a repository.
        
        Arguments:
        origin -- repository to clone from (source)
        
        """
        r = repo.Repo.clone(origin, self.connector)
        self.init_repo_logging(r.config['logging.file'],
                               r.config['logging.format'])
        log.info("Cloned repository from %s to %s" % (origin.url.path,
                                                      self.connector.url.path))
        return r

    def init_repo_logging(self, log_file, log_format):
        # repo file logging (only if repo is local)
        if isinstance(self.connector, LocalConnector):
            log_path = os.path.join(self.connector.url.path, log_file)
            file_handler = logging.FileHandler(log_path)
            formatter = logging.Formatter(log_format)
            file_handler.setFormatter(formatter)
            logging.getLogger().addHandler(file_handler)

    def shutdown(self):
        log.info("Exiting...")
