import unittest

from ..repo import *
from .. import config


class RepoObjectCreationTest(unittest.TestCase):
    connector = "testconnector"
    config_file = "testconfig_file"
    
    def testAttributes(self):
        """
        __init__ should store supplied attributes and initialize all properties
        """
        r = Repo(self.connector, config_file=self.config_file)
        self.assertEqual(self.connector, r.connector)
        self.assertEqual(self.config_file, r.config_file)
        self.assertEqual(None, r.config)
        self.assertEqual(None, r.index)
        
    def testAttributeDefaults(self):
        """
        __init__ should apply defaults to undefined attributes
        """
        r = Repo(self.connector)
        self.assertEqual(self.connector, r.connector)
        self.assertEqual(config.CONFIG_FILE, r.config_file)
        self.assertEqual(None, r.config)
        self.assertEqual(None, r.index)
        
        
class RepoConnectTest(unittest.TestCase):
    def setUp(self):
        """
        setup mock connector object and create Repo object
        """
        class MockConnector(object):
            def connect(self):
                self.connected = True
        self.connector = MockConnector()
        self.repo = Repo(self.connector, None)

    def testConnectorConnect(self):
        """
        connect should call connector's connect method
        """       
        self.repo.connect()
        self.assertTrue(self.connector.connected)
        

class RepoDisconnectTest(unittest.TestCase):
    def setUp(self):
        """
        setup mock connector object and create Repo object
        """
        class MockConnector(object):
            def disconnect(self):
                self.connected = False
        self.connector = MockConnector()
        self.repo = Repo(self.connector, None)

    def testConnectorDisconnect(self):
        """
        disconnect should call connector's disconnect method
        """       
        self.repo.disconnect()
        self.assertFalse(self.connector.connected) 


#class RepoLoadConfigTest(unittest.TestCase):

        
#class RepoLoadIndexTest(unittest.TestCase):


#class RepoWriteIndexTest(unittest.TestCase):
    

if __name__ == "__main__":
    unittest.main()   
