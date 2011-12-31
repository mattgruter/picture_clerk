"""
Created on 2011/08/09

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import unittest
import mock
import StringIO
import ConfigParser

import connector
import repo
import config

from repo_handler import RepoHandler, IndexParsingError
from repo import Repo

class IndexTest(unittest.TestCase):
    def setUp(self):
        self.repo = mock.Mock()
        self.repo.index = ["Test index item 1", "Test index item 2"]
        self.rh = RepoHandler(self.repo)
        # create file-like string buffer
        self.index_fh = StringIO.StringIO()
    
    def tearDown(self):
        self.index_fh.close()
  
    def test_load_save_index(self):
        """Do a save-load index cycle and compare loaded index with index that
        started with."""
        other_repo = mock.Mock()
        other_repo.index = []
        other_rh = RepoHandler(other_repo)
        # dump/save index of test repo
        self.rh.save_index(self.index_fh)
        # rewind buffer
        self.index_fh.seek(0)
        # load saved index into other repo
        other_rh.load_index(self.index_fh)
        self.assertEqual(self.repo.index, other_repo.index,
                         msg="Saved and loaded index do not match")
        self.assertIsNot(self.repo.index, other_repo.index,
                         msg="Each repo should have their own copy of the " +\
                             "index. But they reference the same object.")
        
    def test_load_index_error(self):
        """RepoHandler.load_index should raise IndexParsingError if index
        unreadable"""
        # creating buffer content that can't be unpickled
        corrupt_buf = "42\n"
        self.index_fh.write(corrupt_buf)
        self.assertRaises(IndexParsingError, self.rh.load_index, self.index_fh)
        

class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.repo = mock.Mock()
        self.rh = RepoHandler(self.repo)
        self.cp = ConfigParser.SafeConfigParser()
        self.cp.add_section("test")
        self.option1 = "test option1"
        self.cp.set("test", "option1", self.option1)
        self.option2 = "test option 2"
        self.cp.set("test", "option2", self.option2)
        # create file-like string buffer
        self.config_fh = StringIO.StringIO()
        # write test config to buffer
        self.cp.write(self.config_fh)
        # rewind buffer
        self.config_fh.seek(0)
    
    def tearDown(self):
        self.config_fh.close()
    
    def test_load_config(self):
        """RepoHandler.load_config should load configuration options from the
        supplied file handle."""
        self.rh.load_config(self.config_fh)
        sections = self.cp.sections()
        repo_sections = self.repo.config.sections()
        self.assertEqual(repo_sections, sections,
            msg="config sections should match " +
                "%s != %s" % (repo_sections, sections))
        for section in sections:
            options = self.cp.options(section)
            repo_options = self.repo.config.options(section)
            self.assertEqual(repo_options, options,
                msg="options in section '%s' should match: " % section +
                    "%s != %s" % (repo_options, options))
        self.assertIsNot(self.cp, self.repo.config)
        
    def test_save_config(self):
        """Config file dump from RepoHandler.save_config should match dump
        created in setUp method."""
        # expected
        config_buf = self.config_fh.readlines()
        # test dump
        test_config_fh = StringIO.StringIO()        
        self.repo.config = self.cp
        self.rh.save_config(test_config_fh)
        test_config_fh.seek(0)
        test_config_buf = test_config_fh.readlines()
        self.assertEqual(test_config_buf, config_buf)
         
        
class InitDirTest(unittest.TestCase):
    def setUp(self):
        self.repo = mock.Mock(spec_set=repo.Repo)
        self.rh = mock.Mock(spec=RepoHandler)
        self.rh.repo = self.repo
        self.connector = mock.Mock(spec_set=connector.Connector)

    def tearDown(self):
        pass

    def test_init_dir(self):
        """
        RepoHandler.init_dir should create necessary subdirectories.
        """
        RepoHandler.init_dir(self.rh, self.connector)
        fh = self.connector.open.return_value
        # check that connector is activated
        self.connector.connect.assert_called_once_with()
        # check that pic dir is created
        self.connector.mkdir.assert_called_once_with(config.PIC_DIR)
        # check that default config is created and written to file
        self.assertIn(((config.CONFIG_FILE, 'wb'), {}),
                        self.connector.open.call_args_list)
        self.rh.save_config.assert_called_once_with(fh)
        # check that index is written to file
        self.assertIn(((config.INDEX_FILE, 'wb'), {}),
                        self.connector.open.call_args_list)
        self.rh.save_index.assert_called_once_with(fh)
    
    def test_create_and_init_dir(self):
        """
        RepoHandler.init_dir should create repo directory if create_dir is set
        to True.
        """
        RepoHandler.init_dir(self.rh, self.connector, create_dir=True)
        # mkdir should have been called twice ('.' & '.pic')
        self.assertEqual(self.connector.mkdir.call_count, 2)
        # check that correct directories were created
        self.assertIn((('.',), {}), self.connector.mkdir.call_args_list)
        self.assertIn(((config.PIC_DIR,), {}), self.connector.mkdir.call_args_list)
        
    def test_disconnect_after_fail(self):
        """
        RepoHandler.init_dir should disconnect if exception occurs.
        """
        # force connector to throw exception
        self.connector.mkdir.side_effect = Exception("test exception")
        # check that mock exception is re-raised
        self.assertRaises(Exception,
                          RepoHandler.init_dir, self.rh, self.connector)
        # check that disconnect method is called
        self.connector.disconnect.assert_called_once_with()
 
 
class MockPic(object):
    def __init__(self, pic):
        self.pic = pic
    def __eq__(self, other):
        return self.pic == other.pic
    def __repr__(self):
        return "MockPic(%s)" % self.pic
    def get_filenames(self):
        return ['filename1', 'filename2']
    
class MockConfig(object):
    def __init__(self, conf):
        self.conf = conf
    def __eq__(self, other):
        return self.conf == other.conf
    def __repr__(self):
        return "MockConfig(%s)" % self.conf

class CloneTest(unittest.TestCase):
    def setUp(self):
        src_repo = repo.Repo([])
        self.src_rh = mock.Mock(spec=RepoHandler)
        self.src_rh.repo = src_repo
        self.src_connector = mock.Mock(spec_set=connector.Connector)
        
        dest_repo = repo.Repo([])
        self.dest_rh = mock.Mock(spec=RepoHandler)
        self.dest_rh.repo = dest_repo
        self.dest_connector = mock.Mock(spec_set=connector.Connector)

    def tearDown(self):
        pass
        
    def test_clone_repo(self):
        # setup source repo's config
        test_config = MockConfig("mock config")
        self.src_rh.repo.config = test_config

        # setup source repo's index
        pic = MockPic('mock picture')
        test_index = [pic]
        self.src_rh.repo.index = test_index
        
        # clone source repo
        RepoHandler.clone_repo(self.src_rh, self.src_connector,
                               self.dest_rh, self.dest_connector)
        
        # dest repo's config should be a exact copy of src repo's config
        self.assertEqual(self.dest_rh.repo.config, test_config)
        self.assertIsNot(self.dest_rh.repo.config, test_config)
        
        # dest repo's index should be a exact copy of src repo's index
        self.assertEqual(self.dest_rh.repo.index, test_index)
        self.assertIsNot(self.dest_rh.repo.index, test_index)
        
        
if __name__ == "__main__":
    unittest.main()
