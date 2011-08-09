"""
Created on 2011/08/09

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import unittest
import mock

import connector

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
        

if __name__ == "__main__":
    unittest.main()