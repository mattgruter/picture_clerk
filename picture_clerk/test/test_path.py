import unittest

from ..path import *

class PathObjectCreationTest(unittest.TestCase):
    path = "test-path"
    hostname = "test-host"
    username = "test-user"
    port = 123
    protocol_local = "file"
    protocol_ssh = "ssh"
    protocol_http = "http"
    
    def testDefaultAttributes(self):
        """
        __init__ should apply the correct default attribute values
        """
        p = Path()
        self.assertEqual(None, p.path)
        self.assertEqual(None, p.hostname)
        self.assertEqual(None, p.username)
        self.assertEqual(None, p.port)
        self.assertEqual(self.protocol_local, p.protocol)
        self.assertTrue(p.islocal)
        self.assertFalse(p.isremote)
    
    def testAllAttributesLocal(self):
        """
        __init__ should store all supplied attributes and set islocal, isremote
        """
        # local path
        p = Path(self.path, self.protocol_local,
                 self.hostname, self.username, self.port)
        self.assertEqual(self.path, p.path)
        self.assertEqual(self.hostname, p.hostname)
        self.assertEqual(self.username, p.username)
        self.assertEqual(self.port, p.port)
        self.assertEqual(self.protocol_local, p.protocol)
        self.assertTrue(p.islocal)
        self.assertFalse(p.isremote)
        
    def testAllAttributesRemoteSSH(self):
        """
        __init__ should store all supplied pattributes and set islocal, isremote
        """
        # remote path (SSH)
        p = Path(self.path, self.protocol_ssh,
                 self.hostname, self.username, self.port)
        self.assertEqual(self.path, p.path)
        self.assertEqual(self.hostname, p.hostname)
        self.assertEqual(self.username, p.username)
        self.assertEqual(self.port, p.port)
        self.assertEqual(self.protocol_ssh, p.protocol)
        self.assertFalse(p.islocal)
        self.assertTrue(p.isremote)
        
    def testAllAttributesRemoteHTTP(self):
        """
        __init__ should store all supplied attributes and set islocal, isremote
        """
        # remote path (HTTP)
        p = Path(self.path, self.protocol_http,
                 self.hostname, self.username, self.port)
        self.assertEqual(self.path, p.path)
        self.assertEqual(self.hostname, p.hostname)
        self.assertEqual(self.username, p.username)
        self.assertEqual(self.port, p.port)
        self.assertEqual(self.protocol_http, p.protocol)
        self.assertFalse(p.islocal)
        self.assertTrue(p.isremote)
        
        
class PathStrTest(unittest.TestCase):
    def testLocalPathStr(self):
        """
        str represenation of a local path should look like "file://path"
        """
        p = Path(path="/foo/bar", protocol="file", hostname=None,
                 username=None, port=None)
        self.assertEqual("file:///foo/bar", str(p))
        
    def testRemotePathStr(self):
        """
        str represenation of a remote path should look like
        "<protocol>://<username>@<hostname>:<port>/<path>"
        """
        p = Path(path="/foo/bar", protocol="ssh", hostname="server",
                 username=None, port=None)
        self.assertEqual("ssh://server/foo/bar", str(p))
        
    def testRemotePathWithUsernameStr(self):
        """
        str represenation of a remote path should look like
        "<protocol>://<username>@<hostname>:<port>/<path>"
        """
        p = Path(path="/foo/bar", protocol="ssh", hostname="server",
                 username="user", port=None)
        self.assertEqual("ssh://user@server/foo/bar", str(p))
        
    def testRemotePathWithPortStr(self):
        """
        str represenation of a remote path should look like
        "<protocol>://<username>@<hostname>:<port>/<path>"
        """
        p = Path(path="/foo/bar", protocol="ssh", hostname="server",
                 username="user", port=123)
        self.assertEqual("ssh://user@server:123/foo/bar", str(p))
        
    def testRemoteNullPathStr(self):
        """
        str represenation of a remote path should look like
        "<protocol>://<username>@<hostname>:<port>/<path>"
        """
        p = Path(path="", protocol="ssh", hostname="server",
                 username=None, port=None)
        self.assertEqual("ssh://server", str(p))
        
    def testRemoteRelativePathStr(self):
        """
        str represenation of a remote path should look like
        "<protocol>://<username>@<hostname>:<port>/<path>"
        """
        p = Path(path="relative/path", protocol="ssh", hostname="server",
                 username=None, port=None)
        self.assertEqual("ssh://server/~/relative/path", str(p))


class PathExistsTest(unittest.TestCase):
    existing_paths = [".", "/", ".."]
    non_existing_paths = ["/tu024nvalkjas", "420  ds093 - asw34_4"]
        
    def testExistingPath(self):
        """
        exists should return True for paths known to exist
        """
        for path in self.existing_paths:
            p = Path.fromPath(path)
            self.assertTrue(p.exists())
            
    def testNonExistingPath(self):
        """
        exists should return False for paths known not to exist
        """
        for path in self.non_existing_paths:
            p = Path.fromPath(path)
            self.assertFalse(p.exists())
    
    def testRemotePathException(self):
        """
        exists should raise an exception if called with remote path
        """
        p = Path.fromPath("server:/remote/path")
        self.assertRaises(ExistsNotSupported, p.exists)
        

class LocalPathParsingTest(unittest.TestCase):
    paths = (".", "/", "/tu024nvalkjas", "420  ds093 - asw34_4", "o.@jgae%")
       
    def testParsePaths(self):
        for path  in self.paths:
            p = Path.fromPath(path)
            self.assertEqual(path, p.path)
            self.assertEqual("file", p.protocol)
            self.assertEqual(None, p.hostname)
            self.assertEqual(None, p.username)
            self.assertEqual(None, p.port)
            
            
class RemotePathParsingTest(unittest.TestCase):
    ssh_paths = (
            ("server.example.com:/abs/path",
                {'path':     "/abs/path",
                 'protocol': "ssh",
                 'hostname': "server.example.com",
                 'username': None,
                 'port':     None}),
            ("server.example.com:rel/path",
                {'path':     "rel/path",
                 'protocol': "ssh",
                 'hostname': "server.example.com",
                 'username': None,
                 'port':     None}),
            ("user@server.example.com:rel/path",
                {'path':     "rel/path",
                 'protocol': "ssh",
                 'hostname': "server.example.com",
                 'username': "user",
                 'port':     None}),
            ("host:",
                {'path':     "",
                 'protocol': "ssh",
                 'hostname': "host",
                 'username': None,
                 'port':     None}))
 
    def testToPath(self):
        for path, d  in self.ssh_paths:
            p = Path.fromPath(path)
            self.assertEqual(d['path'], p.path)
            self.assertEqual(d['protocol'], p.protocol)
            self.assertEqual(d['hostname'], p.hostname)
            self.assertEqual(d['username'], p.username)
            self.assertEqual(d['port'], p.port)
       
            
class LocalURIParsingTest(unittest.TestCase):
    uris = (("file:///abs/path", "/abs/path"),
            ("file://rel/path", "rel/path"),
            ("file:///", "/"))
       
    def testToPath(self):
        for uri, path  in self.uris:
            p = Path.fromURI(uri)
            self.assertEqual(path, p.path)
            self.assertEqual("file", p.protocol)
            self.assertEqual(None, p.hostname)
            self.assertEqual(None, p.username)
            self.assertEqual(None, p.port)
            
    def testToStr(self):
        for uri, path  in self.uris:
            p = Path.fromURI(uri)
            self.assertEqual(uri, str(p))
      
            
class RemoteURIParsingTest(unittest.TestCase):
    uris = (
            ("smb://bob@fileserver/share/subdir",
                {'path':     "/share/subdir",
                 'protocol': "smb",
                 'hostname': "fileserver",
                 'username': "bob",
                 'port':     None}),
            ("https://joe@host.domain.org", 
                {'path':     "",
                  'protocol': "https",
                  'hostname': "host.domain.org",
                  'username': "joe",
                  'port':     None}),
            ("ftp://alice@ftp.example.com:21/~/inbox",
                {'path':     "/~/inbox", # FIXME: shouldn't it be "~/inbox"?
                 'protocol': "ftp",
                 'hostname': "ftp.example.com",
                 'username': "alice",
                 'port':     21}))
                                  
    def testToPath(self):
        for uri, d  in self.uris:
            p = Path.fromURI(uri)
            self.assertEqual(d['path'], p.path)
            self.assertEqual(d['protocol'], p.protocol)
            self.assertEqual(d['hostname'], p.hostname)
            self.assertEqual(d['username'], p.username)
            self.assertEqual(d['port'], p.port)
            
    def testToStr(self):
        for uri, d  in self.uris:
            p = Path.fromURI(uri)
            self.assertEqual(uri, str(p))
            
            
class InvalidURITest(unittest.TestCase):
    def testInvalidURIException(self):
        uri = "foobar"
        self.assertRaises(InvalidURI, Path.fromURI, uri)


if __name__ == "__main__":
    unittest.main()   
