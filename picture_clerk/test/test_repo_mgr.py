"""
Created on 2011/08/09

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import unittest
import mock

import connector
import repo
import config

from repo_mgr import RepoMgr


@mock.patch('repo.Repo')
class Test(unittest.TestCase):
    def setUp(self):
        self.connector = mock.Mock(spec_set=connector.Connector)

    def tearDown(self):
        pass

    def test_init_dir(self, MockRepo):
        """
        RepoMgr.init_dir should instantiate a Repo object (return value) and
        call its init_repo method.
        """
        instance = MockRepo.return_value
        result = RepoMgr.init_dir(self.connector)
        fh = self.connector.open.return_value
        # check that correct repo instance is returned
        self.assertEqual(instance, result)
        # check that connector is activated
        self.connector.connect.assert_called_once_with()
        # check that pic dir is created
        self.connector.mkdir.assert_called_once_with(config.PIC_DIR)
        # check that default config is created and written to file
        self.assertIn(((config.CONFIG_FILE, 'wb'), {}),
                        self.connector.open.call_args_list)
        result.write_config.assert_called_once_with(fh)
        # check that index is written to file
        self.assertIn(((config.INDEX_FILE, 'wb'), {}),
                        self.connector.open.call_args_list)
        result.write_index.assert_called_once_with(fh)
    
    def test_create_and_init_dir(self, MockRepo):
        """
        RepoMgr.create_and_init_dir should call Connector.mkdir, instantiate
        a Repo object (return value) and call its init_repo method.
        """
        instance = MockRepo.return_value
        result = RepoMgr.init_dir(self.connector, create_dir=True)
        # check that correct repo instance is returned
        self.assertEqual(instance, result)
        # check that repo dir is created
        self.assertIn((('.',), {}), self.connector.mkdir.call_args_list)
        
    def test_disconnect_after_fail(self, MockRepo):
        """
        RepoMgr.init_dir should disconnect if exception occurs.
        """
        self.connector.mkdir.side_effect = Exception("test exception")
        # check that mock exception is re-raised
        self.assertRaises(Exception,
                          RepoMgr.init_dir, self.connector)
        # check that disconnect method is called
        self.connector.disconnect.assert_called_once_with()
 
 
class MockPic(object):
    def __init__(self, pic):
        self.pic = pic
    def __eq__(self, other):
        return self.pic == other.pic
    def __repr__(self):
        return "MockPic(%s)" % self.pic
    
class MockConfig(object):
    def __init__(self, conf):
        self.conf = conf
    def __eq__(self, other):
        return self.conf == other.conf
    def __repr__(self):
        return "MockConfig(%s)" % self.pic
    def write(self, fh):
        pass

@mock.patch('repo.Repo.write_index')
class CloneTest(unittest.TestCase):
    def setUp(self):
        # mock connector for source and destination repos
        self.src_connector = mock.Mock(spec_set=connector.Connector)
        self.dest_connector = mock.Mock(spec_set=connector.Connector)

    def tearDown(self):
        pass
        
    def test_clone_repo(self, mock_write_index):
        # setup source repo
        src_config = MockConfig("mock config")
        pic = MockPic('mock picture')
        pic.get_filenames = mock.Mock(return_value=['filename1', 'filename2'])
        src_index = [pic]
        src_repo = repo.Repo(src_config, src_index)
        src_repo.load_config = mock.Mock()
        src_repo.load_config = mock.Mock()
        
        # clone source repo
        dest_repo = RepoMgr.clone_repo(src_repo, self.src_connector,
                                           self.dest_connector)
        
        self.assertIsInstance(dest_repo, repo.Repo)
        # check that index & config are equal copies
        self.assertEqual(src_repo.config, dest_repo.config)
        self.assertIsNot(src_repo.config, dest_repo.config)
        self.assertEqual(src_repo.index, dest_repo.index)
        self.assertIsNot(src_repo.index, dest_repo.index)
        

if __name__ == "__main__":
    unittest.main()