"""
Created on 2011/03/08

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL

"""
import unittest
import mock
import StringIO

from index import PictureIndex
from index import PictureAlreadyIndexedError, IndexParsingError


class BasicTests(unittest.TestCase):

    def setUp(self):
        self.mock_pic = mock.Mock()
        self.index = {'pic1': 'file1', 'pic2': 'file2', 'pic3': 'file3'}

    def test_type(self):
        mock_index = mock.Mock()
        pi = PictureIndex(d=mock_index)
        self.assertIsInstance(pi, PictureIndex)

    def test_equality(self):
        self.assertEqual(PictureIndex(self.index), PictureIndex(self.index))
        self.assertNotEqual(PictureIndex(self.index), PictureIndex())
        self.assertNotEqual(PictureIndex(self.index),
                            PictureIndex({'pic1': 'file1'}))

    def test_add(self):
        pi = PictureIndex(self.index)
        pi.add(self.mock_pic)
        self.assertIn(self.mock_pic, self.index.values())

    def test_readd_error(self):
        pi = PictureIndex(self.index)
        pi.add(self.mock_pic)
        self.assertRaises(PictureAlreadyIndexedError,
                          pi.add, self.mock_pic)

    def test_add_many(self):
        pi = PictureIndex(self.index)
        mock_pics = [mock.Mock(), mock.Mock(), mock.Mock()]
        pi.add_many(mock_pics)
        for mock_pic in mock_pics:
            self.assertIn(mock_pic, pi.pics())

    def test_iterpics(self):
        pi = PictureIndex(self.index)
        self.assertSequenceEqual(pi.pics(),
                                 list(pi.iterpics()))

    def test_get(self):
        pi = PictureIndex(self.index)
        pi.add(self.mock_pic)
        key = self.mock_pic.filename
        pic = pi[key]
        self.assertEqual(pic, self.mock_pic)

    def test_key_error(self):
        pi = PictureIndex(self.index)
        self.assertRaises(KeyError, pi.__getitem__, "unknown")

    def test_replace(self):
        pi = PictureIndex(self.index)
        pi.add(self.mock_pic)
        new_mock_pic = mock.Mock()
        new_mock_pic.filename = self.mock_pic.filename
        pi.replace(new_mock_pic)
        self.assertIn(new_mock_pic, self.index.values())
        self.assertNotIn(self.mock_pic, self.index.values())

    def test_replace_key_error(self):
        pi = PictureIndex(self.index)
        self.assertRaises(KeyError, pi.replace, self.mock_pic)


class ReadWriteTest(unittest.TestCase):

    def setUp(self):
        self.fh = StringIO.StringIO() # file-like string buffer

    def tearDown(self):
        self.fh.close()

    def test_write_read_cycle(self):
        index_a = PictureIndex({'pic1': "Picture 1", 'pic2': "Picture 2"})
        index_a.write(self.fh)
        self.fh.seek(0) # rewind buffer
        index_b = PictureIndex()
        index_b.read(self.fh)
        self.assertEqual(index_a, index_b, "Dumped and read index don't match.")
        self.assertIsNot(index_a, index_b, "Dumped and read index is same obj.")

    def test_read_error(self):
        # creating buffer content that can't be unpickled
        corrupt_buf = "42\n"
        self.fh.write(corrupt_buf)
        self.fh.seek(0) # rewind buffer
        pi = PictureIndex()
        self.assertRaises(IndexParsingError, pi.read, self.fh)


if __name__ == "__main__":
    unittest.main()
