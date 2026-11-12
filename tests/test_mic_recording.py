"""Microphone capture, device settings, and recorded-sound safety."""
import unittest
import os
import tempfile
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, call, patch

import wx
from pyo import Server, Sig, SndTable

from Resources import audio
from Resources.ControlPanel import ControlPanel
from Resources.MainFrame import MainFrame
from Resources.numeric_input import filterNumericChar


class MicrophoneAudioTests(unittest.TestCase):
    def test_failed_duplex_boot_falls_back_to_output(self):
        engine = audio.SG_Audio.__new__(audio.SG_Audio)
        engine.server = MagicMock()
        engine.server.getIsBooted.side_effect = [False, False, True]
        engine.controls = SimpleNamespace(meter=Mock())
        engine.envFrame = Mock()
        engine.clock = Mock()
        engine.refresh = Mock()
        names = ('Mixer', 'CosTable', 'Metro', 'TrigFunc', 'Randh', 'Sig',
                 'Choice', 'Noise', 'SigTo', 'Granulator_Stream', 'FourBand',
                 'Mix', 'Compress', 'Delay')
        with patch.multiple(audio, **{name: MagicMock() for name in names}):
            engine.boot(4, 2, 44100, 5)
        self.assertFalse(engine.inputAvailable)
        self.assertEqual(engine.server.setDuplex.call_args_list, [call(1), call(0)])
        self.assertEqual(engine.server.boot.call_count, 2)
        engine.server.setInputDevice.assert_called_once_with(5)

    def test_mono_capture_records_and_triggers_completion(self):
        server = Server(audio='manual', sr=44100, buffersize=64, duplex=0).boot()
        engine = audio.SG_Audio.__new__(audio.SG_Audio)
        engine.server = server
        engine.started = False
        engine.inputAvailable = True
        engine.micRecording = False
        engine.useTable = Mock()
        finished = Mock()
        try:
            with patch.object(audio, 'Input', side_effect=lambda chnl: Sig(0.5)), \
                 patch.object(audio.wx, 'CallAfter', side_effect=lambda callback: callback()):
                engine.startMic(0.1, finished)
                table = engine.useTable.call_args.args[0]
                self.assertEqual(len(table), 1)
                self.assertTrue(server.getIsStarted())
                for _ in range(10):
                    server.process()
                self.assertAlmostEqual(table.getTable()[100], 0.5, places=4)
                self.assertEqual(table.getTable()[-1], 0.0)
                for _ in range(140):
                    server.process()
                self.assertAlmostEqual(table.getTable()[100], 0.5, places=4)
                finished.assert_called_once_with()
                engine.stopMic()
                self.assertFalse(engine.micRecording)
                self.assertFalse(server.getIsStarted())
                with tempfile.TemporaryDirectory() as directory:
                    path = os.path.join(directory, 'capture.wav')
                    table.save(path, 0, 0)
                    restored = SndTable(path)
                    self.assertEqual(len(restored), 1)
                    self.assertAlmostEqual(restored.getTable()[100], 0.5, places=3)
        finally:
            server.shutdown()

    def test_stopping_capture_keeps_active_playback_server_running(self):
        engine = audio.SG_Audio.__new__(audio.SG_Audio)
        engine.server = Mock()
        engine.server.getIsStarted.return_value = True
        engine.started = True
        engine.micRecording = True
        engine.micRecorder = Mock()
        engine.micTrigger = Mock()
        engine.micInput = Mock()
        engine.stopMic()
        engine.server.stop.assert_not_called()
        self.assertFalse(engine.micRecording)

    def test_mic_requires_a_usable_input(self):
        engine = audio.SG_Audio.__new__(audio.SG_Audio)
        engine.inputAvailable = False
        with self.assertRaisesRegex(RuntimeError, 'audio input'):
            engine.startMic(1, Mock())

    def test_stopping_playback_keeps_microphone_server_running(self):
        engine = audio.SG_Audio.__new__(audio.SG_Audio)
        engine.started = True
        engine.micRecording = True
        engine.refresh_met = Mock()
        engine.server = Mock()
        engine.activeStreams = [2]
        engine.streams = {2: Mock()}
        engine.stop()
        self.assertFalse(engine.started)
        self.assertTrue(engine.micRecording)
        engine.streams[2].setActive.assert_called_once_with(0)
        engine.server.stop.assert_not_called()

    def test_replacing_table_reconnects_active_playback(self):
        engine = audio.SG_Audio.__new__(audio.SG_Audio)
        engine.started = True
        engine.activeStreams = [2]
        stream = Mock()
        engine.streams = {2: stream}
        engine.fxs = {}
        engine.chnls = 2
        engine.pos_noise = Mock()
        engine.mixer = Mock()
        engine.mixer.getKeys.return_value = [2]
        engine.stream_sum = SimpleNamespace(value=None)
        table = Mock()
        table.getSize.return_value = 100
        with patch.object(audio, 'Sig'), patch.object(audio, 'Mix'):
            engine.useTable(table)
        stream.create_granulator.assert_called_once()
        engine.mixer.delInput.assert_called_once_with(2)
        engine.mixer.addInput.assert_called_once_with(2, stream.granulator)
        stream.setActive.assert_called_once_with(1)


class MicrophoneControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = wx.App.Get() or wx.App(False)

    def setUp(self):
        self.frame = wx.Frame(None)
        self.frame.sg_audio = Mock()
        self.frame.sg_audio.micRecording = False
        self.frame.sg_audio.started = False
        self.frame.sg_audio.server.getCurrentTimeInSamples.return_value = 0
        self.frame.sg_audio.getTableDuration.return_value = 2.0
        self.frame.checkForMixedSound = Mock(return_value=(True, ''))
        self.frame.enableDrivers = Mock()
        self.frame.log = Mock()
        self.frame.draw = True
        self.frame.is_unsaved = False
        self.surface = Mock()
        self.surface.bitmapDict = {}
        self.panel = ControlPanel(self.frame, self.surface)
        self.frame.sg_audio.startMic.side_effect = lambda length, done: setattr(self.frame.sg_audio, 'micRecording', True)
        self.frame.sg_audio.stopMic.side_effect = lambda: setattr(self.frame.sg_audio, 'micRecording', False)

    def tearDown(self):
        self.panel.micTimer.Stop()
        self.frame.Destroy()

    def test_capture_updates_waveform_and_retains_partial_recording(self):
        self.panel.micLength.SetValue('2')
        self.panel.tog_mic.SetValue(True)
        self.panel.handleMic(None)
        self.frame.sg_audio.startMic.assert_called_once()
        self.assertEqual(self.frame.sg_audio.startMic.call_args.args[0], 2.0)
        self.assertEqual(self.panel.sndPath, 'Mixed sound (microphone)')
        self.assertTrue(self.frame.is_unsaved)
        self.surface.analyse.assert_called_with(self.panel.sndPath)
        self.assertFalse(self.panel.micLength.IsEnabled())
        self.panel.finishMic()
        self.assertFalse(self.frame.sg_audio.micRecording)
        self.assertTrue(self.panel.micLength.IsEnabled())
        self.assertEqual(self.panel.sndPath, 'Mixed sound (microphone)')

    def test_invalid_length_and_cancel_do_not_replace_sound(self):
        self.panel.micLength.SetValue('nan')
        self.panel.tog_mic.SetValue(True)
        with patch('Resources.ControlPanel.wx.MessageBox'):
            self.panel.handleMic(None)
        self.frame.sg_audio.startMic.assert_not_called()
        self.panel.micLength.SetValue('2')
        self.panel.tog_mic.SetValue(True)
        self.frame.checkForMixedSound.return_value = (False, '')
        self.panel.handleMic(None)
        self.frame.sg_audio.startMic.assert_not_called()
        self.assertFalse(self.panel.tog_mic.GetValue())

    def test_duration_filters_typed_characters_and_allows_editing(self):
        field = self.panel.micLength
        field.ChangeValue('1.5')
        field.SetSelection(3, 3)
        for char, allowed in (('a', False), (',', False), ('.', False), ('7', True)):
            event = Mock()
            event.GetEventObject.return_value = field
            event.GetKeyCode.return_value = ord(char)
            event.GetUnicodeKey.return_value = ord(char)
            event.ControlDown.return_value = False
            event.MetaDown.return_value = False
            event.AltDown.return_value = False
            filterNumericChar(event)
            self.assertEqual(event.Skip.call_count, int(allowed))
        event.ControlDown.return_value = True
        event.Skip.reset_mock()
        filterNumericChar(event)
        event.Skip.assert_called_once()

    def test_stale_completion_does_not_stop_a_new_recording(self):
        self.frame.sg_audio.micRecording = True
        self.panel.micGeneration = 2
        self.panel.finishMic(1)
        self.frame.sg_audio.stopMic.assert_not_called()

    def test_stalled_audio_device_stops_recording_and_reports_error(self):
        self.panel.micLength.SetValue('2')
        self.panel.tog_mic.SetValue(True)
        with patch('Resources.ControlPanel.time.monotonic', return_value=10):
            self.panel.handleMic(None)
        with patch('Resources.ControlPanel.time.monotonic', return_value=16), \
             patch('Resources.ControlPanel.wx.MessageBox') as message:
            self.panel.refreshMicWaveform(None)
        self.assertFalse(self.frame.sg_audio.micRecording)
        message.assert_called_once()

    def test_input_device_can_be_changed_and_cancelled(self):
        controls = SimpleNamespace(pop_input_driver=Mock(), sndPath='sound.wav',
                                   shutdownServer=Mock(), bootServer=Mock())
        frame = SimpleNamespace(controls=controls, inputDriverIndexes=[2, 5], inputDriver=2,
                                checkForMixedSound=Mock(return_value=(False, '')))
        event = SimpleNamespace(GetSelection=lambda: 1)
        MainFrame.handleInputDriver(frame, event)
        controls.pop_input_driver.SetSelection.assert_called_once_with(0)
        controls.shutdownServer.assert_not_called()
        frame.checkForMixedSound.return_value = (True, '')
        MainFrame.handleInputDriver(frame, event)
        self.assertEqual(frame.inputDriver, 5)
        controls.shutdownServer.assert_called_once_with()
        controls.bootServer.assert_called_once_with()


class MicrophoneSaveTests(unittest.TestCase):
    def test_input_preference_selects_matching_device(self):
        controls = SimpleNamespace(pop_audio_driver=Mock(), pop_input_driver=Mock(), bootServer=Mock())
        frame = SimpleNamespace(controls=controls, status=Mock(), audioDriver=None, inputDriver=None)
        with patch('Resources.MainFrame.checkForDrivers', return_value=(['output'], [4], 4)), \
             patch('Resources.MainFrame.checkForInputDrivers', return_value=(['first', 'chosen'], [5, 6], 5)):
            MainFrame.check(frame, 'output', 'chosen')
        self.assertEqual(frame.inputDriver, 6)
        controls.pop_input_driver.SetSelection.assert_called_once_with(1)
        controls.bootServer.assert_called_once_with()

    def test_canceling_audio_save_dialog_aborts_destructive_action(self):
        controls = SimpleNamespace(sndPath='Mixed sound (microphone)', fileformat=0, sampletype=0)
        frame = SimpleNamespace(controls=controls, sg_audio=SimpleNamespace(micRecording=False))
        confirm = Mock()
        confirm.ShowModal.return_value = wx.ID_YES
        file_dialog = Mock()
        file_dialog.ShowModal.return_value = wx.ID_CANCEL
        with patch('Resources.MainFrame.wx.MessageDialog', return_value=confirm), \
             patch('Resources.MainFrame.wx.FileDialog', return_value=file_dialog):
            self.assertEqual(MainFrame.checkForMixedSound(frame), (False, ''))


if __name__ == '__main__':
    unittest.main()
