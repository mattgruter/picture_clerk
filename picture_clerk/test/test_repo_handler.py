"""
Created on 2011/08/09

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import unittest
import StringIO
import ConfigParser

from repo_handler import RepoHandler, IndexParsingError

class IndexTest(unittest.TestCase):
    def setUp(self):
        self.handler = RepoHandler(repo=None, config=None, connector=None)
        self.fh = StringIO.StringIO() # file-like string buffer
    
    def tearDown(self):
        self.fh.close()
  
    def test_dump_read_index(self):
        """Do dump-read index cycle and compare start with end index."""
        index_a = ["Test index item 1", "Test index item 2"]
        self.handler.dump_index(index_a, self.fh)
        self.fh.seek(0) # rewind buffer
        index_b = self.handler.read_index(self.fh)
        self.assertEqual(index_a, index_b, "Dumped and read index don't match.")
        self.assertIsNot(index_a, index_b, "Dumped and read index is same obj.")
        
    def test_read_index_error(self):
        """Should raise IndexParsingError if index unreadable."""
        # creating buffer content that can't be unpickled
        corrupt_buf = "42\n"
        self.fh.write(corrupt_buf)
        self.assertRaises(IndexParsingError, self.handler.read_index, self.fh)
        

class ConfigTest(unittest.TestCase):
    def setUp(self):
        # test ConfigParser instance
        cp = ConfigParser.SafeConfigParser()
        cp.add_section("test")
        cp.set("test", "option1", "test option1")
        cp.set("test", "option2", "test option 2")
        self.handler = RepoHandler(repo=None, config=cp, connector=None)

        # dump test object
        self.fh = StringIO.StringIO() # file-like string buffer
        cp.write(self.fh)
        self.fh.seek(0) # rewind buffer
    
    def tearDown(self):
        self.fh.close()
    
    def test_read_config(self):
        """read_config should load ConfigParser instance from file handle."""
        # compare ConfigParser instance
        conf = self.handler.read_config(self.fh)
        self.assertIsNot(conf, self.handler.config)

        # compare config sections
        secs_a = self.handler.config.sections()
        secs_b = conf.sections()
        self.assertEqual(
                 secs_b, secs_a,
                 msg="config sections not equal: %s != %s" % (secs_b, secs_a))
        
        # compare config opts_a
        for section in secs_a:
            opts_a = self.handler.config.options(section)
            opts_b = conf.options(section)
            self.assertEqual(
                    opts_b, opts_a,
                    msg="config options in section '%s' not equal: " % section +
                        "%s != %s" % (opts_b, opts_a))
    
    def test_dump_config(self):
        """Return value from dump_config should match dump created in setUp"."""
        # expected dump
        buf = self.fh.readlines()
        # test dump
        test_fh = StringIO.StringIO()
        self.handler.dump_config(self.handler.config, test_fh)
        test_fh.seek(0) # rewind test buffer
        test_buf = test_fh.readlines()
        self.assertEqual(test_buf, buf)
        
    def test_create_default_config(self):
        """create_default_config should return ConfigParser instance."""
        conf = RepoHandler.create_default_config()
        self.assertIsInstance(conf, ConfigParser.ConfigParser)
        
        
if __name__ == "__main__":
    unittest.main()
