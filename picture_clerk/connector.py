"""
Created on 2011/04/24

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""

import os
import urlparse
import logging

import paramiko

from abc import ABCMeta, abstractmethod


log = logging.getLogger('pic.connector')

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
        raise NotImplementedError

    def connect(self):
        """Setup connection to base URL."""
        #@todo: connect & disconnect should be implemented as ContextManager so
        #       that they can be used with the "with" statement.
        if not self.isconnected:
            log.debug("Connecting to '%s'" % self.url.geturl())
            self._connect()
            self.isconnected = True
        else:
            # do nothing if we're already connected
            pass

    @abstractmethod
    def _disconnect(self):
        raise NotImplementedError

    def disconnect(self):
        """Cleanly disconnect from connector's base URL."""
        if self.isconnected:
            log.debug("Disconnecting from '%s'" % self.url.geturl())
            self._disconnect()
            self.isconnected = False
        else:
            # do nothing if we're already disconnected
            pass

    @abstractmethod
    def _open(self, path, mode):
        raise NotImplementedError

    def open(self, rel_path, mode):
        """Open file at the supplied relative path and return a file handle.
        
        Arguments:
        rel_path -- path of file to open relative to connector's base URL
        
        Raises:
        NotConnectedError
        
        """
        if self.isconnected:
            path = self._rel2abs(rel_path)
            log.debug("Opening file '%s'" % path)
            return self._open(path, mode)
        else:
            raise NotConnectedError()

    @abstractmethod
    def _mkdir(self, path, mode):
        raise NotImplementedError

    def mkdir(self, rel_path, mode=0777):
        """Create a directory at the supplied relative path.
        
        Arguments:
        rel_path -- path of directory to create relative to connector's base URL
        
        Raises:
        NotConnectedError
        
        """
        if self.isconnected:
            path = self._rel2abs(rel_path)
            log.debug("Creating directory '%s'" % path)
            self._mkdir(path, mode)
        else:
            raise NotConnectedError()

    @abstractmethod
    def _remove(self, path):
        raise NotImplementedError

    def remove(self, rel_path):
        """Remove file at supplied relative path.
        
        Arguments:
        rel_path -- path of file to remove relative to connector's base URL
        
        Raises:
        NotConnectedError
        
        """
        if self.isconnected:
            path = self._rel2abs(rel_path)
            log.debug("Removing file '%s'" % path)
            self._remove(path)
        else:
            raise NotConnectedError()

    @abstractmethod
    def _exists(self, path):
        raise NotImplementedError

    def exists(self, rel_path):
        """Check if relative path exists
        
        Arguments:
        rel_path -- path to check relative to connector's base URL
        
        Raises:
        NotConnectedError
        
        """
        if self.isconnected:
            path = self._rel2abs(rel_path)
            log.debug("Checking path '%s'" % path)
            return self._exists(path)
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
            log.debug("Copying '%s'" % \
                          urlparse.urljoin(dest_conn.url.geturl(), dest_path))
            dest_conn.connect()
            with self.open(src_path, 'r') as src_fh:
                with dest_conn.open(dest_path, 'w') as dest_fh:
                    dest_fh.writelines(src_fh.readlines())
            dest_conn.disconnect()
        else:
            raise NotConnectedError()

    @classmethod
    def from_string(cls, url):
        """Parse url string and return appropriate Connector instance.
        
        Arguments:
        url -- connector's base path URL as a string, parsable by urlparse
        
        Example URL strings:
           "rel/path/..."                            --> relative local path
           "/abs/path/..."                           --> absolute local path
           "ssh://alice@myhost.domain.org:22/~/path" --> remote SSH path
           "file:///var/file"                        --> absolute local path
    
           Reference document on SSH/SFTP URI format:
           http://tools.ietf.org/wg/secsh/draft-ietf-secsh-scp-sftp-ssh-uri/
        
        """
        url = urlparse.urlparse(url)
        if cls == Connector:
            if not url.scheme or url.scheme == 'file':
                return LocalConnector(url)
            elif url.scheme == 'ssh':
                return SSHConnector(url)
            else:
                raise NotImplementedError
        else:
            return cls(urlparse.urlparse(url))


class LocalConnector(Connector):

    def __init__(self, url):
        Connector.__init__(self, url)

    def _connect(self):
        if not os.path.exists(self.url.path):
            raise ConnectionError(self.url)
        return

    def _disconnect(self):
        return

    def _open(self, path, mode):
        return open(path, mode)

    def _exists(self, path):
        return os.path.exists(path)

    def _mkdir(self, path, mode):
        os.mkdir(path, mode)

    def _remove(self, path):
        os.remove(path)


class SSHConnector(Connector):

    def __init__(self, url):
        Connector.__init__(self, url)

    def _connect(self):
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
        self._sftp.close()
        self._ssh.close()

    def _open(self, path, mode):
        return self._sftp.open(path, mode)

    def _mkdir(self, path, mode):
        self._sftp.mkdir(path, mode)

    def _remove(self, path):
        self._sftp.remove(path)
