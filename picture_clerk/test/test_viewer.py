"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL
"""
import unittest
import mock

from viewer import Viewer
from viewer import log as viewer_logger


@mock.patch('os.path.exists', spec_set=True)
@mock.patch('subprocess.call', spec_set=True)
class TestViewer(unittest.TestCase):

    def setUp(self):
        self.prog = 'prog -a -b -c'
        self.pics = ['pic1', 'pic2', 'pic3']
        self.viewer_err_logger = mock.Mock()
        viewer_logger.error = self.viewer_err_logger # patch viewer's log.error


    def tearDown(self):
        pass

    def test_execution_sucess(self, mock_call, mock_exists):
        mock_call.return_value = 0
        mock_exists.return_value = True
        v = Viewer(self.prog)
        deleted_pics = v.show(self.pics)
        mock_call.assert_called_once_with(self.prog.split() + self.pics)
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
        def pic_exists(path):
            if path == 'pic2':
                return False
            else:
                return True
        mock_exists.side_effect = pic_exists
        v = Viewer(self.prog)
        deleted_pics = v.show(self.pics)
        self.assertListEqual(deleted_pics, ['pic2'])
        self.assertFalse(self.viewer_err_logger.called)


if __name__ == "__main__":
    unittest.main()
