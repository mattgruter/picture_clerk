"""
Created on 2011/04/24

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""

import urlparse

from abc import ABCMeta, abstractmethod


class NotConnectedError(Exception):
    pass

class URLNotSupportedError(Exception):
    def __init__(self, url):
        self.url = url
    def __str__(self):
        return self.url.geturl()
        
class ConnectionError(Exception):
    def __init__(self, url):
        self.url = url
    def __str__(self):
        return self.url.geturl()

class Connector(object):
    
    """Holds the logic on how to connect to given URLs. (Abstract class)"""
    
    __metaclass__ = ABCMeta
    
    def __init__(self, url):
        """Connector's constructor.
        
        Arguments:
        url -- connector's base path URL, type urlparser.ParseResult or compat.
        
        """
        self.url = url
        self.isconnected = False
        
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self.url))
    
    def _rel2abs(self, rel_path):
        if rel_path == '.':
            return self.url.path
        else:
            return urlparse.urljoin(self.url.path, rel_path)
            
    @abstractmethod
    def _connect(self):
        pass
        
    def connect(self):
        """Setup connection to base URL."""
        #@todo: connect & disconnect should be implemented as ContextManager so
        #       that they can be used with the "with" statement.
        if not self.isconnected:
            self._connect()
            self.isconnected = True
        else:
            # do nothing if we're already connected
            pass
    
    @abstractmethod
    def _disconnect(self):
        pass

    def disconnect(self):
        """Cleanly disconnect from connector's base URL."""
        if self.isconnected:
            self._disconnect()
            self.isconnected = False
        else:
            # do nothing if we're already disconnected
            pass
         
    @abstractmethod
    def _open(self, path, mode):
        pass 
           
    def open(self, rel_path, mode):
        """Open file at the supplied relative path and return a file handle.
        
        Arguments:
        rel_path -- path of directory to create relative to connector's base URL
        
        Raises:
        NotConnectedError
        
        """
        if self.isconnected:
            path = self._rel2abs(rel_path)
            return self._open(path, mode)
        else:
            raise NotConnectedError()
         
    @abstractmethod
    def _mkdir(self, path, mode):
        pass 
            
    def mkdir(self, rel_path, mode=0777):
        """Create a directory at the supplied relative path.
        
        Arguments:
        rel_path -- path of directory to create relative to connector's base URL
        
        Raises:
        NotConnectedError
        
        """
        if self.isconnected:
            path = self._rel2abs(rel_path)
            self._mkdir(path, mode)
        else:
            raise NotConnectedError()

    def copy(self, src_path, dest_conn, dest_path):
        """Copy file from src_path to dest_path based on dest_conn's URL.

        Arguments:
        src_path  -- path of file to copy relative to this connector's base URL
        dest_conn -- connector to destination path
        dest_src  -- destination path relative to dest_conn's base URL 

        Raises:
        NotConnectedError

        """
        if self.isconnected:
            dest_conn.connect()
            with self.open(src_path, 'r') as src_fh:
                with dest_conn.open(dest_path, 'w') as dest_fh:
                    dest_fh.writelines(src_fh.readlines())
            dest_conn.disconnect()
        else:
            raise NotConnectedError()
