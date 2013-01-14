"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import os
import urlparse
import logging
import errno
import contextlib

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

    def __eq__(self, other):
        return self.url == other.url

    def _rel2abs(self, rel_path):
        if rel_path == '.':
            return self.url.path
        else:
            return os.path.join(self.url.path, rel_path)

    @abstractmethod
    def _connect(self):
        raise NotImplementedError

    def connect(self):
        """Setup connection to base URL."""
        if not self.isconnected:
            log.debug("Connecting to '%s'" % self.url.geturl())
            self._connect()
            self.isconnected = True
        else:
            pass  # do nothing if we're already connected

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

    @contextlib.contextmanager
    def connected(self):
        """Return a contextmanager that handles connect & disconnect."""
        self.connect()
        try:
            yield
        finally:
            self.disconnect()

    def update_url(self, url):
        """Change connector's URL.

        Arguments:
        url -- new url (of type urlparse.ParseResult)

        """
        self.url = url

    @abstractmethod
    def _open(self, path, mode):
        raise NotImplementedError

    def open(self, rel_path, mode):
        """Open file at relative path and return file handle (context manager).

        Arguments:
        rel_path -- path of file to open relative to connector's base URL
        mode     -- 'r' for reading, 'w' for writing or 'a' for appending

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

    def mkdir(self, rel_path, mode=0777, recursive=False):
        """Create a directory at the supplied relative path.

        Arguments:
        rel_path  -- path of directory to create relative to base URL
        mode      -- numeric mode (default: 0777) see os.mkdir's mode for infos
        recursive -- create parent dirs if they don't exist (default: False)

        Raises:
        NotConnectedError

        """
        if self.isconnected:
            rel_dirname = os.path.dirname(rel_path)
            if recursive and not self.exists(rel_dirname):
                self.mkdir(rel_dirname)
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

    def copy(self, src_path, dest_conn, dest_path, create_parents=False):
        """Copy file from src_path to dest_path based on dest_conn's URL.

        Arguments:
        src_path       -- path of file to copy relative to this conn's base URL
        dest_conn      -- connector to destination path
        dest_src       -- destination path relative to dest_conn's base URL
        create_parents -- recursively create parent directories at destination

        Raises:
        NotConnectedError

        """
        if self.isconnected:
            log.debug("Copying '%s'" % \
                          urlparse.urljoin(dest_conn.url.geturl(), dest_path))
            with self.open(src_path, 'r') as src_fh:
                dest_dirname = os.path.dirname(dest_path)
                if create_parents and not dest_conn.exists(dest_dirname):
                    dest_conn.mkdir(dest_dirname, recursive=True)
                with dest_conn.open(dest_path, 'w') as dest_fh:
                    dest_fh.writelines(src_fh.readlines())
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
            return cls(url)


class LocalConnector(Connector):

    def __init__(self, url):
        Connector.__init__(self, url)

    def _connect(self):
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
            if not self.url.port:
                self._ssh.connect(self.url.hostname, username=self.url.username)
            else:
                self._ssh.connect(self.url.hostname, port=self.url.port,
                                  username=self.url.username)
            self._sftp = self._ssh.open_sftp()
        except paramiko.SSHException:
            raise ConnectionError(self.url)

    def _disconnect(self):
        self._sftp.close()
        self._ssh.close()

    def _open(self, path, mode):
        # patch SFTPFile to be used as a context manager
        def enter(obj):
            return obj
        paramiko.SFTPFile.__enter__ = enter

        def exit(obj, exc_type, exc_val, exc_tb):
            obj.close()
            return False
        paramiko.SFTPFile.__exit__ = exit

        return self._sftp.open(path, mode)

    def _exists(self, path):
        """Equivalent to os.path.exists for SFTP."""
        try:
            self._sftp.stat(path)
        except IOError, e:
            if e.errno == errno.ENOENT:  # "No such file or directory"
                return False
            raise
        else:
            return True

    def _mkdir(self, path, mode):
        self._sftp.mkdir(path, mode)

    def _remove(self, path):
        self._sftp.remove(path)
