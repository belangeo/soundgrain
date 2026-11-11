"""Horizontal canvas zoom; requires a wx display."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

import wx

from Resources.DrawingSurface import DrawingSurface
from Resources.FxBall import FxBall


class HorizontalZoomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = wx.App.Get() or wx.App(False)

    def setUp(self):
        self.frame = wx.Frame(None, size=(800, 600))
        self.frame.sg_audio = Mock()
        self.frame.controls = SimpleNamespace(getSelected=lambda: 0, setSelected=Mock(),
                                              drawWaveform=Mock(), sndDur=10,
                                              penWidth=Mock(GetValue=lambda: 2),
                                              wanderSpeed=Mock(GetValue=lambda: 1),
                                              wanderPeriodicity=Mock(GetValue=lambda: 0))
        self.frame.lowpass = False
        self.frame.fillPoints = False
        self.frame.editionLevel = 2
        self.frame.arrowSpeedLevel = 1
        self.frame.createTempFile = Mock()
        self.surface = DrawingSurface(self.frame, size=(800, 600))
        self.surface.HasCapture = Mock(return_value=False)
        self.surface.CaptureMouse = Mock()
        self.surface.ReleaseMouse = Mock()

    def tearDown(self):
        for ball in self.surface.fxballs.values():
            ball.controls.Destroy()
        self.frame.Destroy()

    def trajectory(self):
        t = self.surface.trajectories[0]
        t.active = True
        t.type = 'free'
        t.setPoints([(100, 100), (200, 200), (300, 300)])
        t.setInitPoints()
        return t

    def event(self, position):
        event = Mock()
        event.GetPosition.return_value = position
        event.AltDown.return_value = False
        event.ShiftDown.return_value = False
        event.Dragging.return_value = True
        event.LeftIsDown.return_value = True
        return event

    def test_zoom_anchor_reset_and_audio_coordinates(self):
        t = self.trajectory()
        before = t.getAttributes()
        self.surface.setZoom(4, 200)
        self.assertEqual(self.surface.screenToCanvas((200, 135)), (200, 135))
        self.assertEqual(self.surface.canvasToScreen((220, 135)), (280, 135))
        self.assertEqual(t.getAttributes(), before)
        self.frame.sg_audio.reset_mock()
        self.surface.clock(0)
        self.frame.sg_audio.setXposition.assert_called_once_with(0, 100 / 800)
        self.frame.sg_audio.setYposition.assert_called_once_with(0, 1 - 100 / 600)
        event = Mock()
        event.GetKeyCode.return_value = wx.WXK_ESCAPE
        self.surface.KeyDown(event)
        self.assertEqual((self.surface.zoomX, self.surface.viewX), (1, 0))

    def test_zoomed_edit_retains_fractional_x_and_original_y_scale(self):
        t = self.trajectory()
        self.surface.setZoom(4, 200)
        event = self.event((200, 200))
        self.surface.MouseDown(event)
        self.assertEqual(self.surface.action, 'edit')
        self.surface.HasCapture.return_value = True
        event.GetPosition.return_value = (201, 203)
        self.surface.MouseMotion(event)
        self.surface.MouseUp(event)
        self.assertEqual(t.points[1], [200.25, 203])

    def test_zoomed_fx_ball_drag(self):
        ball = FxBall(0, 0, self.frame.sg_audio, (100, 100), 60)
        self.surface.fxballs[0] = ball
        self.surface.setZoom(4, 130)
        event = self.event((130, 130))
        self.surface.MouseDown(event)
        self.assertEqual(self.surface.action, 'drag_ball')
        self.surface.HasCapture.return_value = True
        event.GetPosition.return_value = (134, 132)
        self.surface.MouseMotion(event)
        self.assertEqual(ball.getCenter(), (131, 132))
        self.surface.MouseUp(event)

    def test_fx_controls_belong_to_main_frame_and_are_destroyed_on_removal(self):
        self.surface.addFxBall(0)
        controls = self.surface.fxballs[0].controls
        self.assertIs(controls.GetParent(), self.frame)
        controls.Destroy = Mock(wraps=controls.Destroy)
        self.surface.removeFxBall(0)
        controls.Destroy.assert_called_once_with()

    def test_visible_waveform_interval_and_cache(self):
        self.surface.sndBitmap = wx.Bitmap(800, 600)
        self.frame.sg_audio.getViewTable.return_value = [[(0, 100), (800, 200)]]
        self.surface.setZoom(2, 400)
        bitmap = wx.Bitmap(800, 600)
        dc = wx.MemoryDC(bitmap)
        self.surface.draw(dc)
        self.surface.draw(dc)
        dc.SelectObject(wx.NullBitmap)
        self.frame.sg_audio.getViewTable.assert_called_once_with((800, 600), 2.5, 7.5)

    def test_shift_wheel_navigates_and_clamps_view(self):
        self.surface.setZoom(2, 400)
        wheel = self.event((400, 100))
        wheel.GetWheelDelta.return_value = 120
        wheel.GetWheelRotation.return_value = -120
        wheel.ShiftDown.return_value = True
        self.surface.OnWheel(wheel)
        self.assertEqual(self.surface.viewX, -480)
        wheel.GetWheelRotation.return_value = 12000
        self.surface.OnWheel(wheel)
        self.assertEqual(self.surface.viewX, 0)

    def test_horizontal_wheel_pans_without_changing_zoom(self):
        self.surface.setZoom(2, 400)
        wheel = self.event((400, 100))
        wheel.GetWheelAxis.return_value = wx.MOUSE_WHEEL_HORIZONTAL
        wheel.GetWheelDelta.return_value = 120
        wheel.GetWheelRotation.return_value = 120
        self.surface.OnWheel(wheel)
        self.assertEqual((self.surface.zoomX, self.surface.viewX), (2, -480))
        wheel.GetWheelRotation.return_value = -120
        self.surface.OnWheel(wheel)
        self.assertEqual((self.surface.zoomX, self.surface.viewX), (2, -400))

    def test_zoomed_start_handle_drag(self):
        t = self.trajectory()
        self.surface.setZoom(4, 200)
        event = self.event(self.surface.canvasToScreen(t.points[0]))
        self.surface.MouseDown(event)
        self.assertEqual(self.surface.action, 'drag')
        self.surface.HasCapture.return_value = True
        event.GetPosition.return_value = (event.GetPosition.return_value[0] + 4, 102)
        self.surface.MouseMotion(event)
        self.assertEqual(t.points[0], (101, 102))
        self.surface.MouseUp(event)

    def test_pan_and_zoom_are_ignored_during_drag(self):
        self.surface.setZoom(2, 400)
        self.surface.HasCapture.return_value = True
        wheel = self.event((400, 100))
        wheel.GetWheelDelta.return_value = 120
        wheel.GetWheelRotation.return_value = 120
        wheel.ShiftDown.return_value = True
        self.surface.OnWheel(wheel)
        self.surface.setZoom(4, 400)
        self.assertEqual((self.surface.zoomX, self.surface.viewX), (2, -400))

    def test_closed_path_with_fractional_coordinates(self):
        t = self.trajectory()
        t.addFinalPoint((110.25, 110), True)
        self.assertIn((110.25, 110), t.points)


if __name__ == '__main__':
    unittest.main()
