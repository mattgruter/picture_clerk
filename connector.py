"""connector.py

PictureClerk - The little helper for your picture workflow.
This file contains the Picture class
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2011/03/08 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"


import paramiko
import os.path


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
    def __init__(self, error, url):
        self.error = error
    def __str__(self):
        return repr(self.error, self.url)


class Connector(object):
    """
    A Connector object holds the logic on how one can connect to a Repo
    depending on the type of URL used.
    """
    def __init__(self, url):
        self.url = url
        self.isconnected = False
        
    def connect(self):
        """
        Establish connection to supplied url
        
        Raises AlreadyConnectedError, ConnectionError and URLNotSupportedError
        """
        if self.isconnected:
            raise AlreadyConnectedError()
        elif self.url.islocal:
            self.isconnected = True
        elif self.url.protocol == "ssh":
            self._ssh = paramiko.SSHClient()
            self._ssh.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
            try:
                self._ssh.connect(self.url.hostname, port=self.url.port,
                                  username=self.url.username)
                self._sftp = self._ssh.open_sftp()
            except paramiko.SSHException as e:
                raise ConnectionError(e, self.url)
            else:
                self.isconnected = True
        else:
            raise URLNotSupportedError(self.url)
        
    def disconnect(self):
        """
        Cleanly disconnect from supplied url
        
        Raises URLNotSupportedError
        """
        if not self.isconnected:
            pass
        elif self.url.islocal:
            self.isconnected = False
        elif self.url.protocol == "ssh":
            self._sftp.close()
            self._ssh.close()
            self.isconnected = False
        else:
            raise URLNotSupportedError(self.url)
            
    def open(self, filename, mode):
        """
        Open the specified file and return a file handle
        
        Raises NotConnectedError, URLNotSupportedError
        """
        if not self.isconnected:
            raise NotConnectedError()
        elif self.url.islocal:
            return open(os.path.join(self.url.path, filename), mode)
        elif self.url.protocol == "ssh":
            return self._sftp.open(os.path.join(self.url.path, filename), mode)
        else:
            raise URLNotSupportedError(self.url)
            
