"""Y Axis mapping validation and project-state handling."""
import unittest
from unittest.mock import Mock

import wx

from Resources.Modules import GranulatorFrame


class YAxisValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = wx.App.Get() or wx.App(False)

    def setUp(self):
        self.parent = wx.Frame(None)
        self.parent.sg_audio = Mock()
        self.frame = GranulatorFrame(self.parent, self.parent.sg_audio)
        self.audio = self.parent.sg_audio

    def tearDown(self):
        self.frame.Destroy()
        self.parent.Destroy()

    def event(self, field):
        event = Mock()
        event.GetEventObject.return_value = field
        return event

    def test_invalid_values_restore_previous_without_callback(self):
        fields = ((self.frame.tx_dns_ymin, self.frame.handleMapMin, self.audio.setMapMin),
                  (self.frame.tx_dns_ymid, self.frame.handleMapMid, self.audio.setMapMid),
                  (self.frame.tx_dns_ymax, self.frame.handleMapMax, self.audio.setMapMax))
        for field, handler, setter in fields:
            with self.subTest(field=field):
                field.ChangeValue('-1.25')
                handler(self.event(field))
                setter.assert_called_with('y_dns_map', -1.25)
                for invalid in ('0.5aas', '0..5', 'nan', 'inf', '1e999'):
                    setter.reset_mock()
                    field.ChangeValue(invalid)
                    handler(self.event(field))
                    self.assertEqual(field.GetValue(), '-1.25')
                    setter.assert_not_called()

    def test_empty_midpoint_is_allowed_but_empty_min_and_max_are_not(self):
        middle = self.frame.tx_dns_ymid
        middle.ChangeValue('0.5')
        self.frame.handleMapMid(self.event(middle))
        middle.ChangeValue('')
        self.frame.handleMapMid(self.event(middle))
        self.audio.setMapMid.assert_called_with('y_dns_map', None)
        for field, handler, setter in ((self.frame.tx_dns_ymin, self.frame.handleMapMin, self.audio.setMapMin),
                                       (self.frame.tx_dns_ymax, self.frame.handleMapMax, self.audio.setMapMax)):
            old = field.GetValue()
            field.ChangeValue('')
            setter.reset_mock()
            handler(self.event(field))
            self.assertEqual(field.GetValue(), old)
            setter.assert_not_called()

    def test_focus_loss_and_save_validate_pending_edits(self):
        field = self.frame.tx_dns_ymin
        field.ChangeValue('2.5')
        self.frame.onMapFocusLost(self.event(field))
        self.audio.setMapMin.assert_called_with('y_dns_map', 2.5)
        self.audio.setMapMin.reset_mock()
        field.ChangeValue('bad')
        saved = self.frame.save()
        self.assertEqual(field.GetValue(), '2.5')
        self.assertEqual(saved['dnsYmin'], 2.5)
        self.audio.setMapMin.assert_not_called()

    def test_tab_reverts_invalid_edit_without_committing(self):
        field = self.frame.tx_dns_ymax
        field.ChangeValue('0..5')
        event = self.event(field)
        event.GetKeyCode.return_value = wx.WXK_TAB
        self.frame.onCharMapMax(event)
        self.assertEqual(field.GetValue(), '1.')
        self.audio.setMapMax.assert_not_called()
        event.Skip.assert_called_once()

    def key_event(self, field, char=None, key=None, control=False):
        event = self.event(field)
        event.GetKeyCode.return_value = key if key is not None else ord(char)
        event.GetUnicodeKey.return_value = ord(char) if char is not None else wx.WXK_NONE
        event.ControlDown.return_value = control
        event.MetaDown.return_value = False
        event.AltDown.return_value = False
        return event

    def test_typing_filters_non_numeric_and_invalid_decimal_characters(self):
        for field, handler in ((self.frame.tx_dns_ymin, self.frame.onCharMapMin),
                               (self.frame.tx_dns_ymid, self.frame.onCharMapMid),
                               (self.frame.tx_dns_ymax, self.frame.onCharMapMax)):
            field.ChangeValue('0.5')
            field.SetSelection(3, 3)
            for char in ('a', 'e', '.', '-'):
                event = self.key_event(field, char)
                handler(event)
                event.Skip.assert_not_called()
            event = self.key_event(field, '7')
            handler(event)
            event.Skip.assert_called_once()
            field.SetSelection(0, 3)
            event = self.key_event(field, '-')
            handler(event)
            event.Skip.assert_called_once()

    def test_editing_shortcuts_navigation_and_numeric_keypad_are_allowed(self):
        field = self.frame.tx_dns_ymin
        field.ChangeValue('0.5')
        field.SetSelection(3, 3)
        for event in (self.key_event(field, 'v', control=True),
                      self.key_event(field, key=wx.WXK_LEFT),
                      self.key_event(field, key=wx.WXK_BACK),
                      self.key_event(field, key=wx.WXK_NUMPAD5)):
            self.frame.onCharMapMin(event)
            event.Skip.assert_called_once()

    def test_project_loading_updates_last_valid_value(self):
        state = self.frame.save()
        state['dnsYmin'] = 3.75
        state['dnsYmid'] = '0.25'
        self.frame.load(state)
        self.audio.setMapMin.assert_any_call('y_dns_map', 3.75)
        self.audio.setMapMid.assert_any_call('y_dns_map', 0.25)
        field = self.frame.tx_dns_ymin
        field.ChangeValue('3..75')
        self.frame.handleMapMin(self.event(field))
        self.assertEqual(field.GetValue(), '3.75')


if __name__ == '__main__':
    unittest.main()
