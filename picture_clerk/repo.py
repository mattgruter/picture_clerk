"""repo.py

PictureClerk - The little helper for your picture workflow.
This file contains the Picture class
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2011/03/08 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"


try:
   import cPickle as pickle
except:
   import pickle

import ConfigParser

import config


class IndexEmptyError(Exception):
    pass
    

class Repo(object):
    """
    PictureClerk repository
    """
    def __init__(self, connector,
                 pic_dir=config.PIC_DIR, config_file=config.CONFIG_FILE):
        self.connector = connector
        self.pic_dir = pic_dir
        self.config_file = config_file
        self._config_fh = None
        self.config = None
        self._index_fh = None
        self.index = None
        
    def connect(self):
        """
        Connect to the repository.
        """
        self.connector.connect()
            
    def disconnect(self):
        """
        Disconnect from the repository.
        """
        # try any potentially open file handles
        try:
            self._config_fh.close()
            self._index_fh.close()
        except AttributeError:
            pass
        self.connector.disconnect()     
    
    def init(self):
        """
        Initialize a repository
        
        create .pic directory and create default configuration file
        """
        self.connector.mkdir(self.pic_dir)
        self.write_default_config()
        
    def write_default_config(self):
        """
        Write the default repo configuration to the repo's config file
        """
        with self.connector.open(self.config_file, 'w') as self._config_fh:
            self._config_fh.write("[core]\n")
            self._config_fh.write("\tindex_file = %s\n" % config.INDEX_FILE)
            self._config_fh.write("\tindex_format_version = %i\n" % \
                                  config.INDEX_FORMAT_VERSION)
    
    def load_config(self):
        """
        Load the repo configuration from file.
        """
        with self.connector.open(self.config_file, 'rb') as self._config_fh:
            # TODO: how to handle if config file does not exist?
            # TODO: check out ConfigParser's handling of defaults
            self.config = ConfigParser.ConfigParser()
            self.config.readfp(self._config_fh)
            
    def load_index(self):
        """
        Load picture index from index file.
        """
        index_path = self.config.get("core", "index_file")
        self._index_fh = self.connector.open(index_path, 'rb')
        try:
            self.index = pickle.load(self._index_fh)
        except pickle.UnpicklingError:
            raise IndexEmptyError()
        finally:
            self._index_fh.close()
            
    def write_index(self):
        """
        Write picture index to index file
        """
        index_path = self.config.get("core", "index_file")
        with self.connector.open(index_path, 'wb') as self._index_fh:
            pickle.dump(self.index, self._index_fh)

