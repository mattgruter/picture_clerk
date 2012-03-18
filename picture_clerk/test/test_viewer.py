"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import unittest
import mock

from testlib import MockPicture
from viewer import Viewer
from viewer import log as viewer_logger


@mock.patch('os.path.exists', spec_set=True)
@mock.patch('subprocess.call', spec_set=True)
class TestViewer(unittest.TestCase):

    def setUp(self):
        self.prog = 'prog -a -b -c'
        self.pics = MockPicture.create_many(50)
        self.thumbs = [pic.get_thumbnail_filenames()[0] for pic in self.pics]
        self.viewer_err_logger = mock.Mock()
        viewer_logger.error = self.viewer_err_logger # patch viewer's log.error

    def tearDown(self):
        pass

    def test_execution_sucess(self, mock_call, mock_exists):
        mock_call.return_value = 0
        mock_exists.return_value = True

        v = Viewer(self.prog)
        deleted_pics = v.show(self.pics)

        actual_call_args = mock_call.call_args_list[0][0][0]
        expected_call_args = self.prog.split() + sorted(self.thumbs)
        self.assertItemsEqual(expected_call_args, actual_call_args)
        self.assertListEqual(deleted_pics, [])
        self.assertFalse(self.viewer_err_logger.called)

    def test_execution_error(self, mock_call, mock_exists):
        mock_call.return_value = 5

        v = Viewer(self.prog)
        deleted_pics = v.show(self.pics)

        self.assertListEqual(deleted_pics, [])
        self.assertTrue(self.viewer_err_logger.called)

    def test_execution_fail(self, mock_call, mock_exists):
        mock_call.side_effect = OSError("mock execution failed")

        v = Viewer(self.prog)
        deleted_pics = v.show(self.pics)

        self.assertListEqual(deleted_pics, [])
        self.assertTrue(self.viewer_err_logger.called)

    def test_deleted_pics(self, mock_call, mock_exists):
        mock_call.return_value = 0
        deleted_thumbs = [pic.get_thumbnail_filenames()[0]
                          for pic in self.pics[4:15:2]]
        def pic_exists(path):
            if path in deleted_thumbs:
                return False
            else:
                return True
        mock_exists.side_effect = pic_exists

        v = Viewer(self.prog)
        deleted_pics = v.show(self.pics)

        self.assertItemsEqual(deleted_pics, self.pics[4:15:2])
        self.assertFalse(self.viewer_err_logger.called)


if __name__ == "__main__":
    unittest.main()
