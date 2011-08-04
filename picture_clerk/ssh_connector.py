"""ssh_connector.py

PictureClerk - The little helper for your picture workflow.
This file contains the SSHConnector class
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2011/04/24 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"


import paramiko


from connector import Connector
from connector import ConnectionError


class SSHConnector(Connector):
    """
    A SSHConnector object holds the logic on how to connect to remote SSH URLs.
    This class inherits from the Connector base class.
    """
    def __init__(self, url):
        Connector.__init__(self, url)
        
    def _connect(self):
        """
        Establish a SSH connection
        
        Raises ConnectionError
        """
        # TODO: handle SSH authentication
        self._ssh = paramiko.SSHClient()
        self._ssh.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        try:
            self._ssh.connect(self.url.hostname, port=self.url.port,
                              username=self.url.username)
            self._sftp = self._ssh.open_sftp()
        except paramiko.SSHException:
            raise ConnectionError(self.url)
        
    def _disconnect(self):
        """
        Close ssh connection objects
        """
        self._sftp.close()
        self._ssh.close()
            
    def _open(self, filename, mode):
        """
        Open the specified file and return a file handle
        """
        return self._sftp.open(os.path.join(self.url.path, filename), mode)
            
    def _mkdir(self, path, mode):
        """
        Create the specified directory
        """
        self._sftp.mkdir(os.path.join(self.url.path, path), mode)
        
