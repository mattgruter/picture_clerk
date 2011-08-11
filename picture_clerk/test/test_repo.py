"""
Created on 2011/03/08

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import unittest
import mock

import config
from repo import Repo
from repo import RepoNotInitializedError, IndexParsingError


class ObjectCreationTest(unittest.TestCase):
    def setUp(self):
        self.pic_dir = "mock pic dir"
    
    def test_attributes(self):
        """
        Repo.__init__ should store attributes and initialize all properties
        """
        r = Repo(pic_dir=self.pic_dir)
        self.assertIsInstance(r, Repo)
        self.assertEqual(self.pic_dir, r.pic_dir)
        self.assertEqual(None, r.config)
        self.assertEqual(set(), r.index)
        
    def test_attribute_defaults(self):
        """
        Repo.__init__ should apply defaults to undefined attributes
        """
        r = Repo()
        self.assertIsInstance(r, Repo)
        self.assertEqual(config.PIC_DIR, r.pic_dir)
        self.assertEqual(None, r.config)
        self.assertEqual(set(), r.index)
     
     
#@mock.patch('ConfigParser.ConfigParser')    
class ConfigTest(unittest.TestCase):
    def setUp(self):
        # create Repo instance
        self.repo = Repo()
        # mock file handle
        self.config_fh = mock.Mock(spec_set=file)
        # mock config instance & patch ConfigParser
        self.patcher = mock.patch('ConfigParser.ConfigParser')
        self.mock_config_parser = self.patcher.start()
        self.mock_config = self.mock_config_parser.return_value

    def tearDown(self):
        self.patcher.stop()

    def test_load_config(self):
        """
        Repo.load_config should create a ConfigParser instance and populate it
        with ConfigParser's readfp method from the file handle provided. 
        """
        # execute method under test
        self.repo.load_config(self.config_fh)
        # config should be read from mocked file handle 
        self.assertEqual(self.mock_config, self.repo.config)
        self.mock_config.readfp.assert_called_with(self.config_fh)

    def test_write_config(self):
        """
        Repo.write_config should call config's write method with the file handle
        provided.
        """
        # mock repo's config
        self.repo.config = self.mock_config
        # execute method under test
        self.repo.write_config(self.config_fh)
        # config should be written to mocked file handle 
        self.mock_config.write.assert_called_once_with(self.config_fh)
        
        
#@mock.patch('repo.pickle')          
class IndexTest(unittest.TestCase):
    def setUp(self):
        # create Repo instance
        self.repo = Repo()
        # mock file handle
        self.index_fh = mock.Mock(spec_set=file)
        # mock index instance & patch ConfigParser
        self.patcher = mock.patch('repo.pickle')
        self.mock_pickle = self.patcher.start()
        self.mock_index = 'mock index'
        self.mock_pickle.load.return_value = self.mock_index
        
    def tearDown(self):
        self.patcher.stop()
    
    def test_load_index(self):
        """
        Repo.load_index should unpickle the index from the supplied file handle.  
        """
        # execute method under test                
        self.repo.load_index(self.index_fh)
        # index should be read from mocked file handle 
        self.mock_pickle.load.assert_called_with(self.index_fh)
        self.assertEqual(self.repo.index, self.mock_index)
        
    def test_load_raise_index_parsing_error(self):
        """
        Repo.load_index should raise a IndexParsingError exception if unpickling
        fails.
        """
        # mock pickle'r UnpicklingError
        self.mock_pickle.UnpicklingError = Exception
        self.mock_pickle.load.side_effect = \
            self.mock_pickle.UnpicklingError("mock error")
        # execute method under test
        self.assertRaises(IndexParsingError, self.repo.load_index, self.index_fh)
    
    def test_write_index(self):
        """
        Repo.write_index should write the index to the supplied file handle. 
        """
        # mock repo's index
        self.repo.index = self.mock_index  
        # execute method under test
        self.repo.write_index(self.index_fh)
    
        # index should be pickle.dumped to file_handle
        self.mock_pickle.dump.assert_called_with(self.mock_index, self.index_fh)


if __name__ == "__main__":
    unittest.main()   
