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

from repo_factory import RepoFactory


@mock.patch('repo.Repo', spec_set=True)
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
        fh = self.connector.open.return_value
        # check that correct repo instance is returned
        self.assertEqual(instance, result)
        # check that connector is activated
        self.connector.connect.assert_called_once_with()
        # check that pic dir is created
        self.connector.mkdir.assert_called_once_with(config.PIC_DIR)
        # check that default config is created and written to file
        result.create_default_config.assert_called_once_with()
        self.assertIn(((config.CONFIG_FILE, 'wb'), {}),
                        self.connector.open.call_args_list)
        result.write_config.assert_called_once_with(fh)
        # check that index is written to file
        self.assertIn(((config.INDEX_FILE, 'wb'), {}),
                        self.connector.open.call_args_list)
        result.write_index.assert_called_once_with(fh)
    
    def test_create_and_init_dir(self, MockRepo):
        """
        RepoFactory.create_and_init_dir should call Connector.mkdir, instantiate
        a Repo object (return value) and call its init_repo method.
        """
        instance = MockRepo.return_value
        result = RepoFactory.init_dir(self.connector, create_dir=True)
        # check that correct repo instance is returned
        self.assertEqual(instance, result)
        # check that repo dir is created
        self.assertIn((('.',), {}), self.connector.mkdir.call_args_list)
        
    def test_disconnect_after_fail(self, MockRepo):
        """
        RepoFactory.init_dir should disconnect if exception occurs.
        """
        self.connector.mkdir.side_effect = Exception("test exception")
        # check that mock exception is re-raised
        self.assertRaises(Exception,
                          RepoFactory.init_dir, self.connector)
        # check that disconnect method is called
        self.connector.disconnect.assert_called_once_with()
 
 
class CloneTest(unittest.TestCase):
    def setUp(self):
        # mock connector for the source repo
        self.src_connector = mock.Mock()
#        self.src_connector.open.return_value = mock.MagicMock()
        
        # mock connector for the destination repo
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
        src_repo = repo.Repo()
        src_repo.load_config = lambda x: None
        src_repo.config = mock.Mock()
        src_repo.load_index = lambda x: None
        class MockPic(object):
            def __init__(self, pic):
                self.pic = pic
            def __eq__(self, other):
                return self.pic == other.pic
            def __repr__(self):
                return "MockPic(%)" % self.pic
        pic = MockPic('mock picture')
        pic.get_filenames = mock.Mock(return_value=['filename1', 'filename2'])
        src_repo.index = [pic]
        
        # execute method under test
        dest_repo = RepoFactory.clone_repo(src_repo, self.src_connector,
                                           self.dest_connector)
        
        # compare all attributes of src_repo and dest_repo 
        for key, value in src_repo.__dict__.items():
            if key not in ['load_config', 'load_index']:
                self.assertEqual(dest_repo.__dict__[key], value,
                                 "%s not equal" % key)
        
        # TODO: compare that all picture files are copied
        #self.repo.check_index()
        

if __name__ == "__main__":
    unittest.main()