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

from repo_factory import RepoFactory


@mock.patch('repo.Repo')
class Test(unittest.TestCase):
    def setUp(self):
        self.connector = mock.Mock(spec_set=connector.Connector)

    def tearDown(self):
        pass

    def test_init_dir(self, MockRepo):
        """
        RepoFactory.init_dir should instantiate a Repo object (return value) and
        call its init_repo method.
        """
        instance = MockRepo.return_value
        result = RepoFactory.init_dir(self.connector)
        self.assertEqual(instance, result)
        self.connector.connect.assert_called_once_with()
        result.init_repo.assert_called_with()
    
    def test_create_and_init_dir(self, MockRepo):
        """
        RepoFactory.create_and_init_dir should call Connector.mkdir, instantiate
        a Repo object (return value) and call its init_repo method.
        """
        instance = MockRepo.return_value
        result = RepoFactory.create_and_init_dir(self.connector)
        self.assertEqual(instance, result)
        self.connector.connect.assert_called_with()
        self.connector.mkdir.assert_called_once_with('.')
        result.init_repo.assert_called_once_with()
        
    def test_disconnect_after_fail(self, MockRepo):
        """
        RepoFactory.init_dir should disconnect if exception occurs.
        """
        self.connector.connect.side_effect = Exception("test exception")
        self.assertRaises(Exception,
                          RepoFactory.init_dir, self.connector)
        self.connector.disconnect.assert_called_once_with()
 
 
class CloneTest(unittest.TestCase):
    def setUp(self):
        # mock connector of the source repo
        self.src_connector = mock.Mock()
#        self.src_connector.open.return_value = mock.MagicMock()
        
        # mock connector of the destination repo
        self.dest_connector =  mock.Mock()
#        self.dest_connector.open.return_value = mock.MagicMock()
        mock_open = self.dest_connector.open
        mock_open.return_value = mock.Mock()
        mock_open.return_value.__enter__ = mock.Mock()
        mock_open.return_value.__exit__ = mock.Mock()

    def tearDown(self):
        pass
           
    def test_clone_repo(self):
        """
        RepoFactory.clone_repo
        """
        # create source repo with mocked config, index and load_ methods
        mock_pic_dir = "mock pic dir"
        mock_config_file = "mock config file"
        src_repo = repo.Repo(self.src_connector, mock_pic_dir, mock_config_file)
        src_repo.load_config = lambda: None
        src_repo.config = "mock config"
        src_repo.load_index = lambda: None
        class MockPic(object):
            def __init__(self, pic):
                self.pic = pic
            def __eq__(self, other):
                return self.pic == other.pic
        pic = MockPic('mock picture')
        pic.get_filenames = mock.Mock(return_value=['filename1', 'filename2'])
        src_repo.index = [pic]
        
        # execute method under test
        dest_repo = RepoFactory.clone_repo(src_repo, self.dest_connector)
        
        # make sure that src_repo's connector was not cloned, but instead the
        # supplied dest_connector used.
        self.assertNotEqual(self.src_connector, dest_repo.connector)
        self.assertEqual(self.dest_connector, dest_repo.connector)
        # compare all attributes of src_repo and dest_repo 
        for key, value in src_repo.__dict__.items():
            if key not in ['connector', 'load_config', 'load_index']:
                self.assertEqual(dest_repo.__dict__[key], value,
                                 "%s not equal" % key)
        
        # TODO: compare that all picture files are copied
        #self.repo.check_index()
        

if __name__ == "__main__":
    unittest.main()