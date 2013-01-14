"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import unittest
import mock

from urlparse import urlparse

from connector import Connector
from connector import NotConnectedError


class TestConnector(Connector):
    _connect = None
    _disconnect = None
    _open = None
    _exists = None
    _mkdir = None
    _remove = None

    def setup(self):
        self._connect = mock.Mock()
        self._disconnect = mock.Mock()
        self._exists = mock.Mock()
        self._mkdir = mock.Mock()
        self._remove = mock.Mock()

        # make sure that _open returns a (mocked) context manager
        mock_cm = mock.Mock()
        mock_cm.__enter__ = mock.Mock()
        mock_cm.__exit__ = mock.Mock()
        mock_cm.__exit__.return_value = False
        self._open = mock.Mock(return_value=mock_cm)

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


class ConnectorExistsTest(unittest.TestCase):

    def setUp(self):
        url = urlparse("testurl")
        self.tc = TestConnector(url)

    def testExistsTest(self):
        """exists() should raise NotConnectedError if !isconnected."""
        self.assertRaises(NotConnectedError, self.tc.exists, 'path')
        self.assertFalse(self.tc._exists.called)


class ConnectorMkdirTest(unittest.TestCase):

    def setUp(self):
        url = urlparse("testurl")
        self.tc = TestConnector(url)

    def testMkdirFail(self):
        """mkdir() should raise NotConnectedError if !isconnected."""
        self.assertRaises(NotConnectedError, self.tc.mkdir, 'path', 755)
        self.assertFalse(self.tc._mkdir.called)


class ConnectorRemoveTest(unittest.TestCase):

    def setUp(self):
        url = urlparse("testurl")
        self.tc = TestConnector(url)

    def testExistsTest(self):
        """remove() should raise NotConnectedError if !isconnected."""
        self.assertRaises(NotConnectedError, self.tc.remove, 'path')
        self.assertFalse(self.tc._mkdir.called)


class ConnectorCopyTest(unittest.TestCase):

    def setUp(self):
        src_url = urlparse("testurl1")
        self.src_tc = TestConnector(src_url)
        self.src_tc.connect()

        dest_url = urlparse("testurl2")
        self.dest_tc = TestConnector(dest_url)
        self.dest_tc.connect()

    def tearDown(self):
        self.src_tc.disconnect()
        self.dest_tc.disconnect()

    def testCopyFailSrcDisconnected(self):
        """copy() should raise NotConnectedError if src is not connected."""
        self.src_tc.disconnect()
        self.assertRaises(NotConnectedError, self.src_tc.copy,
                          'src_path', self.dest_tc, 'dest_path')

    def testCopyFailDestDisconnected(self):
        """copy() should raise NotConnectedError if dest is not connected."""
        self.dest_tc.disconnect()
        self.assertRaises(NotConnectedError, self.src_tc.copy,
                          'src_path', self.dest_tc, 'dest_path')

    def testCopy(self):
        """copy() should open src path for reading and dest path for writing."""
        self.src_tc.connect()
        self.dest_tc.connect()
        self.src_tc.copy('src_path', self.dest_tc, 'dest_path')

        src_abspath = self.src_tc._rel2abs('src_path')
        dest_abspath = self.dest_tc._rel2abs('dest_path')
        self.src_tc._open.assert_called_once_with(src_abspath, 'r')
        self.dest_tc._open.assert_called_once_with(dest_abspath, 'w')


if __name__ == "__main__":
    unittest.main()
