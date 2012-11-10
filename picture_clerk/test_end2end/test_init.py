"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import unittest
import subprocess
import os
import shutil
import tempfile
import mock

from cli import CLI


def create_temp_dir():
    return tempfile.mkdtemp(prefix="pic")
    

class End2EndTest(unittest.TestCase):

    def create_patch(self, name):
        patcher = mock.patch(name)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def setUp(self):
        self.mock_sys_exit = self.create_patch('sys.exit')

        self.origcwd = os.getcwd()
        self.tempdir = create_temp_dir()
        os.chdir(self.tempdir)

        self.cli = CLI()

    def tearDown(self):
        self.cli.shutdown(0)
        os.chdir(self.origcwd)
        print "removing %s" % self.tempdir
        shutil.rmtree(self.tempdir)


class InitRepoTests(End2EndTest):

    def setUp(self):
        End2EndTest.setUp(self)

    def test_init_repo(self):
    
        print "using %s" % self.tempdir
        self.cli.main(['progname', 'init'])

        self.assertTrue(os.path.exists('.pic'),
                        "PictureClerk control directory '.pic' not found.")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
