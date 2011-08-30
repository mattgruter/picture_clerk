"""connector.py

PictureClerk - The little helper for your picture workflow.
This file contains the Connector class
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2011/04/24 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"


class NotConnectedError(Exception):
    pass

class AlreadyConnectedError(Exception):
    pass

class URLNotSupportedError(Exception):
    def __init__(self, url):
        self.url = url
    def __str__(self):
        return repr(self.url)
        
class ConnectionError(Exception):
    def __init__(self, url):
        self.url = url
    def __str__(self):
        return repr(self.url)


class Connector(object):
    """
    Connector objects hold the logic on how to connect to given URLs.
    This is the base class.
    """
    def __init__(self, url):
        self.url = url
        self.isconnected = False
        
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self.url))
        
    def connect(self):
        """
        Establish connection to supplied url
        
        Raises AlreadyConnectedError
        """
        # TODO: connect & disconnect should be implemented as ContextManager so
        #       that they can be used with the "with" statement.
        if not self.isconnected:
            self._connect()
            self.isconnected = True
        else:
            # do nothing if we're already connected
            pass
        
    def disconnect(self):
        """
        Cleanly disconnect from supplied url
        """
        if self.isconnected:
            self._disconnect()
            self.isconnected = False
        else:
            # do nothing if we're already disconnected
            pass
            
    def open(self, filename, mode):
        """
        Open the specified file and return a file handle
        
        Raises NotConnectedError
        """
        if self.isconnected:
            return self._open(filename, mode)
        else:
            raise NotConnectedError()
            
    def mkdir(self, rel_path, mode=0777):
        """
        Create the specified directory at the supplied relative path
        
        Raises NotConnectedError
        """
        if self.isconnected:
            self._mkdir(rel_path, mode)
        else:
            raise NotConnectedError()

    def copy(self, src, dest_connector, dest):
        """
        Copy file located at src relative to this connector's URL to file
        located at dest relative to dest_connector's URL.
        """
        if self.isconnected:
            dest_connector.connect()
            with self.open(src, 'r') as src_fh:
                with dest_connector.open(dest, 'w') as dest_fh:
                    dest_fh.writelines(src_fh.readlines())
            dest_connector.disconnect()
        else:
            raise NotConnectedError()
