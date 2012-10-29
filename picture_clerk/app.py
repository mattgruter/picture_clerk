"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import os
import logging
import urlparse

import repo

from connector import Connector, LocalConnector
from recipe import Recipe
from picture import Picture, get_sha1
from pipeline import Pipeline
from viewer import Viewer


log = logging.getLogger('pic.app')


def init_repo(connector):
    """
    Initialize a new repository and return it.
    
    Arguments:
    connector -- Connector pointing to location of repo to be initialized.
    
    Returns:
    The initialized repository.
    """
    repo_config = repo.new_repo_config()
    rep = repo.Repo.create_on_disk(connector, repo_config)
    init_repo_logging(rep)
    log.info("Initialized empty PictureClerk repository")
    return rep

def load_repo(connector):
    """
    Load an existing repository from disk and return it.
    
    Arguments:
    connector -- Connector pointing to location of repo on disk.
    
    Returns:
    The loaded repository.
    """
    rep = repo.Repo.load_from_disk(connector)
    init_repo_logging(rep)
    log.info("Loaded PictureClerk repository from disk")
    return rep

def add_pics(rep, paths, process, recipe=None):
    """
    Add pictures to repository.
    
    Arguments:
    rep     -- Add pictures to this repository.
    paths   -- Paths of the pictures to be added (check if path exists).
    process -- Boolean flag if added pictures should be processed.
    recipe  -- Recipe to use for picture processing.
    """

    for path in paths:
        if not os.path.exists(path):
            log.warning("File not found: '%s'. Skipping it." % path)

    pics = [Picture(path) for path in paths if os.path.exists(path)]
    rep.index.add(pics)

    # process pictures
    if process:
        log.info("Processing pictures.")
        # set up pipeline
        if not recipe:
            process_recipe = \
                Recipe.fromString(rep.config['recipes.default'])
        pl = Pipeline('Pipeline1', process_recipe,
                      path=rep.connector.url.path)
        for pic in pics:
            pl.put(pic)
        # process pictures
        pl.start()
        pl.join()

    log.info("Saving index to file.")
    rep.save_index_to_disk()

def remove_pics(rep, files):
    """
    Remove pictures from repository and from disk.
            
    Arguments:
    rep   -- Remove pictures from this repository.
    files -- Remove the pictures associated with these files.
    """
    pics = [rep.index[fname] for fname in files]
    rep.index.remove(pics)

    # remove all files associated with above pictures
    picfiles = (picfile for pic in pics
                        for picfile in pic.get_filenames())

    for picfile in picfiles:
        try:
            rep.connector.remove(picfile)
        except OSError, e:
            if e.errno == 2: # ignore missing file (= already removed) error
                log.debug("No such file: %s" % e.filename)
            else:
                raise   # re-raise all other (e.g. permission error)

    log.info("Saving index to file.")
    rep.save_index_to_disk()

def list_pics(rep, mode):
    """
    Return information about the pictures in a srepository.
    
    Arguments:
    rep  -- List information about this repository.
    mode -- Type of info: "all", "sidecars", "thumbnails" or "checksums".
    """
    if mode == "all":
        return '\n'.join(('%s' % str(pic)
                          for pic in rep.index.pics()))
    elif mode == "sidecars":
        return '\n'.join(('\n'.join(pic.get_sidecar_filenames())
                          for pic in rep.index.pics()))
    elif mode == "thumbnails":
        return '\n'.join(('\n'.join(pic.get_thumbnail_filenames())
                          for pic in rep.index.pics()))
    elif mode == "checksums":
        return '\n'.join(('%s *%s' % (pic.checksum, pic.filename)
                          for pic in rep.index.pics()))

def view_pics(rep, prog):
    """
    Launch external viewer and keep track of pictures deleted within.
            
    Arguments:
    rep -- View pictures from this repository.
    """
    if not prog:
        prog = rep.config['viewer.prog']
    v = Viewer(prog)
    deleted_pics = v.show(rep.index.pics())
    remove_pics(rep, [pic.filename for pic in deleted_pics])

def migrate_repo(rep):
    """
    Migrate repository from an old index format to the current one.
    
    Arguments:
    rep -- Repository to migrate.
    """
    # only migrate if repo is old
    if rep.config['index.format_version'] < repo.INDEX_FORMAT_VERSION:
        log.info("Migrating repository to new format.")
        rep.config['index.format_version'] = repo.INDEX_FORMAT_VERSION
        rep.save_index_to_disk()
        rep.save_config_to_disk()

def check_pics(rep):
    """
    Verify picture checksums. Return names of corrupt & missing files.
    
    Arguments:
    rep -- Verify pictures in this repository.
    
    Returns:
    A 2-tuple containing a list over the corrupted and a list over the
    missing picture's filenames.
    """
    corrupted = []
    missing = []

    for pic in rep.index.pics():
        try:
            with rep.connector.open(pic.filename, 'r') as buf:
                checksum = get_sha1(buf.read())
        except (IOError, OSError):
            missing.append(pic.filename)
        else:
            if checksum != pic.checksum:
                corrupted.append(pic.filename)

    return corrupted, missing

def merge_repos(rep, others):
    """
    Merge multiple repositories into one.
    
    Arguments:
    rep    -- Merge 'others' repositories into this repository.
    others -- Path pointing to repositories to merge into 'rep'.
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
                    connector.copy(fname, rep.connector, dest_path=fname)
        finally:
            connector.disconnect()

        # add pictures to index
        rep.index.add(other.index.iterpics())

    log.info("Saving index to file.")
    rep.save_index_to_disk()

def clone_repo(src, dest):
    """
    Clone a repository.
    
    Arguments:
    src  -- Connector pointing to the repository to clone from.
    dest -- Connector pointing to the target directory of the clone.
    
    Returns:
    A clone of the supplied repository.
    """
    origin = repo.Repo.load_from_disk(src)
    # create clone at "<dest>/<reponame>" not at "<dest>" directly
    dest_path = os.path.join(dest.url.path, origin.name)
    dest.update_url(urlparse.urlparse(dest_path))
    clone = repo.Repo.clone(origin, dest)
    init_repo_logging(clone)
    log.info("Cloned repository from %s to %s" % (src.url.path,
                                                  dest.url.path))
    return clone

def backup_repo(rep, *locations):
    """
    Backup a repository to multiple locations.
    
    Arguments:
    rep       -- Repository to be backed up
    locations -- Backup repo to these locations (1 or more location args).
    """
    for location in locations:
        backup_path = os.path.join(location.url.path, rep.name)
        location.update_url(urlparse.urlparse(backup_path))
        backup = repo.Repo.clone(rep, location)
        init_repo_logging(backup)
        log.info("Backed up repository to %s" % location.url.path)

def init_repo_logging(rep):
    """Setup file-based logging for a local repository."""
    # Only log to file if repository is located on local filesystem.
    if isinstance(rep.connector, LocalConnector):
        log_path = os.path.join(rep.connector.url.path,
                                rep.config['logging.file'])
        file_handler = logging.FileHandler(log_path)
        formatter = logging.Formatter(rep.config['logging.format'])
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)

def shutdown():
    """Safely shut down application."""
    log.info("Exiting...")
