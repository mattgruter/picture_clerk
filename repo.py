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
    
class IndexWritingError(Exception):
    pass
    

class Repo(object):
    """
    PictureClerk repository
    """
    def __init__(self, connector, config_file=config.CONFIG_FILE):
        self.connector = connector
        self.config_file = config_file
        self._config_fh = None
        self.config = None
        self._index_file = None
        self._index_fh = None
        self._index_shelve = None
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
        self.connector.disconnect()     
                
    def load_config(self):
        """
        Load the repo configuration from file.
        """
        self._config_fh = self.connector.open(self.config_file, 'rb')
        # TODO: how to handle if config file does not exist?
        # TODO: check out ConfigParser's handling of defaults
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(self._config_fh)
        self._config_fh.close()
            
            
    def load_index(self):
        """
        Load picture index from index file.
        """
        if not self._index_file:
            # read index_file from repo-config
            self._index_file = self.config.get("global", "index_file")
        self._index_fh = self.connector.open(self._index_file, 'rb')
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
        if not self._index_file:
            # read index_file from repo-config
            self._index_file = self.config.get("global", "index_file")
        self._index_fh = self.connector.open(self._index_file, 'wb')
        try:
            pickle.dump(self.index, self._index_fh)
        except pickle.PicklingError:
            raise IndexWritingError()
        finally:
            self._index_fh.close()
        
        
        
