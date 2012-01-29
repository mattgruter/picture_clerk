import unittest
import mock

from urlparse import urlparse

from connector import Connector
from connector import NotConnectedError


class TestConnector(Connector):
    _connect = None
    _disconnect = None
    _open = None
    _mkdir = None
    
    @classmethod
    def setup(cls):
        cls._connect = mock.Mock()
        cls._disconnect = mock.Mock()
        cls._mkdir = mock.Mock()
        
        # make sure that _open returns a (mocked) context manager
        mock_cm = mock.Mock()
        mock_cm.__enter__ = mock.Mock()
        mock_cm.__exit__ = mock.Mock()
        mock_cm.__exit__.return_value = False
        cls._open = mock.Mock(return_value=mock_cm)
            
    def __init__(self, url):
        Connector.__init__(self, url)
        # recreate all mock objects every time an instance is created
        self.setup()
    

class ConnectorObjectCreationTest(unittest.TestCase):
    
    def setUp(self):        
        self.url = urlparse("testurl")

    def testAttributes(self):
        """Init should store attributes and initialize all properties."""
        tc = TestConnector(self.url) 
        self.assertEqual(self.url, tc.url)

    def testNotConnected(self):
        """Init should set isconnected to False upon object creation."""
        tc = TestConnector(self.url) 
        self.assertFalse(tc.isconnected)
        
        
class ConnectorConnectTest(unittest.TestCase):
    
    def setUp(self):
        url = urlparse("testurl")
        self.tc = TestConnector(url) 
            
    def testConnect(self):
        """connect() should set isconnected flag."""
        self.tc.connect()
        self.assertTrue(self.tc._connect.called)
        self.assertTrue(self.tc.isconnected)
        
    def testDoubleConnect(self):
        """connect() if already connected should not change anything."""
        self.tc.connect()
        self.assertTrue(self.tc.isconnected)
        self.tc.connect()
        self.assertTrue(self.tc.isconnected)


class ConnectorDisconnectTest(unittest.TestCase):
    
    def setUp(self):
        url = urlparse("testurl")
        self.tc = TestConnector(url)
        self.tc.connect() 
            
    def testDisconnect(self):
        """disconnect() should clear isconnected flag."""
        self.tc.disconnect()
        self.assertTrue(self.tc._disconnect.called)
        self.assertFalse(self.tc.isconnected)
        
    def testDoubleDisconnect(self):
        """disconnect() if already disconnected should not change anything."""
        self.tc.disconnect()
        self.assertFalse(self.tc.isconnected)
        self.tc.disconnect()
        self.assertFalse(self.tc.isconnected)


class ConnectorOpenTest(unittest.TestCase):
    
    def setUp(self):
        url = urlparse("testurl")
        self.tc = TestConnector(url)
        
    def testOpenFail(self):
        """open() should raise NotConnectedError if !isconnected."""
        self.assertRaises(NotConnectedError, self.tc.open, 'path', 'rw')
        self.assertFalse(self.tc._open.called)
        
        
class ConnectorMkdirTest(unittest.TestCase):
    
    def setUp(self):
        url = urlparse("testurl")
        self.tc = TestConnector(url)
        
    def testMkdirFail(self):
        """mkdir() should raise NotConnectedError if !isconnected."""
        self.assertRaises(NotConnectedError, self.tc.mkdir, 'path', 'rw')
        self.assertFalse(self.tc._mkdir.called)
        
class ConnectorCopyTest(unittest.TestCase):

    def setUp(self):
        src_url = urlparse("testurl1")
        self.src_tc = TestConnector(src_url)
        dest_url = urlparse("testurl2")
        self.dest_tc = TestConnector(dest_url)
        
    def testCopyFail(self):
        """copy() should raise NotConnectedError if src is not connected."""
        self.assertRaises(NotConnectedError, self.src_tc.copy,
                          'src_path', self.dest_tc, 'dest_path')
        
    def testDestConnect(self):
        """copy() should connect destination connector."""
        self.src_tc.connect()
        self.dest_tc.disconnect()
        self.src_tc.copy('src_path', self.dest_tc, 'dest_path')
        self.assertTrue(self.dest_tc._connect.called)
        self.assertTrue(self.dest_tc._disconnect.called)
        
    

if __name__ == "__main__":
    unittest.main()   
