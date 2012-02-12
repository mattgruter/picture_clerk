"""
Created on 2011/03/08

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import unittest
import mock

from index import PictureIndex
from index import PictureAlreadyIndexedError, PictureNotIndexedError


class ObjectCreationTest(unittest.TestCase):
    def setUp(self):
        self.mock_index = mock.Mock()

    def test_attributes(self):
        """Constructor should return a new Index with supplied contents."""
        pi = PictureIndex(index=self.mock_index)
        self.assertIsInstance(pi, PictureIndex)
        self.assertIs(pi.index, self.mock_index)


class EqualityTest(unittest.TestCase):
    def setUp(self):
        self.index = ['pic1', 'pic2', 'pic3']
        self.instance = PictureIndex(self.index)

    def test_equal(self):
        other = PictureIndex(self.index)
        self.assertTrue(self.instance == other)
        self.assertFalse(self.instance != other)

    def test_notequal(self):
        other = PictureIndex([])
        self.assertTrue(self.instance != other)
        self.assertFalse(self.instance == other)


class IndexTest(unittest.TestCase):
    def setUp(self):
        self.mock_pic = mock.Mock()
        self.index = dict()
        self.pi = PictureIndex(index=self.index)

    def test_add_picture(self):
        """Added picture instance should end up in index."""
        self.pi.add_picture(self.mock_pic)
        self.assertIn(self.mock_pic, self.index.values())

    def test_readd_picture(self):
        """Adding a picture twice should raise PictureAlreadyIndexedError."""
        self.pi.add_picture(self.mock_pic)
        self.assertRaises(PictureAlreadyIndexedError,
                          self.pi.add_picture, self.mock_pic)

    def test_add_get_pictures(self):
        """Added list of pictures should all end up in index."""
        mock_pics = [mock.Mock(), mock.Mock(), mock.Mock()]
        self.pi.add_pictures(mock_pics)
        for mock_pic in mock_pics:
            self.assertIn(mock_pic, self.pi.get_pictures())

    def test_get_pictures_iter(self):
        """get_pictures_iter should return an iterator over all pics."""
        mock_pics = [mock.Mock(), mock.Mock(), mock.Mock()]
        self.pi.add_pictures(mock_pics)
        self.assertSequenceEqual(self.pi.get_pictures(),
                                 list(self.pi.get_pictures_iter()))

    def test_get_picture_by_filename(self):
        """Supplying picture filename should return indexed instance."""
        self.pi.add_picture(self.mock_pic)
        key = self.mock_pic.filename
        pic = self.pi.get_picture_by_filename(key)
        self.assertEqual(pic, self.mock_pic)

    def test_get_picture_by_filename_error(self):
        """Trying to fetch unknown pic should raise PictureNotIndexedError."""
        self.assertRaises(PictureNotIndexedError,
                          self.pi.get_picture_by_filename, "unknown")

    def test_update_picture(self):
        """Updating indexed picture replace existing picture with new one."""
        self.pi.add_picture(self.mock_pic)
        new_mock_pic = mock.Mock()
        new_mock_pic.filename = self.mock_pic.filename
        self.pi.update_picture(new_mock_pic)
        self.assertIn(new_mock_pic, self.index.values())
        self.assertNotIn(self.mock_pic, self.index.values())

    def test_update_picture_error(self):
        """Trying to update unknown pic should raise PictureNotIndexedError."""
        self.assertRaises(PictureNotIndexedError,
                          self.pi.update_picture, self.mock_pic)


if __name__ == "__main__":
    unittest.main()
