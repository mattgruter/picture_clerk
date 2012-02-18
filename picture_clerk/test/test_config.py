"""
Created on 2012/02/12

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import unittest
import mock
import StringIO
import ConfigParser
import collections

from config import Config


class BasicTests(unittest.TestCase):

    def test_type(self):
        c = Config()
        self.assertIsInstance(c, collections.MutableMapping)

    def test_add(self):
        c = Config()
        c['section.option'] = "value"
        self.assertEqual(c['section.option'], "value")

    def test_missing_key(self):
        c = Config()
        self.assertRaises(KeyError, c.__getitem__, 'section.option')

    def test_illegal_key(self):
        c = Config()
        self.assertRaises(KeyError, c.__setitem__, 'illegalkey', 'value')

    def test_update(self):
        c = Config()
        c['section.option'] = "value"
        c['section.option'] = "new value"
        self.assertEqual(c['section.option'], "new value")

    def test_membership(self):
        c = Config()
        c['section.option1'] = "value"
        self.assertTrue('section.option1' in c)
        self.assertFalse('section.option2' in c)
        self.assertFalse('section2.optionx' in c)

    def test_equality(self):
        d = {'a.b': 'c', 'x.y': 'z'}
        self.assertEqual(Config(d), Config(d))
        self.assertNotEqual(Config(d), Config({'a.b': 'c'}))
        self.assertNotEqual(Config(d), Config())

    def test_repr(self):
        data = {'a.b': 'c', 'x.y': 'z'}
        orig = Config(data)
        copy = eval(repr(orig))
        self.assertEqual(copy, orig)
        self.assertIsNot(copy, orig)


class FactoryTests(unittest.TestCase):

    def test_from_configparser(self):
        cp = ConfigParser.SafeConfigParser()
        option1 = 'option1'
        key1 = 'section.%s' % option1
        value1 = str(mock.Mock())
        option2 = 'option2'
        key2 = 'section.%s' % option2
        value2 = str(mock.Mock())
        cp.add_section('section')
        cp.set('section', option1, value1)
        cp.set('section', option2, value2)
        conf = Config.from_configparser(cp)
        self.assertIn(key1, conf)
        self.assertIn(key2, conf)
        self.assertEqual(conf[key1], value1)
        self.assertEqual(conf[key2], value2)

    def test_from_dict(self):
        d = {'a.b': 'c', 'x.y': 'z'}
        conf = Config.from_dict(d)
        for key in d:
            self.assertIn(key, conf)
        self.assertEqual(conf, d)


class ReadWriteTests(unittest.TestCase):

    def setUp(self):
        self.fh = StringIO.StringIO() # file-like string buffer
        # create config to read
        cp = ConfigParser.SafeConfigParser()
        cp.add_section("test")
        cp.set("test", "option1", "test option1")
        cp.set("test", "option2", "test option 2")
        cp.write(self.fh) # dump test object
        self.fh.seek(0) # rewind buffer

    def tearDown(self):
        self.fh.close()

    def test_read(self):
        conf = Config()
        conf.read(self.fh)
        self.assertEqual(conf['test.option1'], 'test option1')
        self.assertEqual(conf['test.option2'], 'test option 2')

    def test_write(self):
        conf = Config()
        conf.read(self.fh)
        try:
            newfh = StringIO.StringIO() # file-like string buffer
            conf.write(newfh)
            newfh.seek(0)
            self.assertEqual(newfh.getvalue(), self.fh.getvalue())
        finally:
            newfh.close()


if __name__ == "__main__":
    unittest.main()
