"""
Created on 2011/03/08

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import unittest
import mock

import config
import connector
from repo import Repo
from repo import RepoNotInitializedError, IndexMissingError, IndexParsingError


class ObjectCreationTest(unittest.TestCase):
    def setUp(self):
        self.connector = mock.Mock(spec_set=connector.Connector)
        self.pic_dir = "mock pic dir"
        self.config_file = "mock config file"
    
    def test_attributes(self):
        """
        Repo.__init__ should store attributes and initialize all properties
        """
        r = Repo(self.connector, pic_dir=self.pic_dir,
                 config_file=self.config_file)
        self.assertIsInstance(r, Repo)
        self.assertEqual(self.connector, r.connector)
        self.assertEqual(self.pic_dir, r.pic_dir)
        self.assertEqual(self.config_file, r.config_file)
        self.assertEqual(None, r.config)
        self.assertEqual(None, r.index)
        
    def test_attribute_defaults(self):
        """
        Repo.__init__ should apply defaults to undefined attributes
        """
        r = Repo(self.connector)
        self.assertIsInstance(r, Repo)
        self.assertEqual(self.connector, r.connector)
        self.assertEqual(config.PIC_DIR, r.pic_dir)
        self.assertEqual(config.CONFIG_FILE, r.config_file)
        self.assertEqual(None, r.config)
        self.assertEqual(None, r.index)
        

class ConnectTest(unittest.TestCase):
    def setUp(self):
        self.connector = mock.Mock(spec_set=connector.Connector)
        self.repo = Repo(self.connector, None)
        self.repo.load_config = mock.Mock()
        
    def test_connect(self):
        """
        Repo.connect should call connector's connect method and load config
        """
        self.repo.connect()
        self.connector.connect.assert_called_with()
        self.repo.load_config.assert_called_once_with()
        
    def test_raise_repo_not_initialized(self):
        """
        Repo.connect raises RepoNotInitializedError if load_config fails
        """
        self.repo.load_config.side_effect = IOError()
        self.assertRaises(RepoNotInitializedError, self.repo.connect)
        self.connector.disconnect.assert_called_with()
    

class DisconnectTest(unittest.TestCase):
    def setUp(self):
        self.connector = mock.Mock(spec_set=connector.Connector)
        self.repo = Repo(self.connector, None)

    def test_disconnect(self):
        """
        Repo.disconnect should call connector's disconnect method
        """       
        self.repo.disconnect()
        self.connector.disconnect.assert_called_with()
        

class InitRepoTest(unittest.TestCase):
    def setUp(self):
        # mock Connector
        self.connector = mock.Mock(spec_set=connector.Connector)
        
        # create Repo instance and mock methods called by init_repo
        self.pic_dir = "mock_pic_dir"
        self.repo = Repo(self.connector, self.pic_dir)
        self.repo._create_default_config = mock.Mock()
        self.repo.write_config = mock.Mock()
        self.repo.write_index = mock.Mock()
        
    def test_init_repo(self):
        """
        Repo.init_repo should create pic directory, create the default config,
        write the config to file and write the index to file
        """       
        self.repo.init_repo()
        self.connector.mkdir.assert_called_once_with(self.pic_dir)
        self.repo._create_default_config.assert_called_once_with()
        self.repo.write_config.assert_called_once_with()
        self.repo.write_index.assert_called_once_with()
        

@mock.patch('ConfigParser.ConfigParser')    
class LoadConfigTest(unittest.TestCase):
    def setUp(self):
        # mocking Connector
        self.connector = mock.Mock(spec_set=connector.Connector)
        self.mock_open = self.connector.open
        self.mock_open.return_value = mock.MagicMock(spec=file)
        
        # create Repo instance
        self.config_file = "mock_config_path"
        self.repo = Repo(self.connector, config_file=self.config_file)

    def tearDown(self):
        pass
    
    def test_load_config(self, MockConfigParser):
        """
        Repo.load_config should create a ConfigParser instance and populate it
        with ConfigParser's readfp method from  
        """
        # execute method under test
        self.repo.load_config()
        # connector's open method should be called with correct config file path
        self.assertIn(self.config_file, self.mock_open.call_args[0])
        # config should be read from mocked file handle 
        file_handle = self.mock_open.return_value.__enter__.return_value
        config_instance = MockConfigParser.return_value
        self.assertEqual(config_instance, self.repo.config)
        config_instance.readfp.assert_called_with(file_handle)

                
class WriteConfigTest(unittest.TestCase):
    def setUp(self):
        # mock Connector
        self.connector = mock.Mock(spec_set=connector.Connector)
        self.mock_open = self.connector.open
        self.mock_open.return_value = mock.MagicMock(spec=file)
        
        # create Repo instance and mock config attribute
        self.config_file = "mock_config_path"
        self.repo = Repo(self.connector, config_file=self.config_file)
        self.mock_write = mock.Mock()
        self.repo.config = mock.Mock()
        self.repo.config.write = self.mock_write

    def tearDown(self):
        pass
    
    def test_write_config(self):
        """
        Repo.write_config should call config's write with the file handle
        pointing to the config file 
        """
        # execute method under test
        self.repo.write_config()
        # connector's open method should be called with correct config file path
        self.assertIn(self.config_file, self.mock_open.call_args[0])
        # config should be written to mocked file handle 
        file_handle = self.mock_open.return_value.__enter__.return_value
        self.mock_write.assert_called_once_with(file_handle)
        

@mock.patch('repo.pickle')          
class LoadWriteIndexTest(unittest.TestCase):
    def setUp(self):
        # mock Connector
        self.connector = mock.Mock(spec_set=connector.Connector)
        self.mock_open = self.connector.open
        self.mock_open.return_value = mock.MagicMock(spec=file)
        
        # create Repo instance, mock its index, index_file and config attribute
        self.mock_index_file = "mock index path"
        self.mock_config = mock.Mock()
        self.mock_config.get.return_value = self.mock_index_file
        self.repo = Repo(self.connector) 
        self.repo.config = self.mock_config

    def tearDown(self):
        pass
    
    def test_load_index(self, mock_pickle):
        """
        Repo.load_index should fetch the index file path from config, open this
        index file path and unpickle the index from it.  
        """
        # execute method under test                
        self.repo.load_index()
        
        # index file path should be fetched from repo's config instance
        self.repo.config.get.assert_called_with("core", "index_file")
        # connector's open method should be called with correct index file path
        self.assertIn(self.mock_index_file, self.mock_open.call_args[0])
        # index should be read from mocked file handle 
        file_handle = self.mock_open.return_value
        mock_pickle.load.assert_called_with(file_handle)
        self.repo.index = mock_pickle.load.return_value
        
    def test_load_raise_index_missing_error(self, mock_pickle):
        """
        Repo.load_index should raise a IndexMissingError exception if the index
        file can not be opened.
        """
        self.mock_open.side_effect = IOError("mock IO error")
        
        # execute method under test
        self.assertRaises(IndexMissingError, self.repo.load_index)
        
    def test_load_raise_index_parsing_error(self, mock_pickle):
        """
        Repo.load_index should raise a IndexParsingError exception if unpickling
        fails and close the index file handle.
        """
        mock_pickle.UnpicklingError = Exception
        mock_pickle.load.side_effect = mock_pickle.UnpicklingError("mock error")
        
        # execute method under test
        self.assertRaises(IndexParsingError, self.repo.load_index)

        # index file handle should be closed if unpickling fails
        file_handle = self.mock_open.return_value
        file_handle.close.assert_called_with()
    
    def test_write_index(self, mock_pickle):
        """
        Repo.write_index should fetch the index file path from config, open this
        index file path and pickle.dump the index to it. 
        """
        mock_index = "mock index"
        self.repo.index = mock_index  

        # execute method under test
        self.repo.write_index()
        # connector's open method should be called with correct config file path
        self.assertIn(self.mock_index_file, self.mock_open.call_args[0])
        # index should be pickle.dumped to file_handle
        file_handle = self.mock_open.return_value.__enter__.return_value
        mock_pickle.dump.assert_called_once_with(mock_index, file_handle)


if __name__ == "__main__":
    unittest.main()   
