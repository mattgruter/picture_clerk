"""
Created on 2011/03/08

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import unittest
import mock

from repo import Repo
from repo import PictureAlreadyIndexedError, PictureNotIndexedError


class ObjectCreationTest(unittest.TestCase):
    def setUp(self):
        pass
        
    def test_attributes(self):
        """
        Repo() should return a new repo with supplied index
        """
        mock_index = mock.Mock()
        r = Repo(index=mock_index)
        self.assertIsInstance(r, Repo)
        self.assertIs(r.index, mock_index)
     

class IndexTest(unittest.TestCase):
    def setUp(self):
        self.mock_pic = mock.Mock()
        self.index = dict()
        self.repo = Repo(index=self.index)

    def test_add_picture(self):
        """
        Added picture instance should end up in index.
        """
        self.repo.add_picture(self.mock_pic)
        self.assertIn(self.mock_pic, self.index.values())
        
    def test_readd_picture(self):
        """
        Adding the same picture twice should raise a PictureAlreadyIndexedError.
        """
        self.repo.add_picture(self.mock_pic)
        self.assertRaises(PictureAlreadyIndexedError,
                          self.repo.add_picture, self.mock_pic)
        
    def test_get_picture_by_filename(self):
        """
        Supplying the picture filename should return indexed picture instance.
        """
        self.repo.add_picture(self.mock_pic)
        key = self.mock_pic.filename
        pic = self.repo.get_picture_by_filename(key)
        self.assertEqual(pic, self.mock_pic)
        
    def test_get_picture_by_filename_error(self):
        """
        Attempting to fetch a picture that is not in the index should raise
        a PictureNotIndexedError.
        """
        self.assertRaises(PictureNotIndexedError,
                          self.repo.get_picture_by_filename, "filename")
        
    def test_update_picture(self):
        """
        Updating a picture in the index should replace the existing picture with
        the new one.
        """
        self.repo.add_picture(self.mock_pic)
        new_mock_pic = mock.Mock()
        new_mock_pic.filename = self.mock_pic.filename
        self.repo.update_picture(new_mock_pic)
        self.assertIn(new_mock_pic, self.index.values())
        self.assertNotIn(self.mock_pic, self.index.values())
        
    def test_update_picture_error(self):
        """
        Attempting to update a picture that is not in the index should raise
        a PictureNotIndexedError.
        """
        self.assertRaises(PictureNotIndexedError,
                          self.repo.update_picture, self.mock_pic)


if __name__ == "__main__":
    unittest.main()   
