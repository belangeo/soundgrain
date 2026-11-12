"""Numeric list entry validation in Granulator controls."""
import unittest
from unittest.mock import Mock

import wx

from Resources.Modules import GranulatorFrame


class GranulatorListTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = wx.App.Get() or wx.App(False)

    def setUp(self):
        self.parent = wx.Frame(None)
        self.parent.sg_audio = Mock()
        self.frame = GranulatorFrame(self.parent, self.parent.sg_audio)
        self.fields = ((self.frame.tx_trans, self.frame.handleTrans, self.frame.onCharTrans,
                        self.parent.sg_audio.setDiscreteTrans),
                       (self.frame.tx_ftrans, self.frame.handleFilterTrans, self.frame.onCharFilterTrans,
                        self.parent.sg_audio.setDiscreteFilterTrans))

    def tearDown(self):
        self.frame.Destroy()
        self.parent.Destroy()

    def key(self, field, char=None, key=None, control=False):
        event = Mock()
        event.GetEventObject.return_value = field
        event.GetKeyCode.return_value = key if key is not None else ord(char)
        event.GetUnicodeKey.return_value = ord(char) if char is not None else wx.WXK_NONE
        event.ControlDown.return_value = control
        event.MetaDown.return_value = False
        event.AltDown.return_value = False
        return event

    def test_numeric_list_typing_and_editing_shortcuts(self):
        for field, _, handler, _ in self.fields:
            with self.subTest(field=field):
                field.ChangeValue('1.2')
                field.SetSelection(3, 3)
                for char in ('a', 'e', '.', '-'):
                    event = self.key(field, char)
                    handler(event)
                    event.Skip.assert_not_called()
                for char in ('5', ',', ' '):
                    event = self.key(field, char)
                    handler(event)
                    event.Skip.assert_called_once()
                field.SetSelection(1, 1)
                event = self.key(field, ' ')
                handler(event)
                event.Skip.assert_called_once()
                field.ChangeValue('1,')
                field.SetSelection(2, 2)
                for char in ('-', '+', '.', '5'):
                    event = self.key(field, char)
                    handler(event)
                    event.Skip.assert_called_once()
                event = self.key(field, ',')
                handler(event)
                event.Skip.assert_not_called()
                for event in (self.key(field, 'v', control=True),
                              self.key(field, key=wx.WXK_LEFT),
                              self.key(field, key=wx.WXK_NUMPAD5)):
                    handler(event)
                    event.Skip.assert_called_once()

    def test_invalid_lists_restore_previous_without_committing(self):
        for field, handler, _, setter in self.fields:
            with self.subTest(field=field):
                field.ChangeValue('1, -2.5, +0.25, ')
                handler(None)
                setter.assert_called_once_with([1.0, -2.5, 0.25])
                for invalid in ('', '1,,2', ',1', '1, -', '0..5', '1,abc', 'nan', 'inf', '1e999'):
                    setter.reset_mock()
                    field.ChangeValue(invalid)
                    handler(None)
                    self.assertEqual(field.GetValue(), '1, -2.5, +0.25, ')
                    setter.assert_not_called()

    def test_focus_loss_tab_and_project_save_validate_pending_text(self):
        for field, handler, onchar, setter in self.fields:
            with self.subTest(field=field):
                field.ChangeValue('2, 3')
                event = self.key(field, key=wx.WXK_TAB)
                onchar(event)
                setter.assert_called_once_with([2.0, 3.0])
                setter.reset_mock()
                field.ChangeValue('2, nope')
                focus = self.key(field, key=wx.WXK_LEFT)
                self.frame.onListFocusLost(focus)
                self.assertEqual(field.GetValue(), '2, 3')
                setter.assert_not_called()
                field.ChangeValue('3,,4')
                state = self.frame.save()
                key = 'trans' if field is self.frame.tx_trans else 'ftrans'
                self.assertEqual(state[key], [2.0, 3.0])
                setter.assert_not_called()

    def test_loaded_values_become_the_new_fallback(self):
        self.frame.setTrans([1.5, 2.5])
        self.frame.setFilterTrans([0.25, 0.75])
        for field, handler, _, setter in self.fields:
            with self.subTest(field=field):
                old = field.GetValue()
                setter.reset_mock()
                field.ChangeValue('invalid')
                handler(None)
                self.assertEqual(field.GetValue(), old)
                setter.assert_not_called()


if __name__ == '__main__':
    unittest.main()
