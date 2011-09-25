"""
Created on 2011/08/09

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
try:
    import cPickle as pickle
except ImportError:
    import pickle

import ConfigParser


class IndexParsingError(Exception):
    pass
    

class Repo(object):
    """
    PictureClerk repository
    """
    def __init__(self, config=None, index=set()):
        self.config = config
        self.index = index
        
    
    def __repr__(self):
        return "Repo(%s, %s)" % (self.config, self.index)
    
    
    def __str__(self):
        return repr(self)
            
    
    def load_config(self, config_fh):
        """
        Load the repo configuration from supplied file handle.
        
        @param config_fh: readable file handle pointing to the config file
        @type config_fh: file
        """
        # TODO: check out ConfigParser's handling of defaults
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(config_fh)
            
            
    def write_config(self, config_fh):
        """
        Write the repo configuration to supplied file handle
        
        @param config_fh: writable file handle pointing to the config file
        @type config_fh: file
        """
        self.config.write(config_fh)


    def get_index_path(self):
        """
        Return path to the repo's index file.
        
        @return: repo index file path
        @rtype: str
        """
        return self.config.get("core", "index_file")

            
    def load_index(self, index_fh):
        """
        Load (unpickle) picture index from supplied file handle.
        
        @param index_fh: readable file handle pointing to the index file
        @type index_fh: file
        @raise IndexParsingError: if index can not be unpickled
        """
        try:
            self.index = pickle.load(index_fh)
        except pickle.UnpicklingError:
            raise IndexParsingError()

            
    def write_index(self, index_fh):
        """
        Write picture index to index file
        
        @param index_fh: writable file handle pointing to the index file
        @type index_fh: file
        """
        pickle.dump(self.index, index_fh)
            
    

    

