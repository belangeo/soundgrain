"""Audio settings behavior; requires wx and pyo."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from Resources.MainFrame import MainFrame


class AudioSettingsTests(unittest.TestCase):
    def setUp(self):
        self.controls = SimpleNamespace(pop_audio_driver=Mock(), pop_precision=Mock(),
                                        sndPath='sound.wav', shutdownServer=Mock(),
                                        bootServer=Mock())
        self.frame = SimpleNamespace(controls=self.controls, driversList=['A', 'B'],
                                     driverIndexes=[4, 9], audioDriver=4,
                                     checkForMixedSound=Mock(return_value=(True, '')))

    def test_driver_selection_restarts_server(self):
        MainFrame.handleDriver(self.frame, SimpleNamespace(GetSelection=lambda: 1))
        self.assertEqual(self.frame.audioDriver, 9)
        self.controls.shutdownServer.assert_called_once_with()
        self.controls.bootServer.assert_called_once_with()

    def test_canceled_driver_change_restores_selection(self):
        self.frame.checkForMixedSound.return_value = (False, '')
        MainFrame.handleDriver(self.frame, SimpleNamespace(GetSelection=lambda: 1))
        self.controls.pop_audio_driver.SetSelection.assert_called_once_with(0)
        self.assertEqual(self.frame.audioDriver, 4)
        self.controls.shutdownServer.assert_not_called()

    def test_unchanged_driver_does_not_restart(self):
        MainFrame.handleDriver(self.frame, SimpleNamespace(GetSelection=lambda: 0))
        self.frame.checkForMixedSound.assert_not_called()
        self.controls.shutdownServer.assert_not_called()

    def test_precision_selection_and_driver_enablement(self):
        self.controls.pop_precision.GetStringSelection.return_value = '64-bit'
        MainFrame.handlePrecision(self.frame, None)
        self.assertEqual(self.frame.sample_precision, '64-bit')
        MainFrame.enableDrivers(self.frame, False)
        self.controls.pop_audio_driver.Enable.assert_called_with(False)
        MainFrame.enableDrivers(self.frame, True)
        self.controls.pop_audio_driver.Enable.assert_called_with(True)


if __name__ == '__main__':
    unittest.main()
