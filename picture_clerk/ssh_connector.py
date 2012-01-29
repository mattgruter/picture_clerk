"""
Created on 2011/04/24

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""

import os
import paramiko

from connector import Connector
from connector import ConnectionError


class SSHConnector(Connector):
    
    """Holds logic on how to connect to SSH URLs, inherits from Connector."""

    def __init__(self, url):
        """SSHConnector's constructor.
        
        Arguments:
        url -- connector's base path URL, type urlparser.ParseResult or compat.
               Example: "ssh://alice@myhost.domain.org:22/~/path"    
        
               Reference document on SSH/SFTP URI format:
               http://tools.ietf.org/wg/secsh/draft-ietf-secsh-scp-sftp-ssh-uri/
        
        """
        Connector.__init__(self, url)
        
    def _connect(self):
        # Establish a SSH connection; raises ConnectionError.
        # overrides Connector._connect
        #@todo: handle SSH authentication
        self._ssh = paramiko.SSHClient()
        self._ssh.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        try:
            self._ssh.connect(self.url.hostname, port=self.url.port,
                              username=self.url.username)
            self._sftp = self._ssh.open_sftp()
        except paramiko.SSHException:
            raise ConnectionError(self.url)
        
    def _disconnect(self):
        # Close ssh connection objects.
        # overrides Connector._disconnect
        self._sftp.close()
        self._ssh.close()
            
    def _open(self, path, mode):
        # Open file at supplied path and return file handle.
        # overrides Connector._open
        return self._sftp.open(path, mode)
            
    def _mkdir(self, path, mode):
        # Create a directory at the supplied path.
        # overrides Connector._mkdir
        self._sftp.mkdir(path, mode)
        
