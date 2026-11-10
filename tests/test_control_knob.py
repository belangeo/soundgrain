"""Control knob callbacks; requires a wx display."""
import unittest
from unittest.mock import Mock, patch

import wx

from Resources.widgets import ControlKnob


class ControlKnobTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = wx.App.Get() or wx.App(False)

    def setUp(self):
        self.frame = wx.Frame(None)
        self.callback = Mock()
        self.knob = ControlKnob(self.frame, 0, 100, 20, outFunction=self.callback)

    def tearDown(self):
        self.frame.Destroy()

    def test_value_changes_notify_without_waiting_for_paint(self):
        self.callback.assert_not_called()
        self.knob.SetValue(35)
        self.callback.assert_called_once_with(35)
        self.knob.HasCapture = Mock(return_value=True)
        self.knob.clickPos = (10, 100)
        self.knob.oldValue = 35
        event = Mock()
        event.Dragging.return_value = True
        event.LeftIsDown.return_value = True
        with patch('Resources.widgets.wx.GetMousePosition', return_value=(10, 80)):
            self.knob.MouseMotion(event)
        self.callback.assert_called_with(45)

    def test_paint_does_not_call_audio_callback(self):
        # Repaints can arrive after the audio graph has been destroyed.
        event = Mock()
        dc = Mock()
        dc.GetCharWidth.return_value = 8
        with patch('Resources.widgets.wx.AutoBufferedPaintDC', return_value=dc):
            self.knob.OnPaint(event)
        self.callback.assert_not_called()


if __name__ == '__main__':
    unittest.main()
