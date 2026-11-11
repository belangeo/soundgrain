"""Launcher and resource lookup checks."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import SoundGrain

ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_resources_are_independent_of_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = os.getcwd()
            try:
                os.chdir(directory)
                spec = importlib.util.spec_from_file_location('soundgrain_test_constants', ROOT / 'Resources/constants.py')
                constants = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(constants)
                self.assertEqual(Path(constants.RESOURCES_PATH), ROOT / 'Resources')
                self.assertTrue(Path(constants.SPLASH_FILE).is_file())
                self.assertTrue((Path(constants.DOCUMENTATION_PATH) / '02_surface.md').is_file())
                self.assertTrue((Path(constants.RESOURCES_PATH) / 'new_soundgrain_file.sg').is_file())
                self.assertEqual(os.getcwd(), directory)
            finally:
                os.chdir(previous)

    def test_entry_point_passes_project_and_starts_event_loop(self):
        app = Mock()
        with patch.object(SoundGrain, 'SoundGrainApp', return_value=app) as create_app, \
             patch.object(SoundGrain, 'SoundGrainSplashScreen') as splash, \
             patch.object(SoundGrain.wx, 'CallAfter') as call_after, \
             patch.object(sys, 'argv', ['soundgrain', 'project.sg']):
            SoundGrain.main()
        create_app.assert_called_once_with(redirect=False)
        splash.assert_called_once_with(None, SoundGrain.SPLASH_FILE, app.frame)
        call_after.assert_called_once_with(app.frame.loadFile, 'project.sg')
        app.MainLoop.assert_called_once_with()



if __name__ == '__main__':
    unittest.main()
