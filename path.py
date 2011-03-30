"""path.py

PictureClerk - The little helper for your picture workflow.
This file contains the Picture class
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2011/03/08 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"


import re
import os.path

from urlparse import urlparse


class ExistsNotSupported(Exception):
    def __init__(self, protocol):
        self.protocol = protocol
    def __str__(self):
        return repr(self.protocol)
        
class InvalidURI(Exception):
    pass

# TODO: rename to URL
# TODO: add join method
class Path(object):
    """
    Repository path encapsulation (local or remote)
    """
    def __init__(self, path=None, protocol="file",
                 hostname=None, username=None, port=None):
        self.path = path
        self.protocol = protocol
        self.hostname = hostname
        self.username = username
        self.port = port
        if not self.protocol or self.protocol == "file":
            self.islocal = True
            self.isremote = False
        else:
            self.islocal = False
            self.isremote = True
            
            
    def __str__(self):
        if self.islocal:
            return "file://%s" % self.path
            
        if self.isremote:
            if self.path.startswith("~"):
                path = "/" + self.path
            # relative paths are relative to user's home
            elif self.path and not self.path.startswith("/"):
                path = "/~/" + self.path
            else:
                path = self.path
            if self.username:
                if self.port:
                    return "%s://%s@%s:%s%s" % (self.protocol, self.username,
                                                self.hostname, self.port, path)
                else:
                    return "%s://%s@%s%s" % (self.protocol, self.username,
                                             self.hostname, path)
            else:
                if self.port:
                    return "%s://%s:%s%s" % (self.protocol, self.hostname,
                                             self.port, path)
                else:
                    return "%s://%s%s" % (self.protocol, self.hostname, path)
                
    
    @staticmethod
    def fromPath(path):
        """
        Factory method to create Path instances from parsed path strings.
        Local paths look like "relative/path", "/absolute/path" and remote SSH
        paths look like "username@server:/absolute/path"
        """
        # try to split path into hostname:path pair
        try:
            hostname, path = re.split(r':', path, maxsplit=1)
        except ValueError:
            # path is local
            return Path(path, "file")
        else:
            # default remote protocol is SSH
            protocol = "ssh"
            port = None
                
            # check if hostname is prefixed by username
            m = re.match(r'^(\w+)@(.+)$', hostname)
            if m:
                # split off username from hostnname
                username, hostname = m.groups()
            else:
                username = None
            
            return Path(path, protocol, hostname, username, port)

    
    # TODO: rename to fromStr
    @staticmethod
    def fromURI(uri):
        """
        Factory method to create Path instances from URI.
        Format: [protocol]://[username]@[hostname]:[port]/[path]
        Examples: "http://joe@server.yourdomain.com/path/subdir"
                  "file:///absolute/path"
                  "ssh://alice@myhost.domain.org:22/~/path"
        
        See http://tools.ietf.org/wg/secsh/draft-ietf-secsh-scp-sftp-ssh-uri/
        for reference on SSH/SFTP URI format
        """
        # check if protocol is supplied (syntax "proto://rest")
        if not re.match(r'^(\w+)://(.*)$', uri):
            raise InvalidURI
            
        else:
            url = urlparse(uri)
            if url.scheme == "file":
                # local path
                return Path(path=url.netloc+url.path, protocol="file",
                            hostname=None, username=None, port=None)
            else:
                # remote path
                return Path(path=url.path, protocol=url.scheme,
                            hostname=url.hostname, username=url.username,
                            port=url.port)
                
            
    def exists(self):
        if self.islocal:
            if os.path.isdir(self.path):
                return True
            else:
                return False
                
        if self.isremote:
            raise ExistsNotSupported(self.protocol)

