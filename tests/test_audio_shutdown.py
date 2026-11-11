"""Audio callbacks around server shutdown."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

import wx
from pyo.lib._wxwidgets import ControlSlider

from Resources.audio import SG_Audio
from Resources.MainFrame import silenceSliderCallbacks


class AudioShutdownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = wx.App.Get() or wx.App(False)

    def test_queued_slider_callbacks_disabled_on_quit(self):
        frame = wx.Frame(None)
        try:
            nested = wx.Panel(frame)
            callback = Mock()
            slider = ControlSlider(nested, 1, 100, 10, outFunction=callback)
            self.assertIs(slider.outFunction, callback)
            silenceSliderCallbacks(frame)
            self.assertIsNone(slider.outFunction)
        finally:
            frame.Destroy()

    def test_playback_updates_when_audio_graph_is_unavailable(self):
        audio = SG_Audio.__new__(SG_Audio)
        audio.streams = {}
        audio.setMetroTime(2, 0.1)
        audio.setTranspo(2, 1.2)
        audio.setTrajAmplitude(2, 0.5)
        audio.setXposition(2, 0.25)
        audio.setYposition(2, 0.75)
        stream = SimpleNamespace(metro=SimpleNamespace(), transpo=SimpleNamespace(),
                                 traj_amp=SimpleNamespace(), position=SimpleNamespace())
        audio.streams = {2: stream}
        audio.setMetroTime(2, 0.1)
        audio.setTranspo(2, 1.2)
        audio.setTrajAmplitude(2, 0.5)
        audio.setXposition(2, 0.25)
        self.assertEqual((stream.metro.time, stream.transpo.value,
                          stream.traj_amp.value, stream.position.value), (0.1, 1.2, 0.5, 0.25))
        with self.assertRaises(KeyError):
            audio.setMetroTime(3, 0.1)

    def test_waveform_query_during_shutdown(self):
        audio = SG_Audio.__new__(SG_Audio)
        self.assertEqual(audio.getViewTable((800, 600), 1, 2), [])
        audio.table = Mock()
        audio.table.getViewTable.return_value = [[(0, 10), (1, 11)]]
        self.assertEqual(audio.getViewTable((800, 600), 1, 2), [[(0, 10), (1, 11)]])
        audio.table.getViewTable.assert_called_once_with((800, 600), 1, 2)
        del audio.table
        self.assertEqual(audio.getViewTable((800, 600), 1, 2), [])

    def test_mixer_updates_before_and_after_shutdown(self):
        audio = SG_Audio.__new__(SG_Audio)
        trajectory = SimpleNamespace(getId=lambda: 2, circlePos=(10, 20))
        fx = SimpleNamespace(getId=lambda: 3, getAmpValue=Mock(return_value=0.5))
        # A late paint after shutdown must not try to update a deleted mixer.
        audio.setMixerChannelAmps([trajectory], [fx])
        fx.getAmpValue.assert_not_called()
        audio.mixer = mixer = Mock()
        audio.setMixerChannelAmps([trajectory], [fx])
        fx.getAmpValue.assert_called_once_with((10, 20))
        mixer.setAmp.assert_called_once_with(2, 3, 0.5)
        del audio.mixer
        audio.setMixerChannelAmps([trajectory], [fx])
        mixer.setAmp.assert_called_once()


if __name__ == '__main__':
    unittest.main()
