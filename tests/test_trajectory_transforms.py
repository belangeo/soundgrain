"""Keyboard transformations of the selected trajectory."""
import math
import unittest
import xmlrpc.client
from types import SimpleNamespace
from unittest.mock import Mock

import wx

from Resources.DrawingSurface import DrawingSurface
from Resources.MainFrame import MainFrame
from Resources.Trajectory import Trajectory


class TrajectoryTransformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = wx.App.Get() or wx.App(False)

    def setUp(self):
        self.frame = wx.Frame(None, size=(800, 600))
        self.frame.sg_audio = Mock()
        self.frame.controls = SimpleNamespace(getSelected=lambda: 0, setSelected=Mock(), drawWaveform=Mock())
        self.frame.arrowSpeedLevel = 1
        self.frame.fillPoints = False
        self.frame.lowpass = False
        self.frame.editionLevel = 2
        self.frame.createTempFile = Mock()
        self.surface = DrawingSurface(self.frame, size=(800, 600))
        self.surface.HasCapture = Mock(return_value=False)
        self.surface.CaptureMouse = Mock()
        self.surface.ReleaseMouse = Mock()
        self.t = self.surface.trajectories[0]
        self.t.active = True
        self.t.type = 'free'
        self.t.setPoints([(100, 100), (200, 200), (300, 100)])

    def tearDown(self):
        self.frame.Destroy()

    def key(self, letter, shift=False, control=False, alt=False):
        event = Mock()
        event.GetKeyCode.return_value = ord(letter.upper())
        event.ShiftDown.return_value = shift
        event.ControlDown.return_value = control
        event.AltDown.return_value = alt
        event.MetaDown.return_value = False
        self.surface.KeyDown(event)
        return event

    def test_flip_selected_preserves_order_and_playback_position(self):
        self.t.circlePos = (125, 125)
        self.t.lastCirclePos = (110, 110)
        self.t.counter = 2
        self.key('h')
        self.assertEqual(self.t.points, [(300, 100), (200, 200), (100, 100)])
        self.assertEqual(self.t.circlePos, (275, 125))
        self.assertEqual(self.t.lastCirclePos, (290, 110))
        self.assertEqual(self.t.counter, 2)
        self.assertEqual(self.t.initPoints, self.t.points)
        self.frame.createTempFile.assert_called_once()
        self.key('v')
        self.assertEqual(self.t.points, [(300, 200), (200, 100), (100, 200)])
        self.assertEqual(self.frame.createTempFile.call_count, 2)

    def test_rotate_step_modifiers_and_zoom(self):
        self.surface.setZoom(4, 200)
        for shift, control, angle in ((False, False, 15), (True, False, 5), (True, True, 1)):
            self.t.setPoints([(100, 200), (200, 200), (300, 200)])
            self.key('r', shift=shift, control=control)
            expected = math.radians(angle)
            self.assertAlmostEqual(self.t.points[2][0], 200 + 100 * math.cos(expected))
            self.assertAlmostEqual(self.t.points[2][1], 200 + 100 * math.sin(expected))
        self.assertEqual(self.frame.createTempFile.call_count, 3)

    def test_unrelated_modifiers_and_empty_selection_do_not_change_trajectory(self):
        before = self.t.points[:]
        event = self.key('r', control=True)
        event.Skip.assert_called_once()
        self.key('h', alt=True)
        self.assertEqual(self.t.points, before)
        self.t.active = False
        self.key('h')
        self.assertEqual(self.t.points, before)
        self.frame.createTempFile.assert_not_called()

    def test_full_rotation_returns_to_original_position(self):
        original = self.t.points[:]
        for _ in range(24):
            self.key('r')
        for actual, expected in zip(self.t.points, original):
            self.assertAlmostEqual(actual[0], expected[0])
            self.assertAlmostEqual(actual[1], expected[1])

    def test_transformation_is_undoable(self):
        self.frame.panel = self.surface
        self.frame.menu1 = Mock()
        self.frame.temps = []
        self.frame.recall = self.frame.undos = 0
        self.frame.createTempFile = lambda: MainFrame.createTempFile(self.frame)
        MainFrame.createInitTempFile(self.frame)
        original = self.t.points[:]
        self.key('h')
        self.assertNotEqual(self.t.points, original)
        MainFrame.recallTempFile(self.frame, 110)
        self.assertEqual(self.t.points, original)

    def test_d_duplicates_selected_trajectory_and_is_undoable(self):
        self.frame.panel = self.surface
        self.frame.menu1 = Mock()
        self.frame.temps = []
        self.frame.recall = self.frame.undos = 0
        self.frame.createTempFile = lambda: MainFrame.createTempFile(self.frame)
        self.t.setWidth(40)
        self.t.setWanderSpeed(2)
        self.t.setWanderPeriodicity(0.5)
        self.t.closed = True
        MainFrame.createInitTempFile(self.frame)
        self.key('d')
        duplicate = self.surface.selected
        self.assertIsNot(duplicate, self.t)
        self.assertTrue(duplicate.getActive())
        self.assertEqual(duplicate.points, self.t.points)
        self.assertEqual((duplicate.getWidth(), duplicate.getWanderSpeed(), duplicate.getWanderPeriodicity()),
                         (40, 2, 0.5))
        self.assertTrue(duplicate.closed)
        self.assertTrue(self.frame.is_unsaved)
        MainFrame.recallTempFile(self.frame, 110)
        self.assertFalse(duplicate.getActive())
        self.assertTrue(self.t.getActive())

    def test_d_does_nothing_without_selected_trajectory_or_free_slot(self):
        self.t.active = False
        self.key('d')
        self.frame.createTempFile.assert_not_called()
        for trajectory in self.surface.trajectories:
            trajectory.active = True
        self.key('d')
        self.assertIs(self.surface.selected, self.t)
        self.frame.createTempFile.assert_not_called()

    def test_transformed_circle_survives_project_roundtrip_and_resize(self):
        self.t.type = 'circle'
        self.t.closed = True
        self.t.center = (250, 250)
        self.t.radius = 40
        self.t.setPoints([(210, 250), (250, 210), (290, 250), (250, 290)])
        self.key('h')
        data = xmlrpc.client.loads(xmlrpc.client.dumps((self.t.getAttributes(),), allow_none=True))[0][0]
        restored = Trajectory(self.surface, 2)
        restored.setAttributes(data)
        self.assertEqual(restored.radius, 40)
        self.assertEqual([tuple(point) for point in restored.points], self.t.points)
        self.assertTrue(restored.geometryTransformed)
        before = self.t.points[:]
        event = Mock()
        event.GetPosition.return_value = self.t.getLosangePoint()
        event.AltDown.return_value = False
        self.surface.MouseDown(event)
        self.assertEqual(self.surface.action, 'rescale')
        self.surface.HasCapture.return_value = True
        event.Dragging.return_value = True
        event.LeftIsDown.return_value = True
        event.GetPosition.return_value = (310, 250)
        self.surface.MouseMotion(event)
        for actual, original in zip(self.t.points, before):
            self.assertAlmostEqual(actual[0], 250 + (original[0] - 250) * 1.5)
            self.assertAlmostEqual(actual[1], 250 + (original[1] - 250) * 1.5)
        self.surface.MouseUp(event)

    def test_transformed_oscillation_preserves_shape_metadata(self):
        self.t.type = 'oscil'
        self.t.center = (200, 200)
        self.t.radius = 100
        self.key('r', shift=True)
        data = xmlrpc.client.loads(xmlrpc.client.dumps((self.t.getAttributes(),), allow_none=True))[0][0]
        restored = Trajectory(self.surface, 2)
        restored.setAttributes(data)
        self.assertEqual(restored.getType(), 'oscil')
        self.assertEqual(restored.getCenter(), (200, 200))
        self.assertEqual(restored.getRadius(), 100)
        self.assertEqual([tuple(point) for point in restored.points], self.t.points)


if __name__ == '__main__':
    unittest.main()
