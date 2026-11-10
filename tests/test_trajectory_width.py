"""Run with python3 -m unittest discover -s tests (requires a wx display)."""
import math
import unittest
import xmlrpc.client
from types import SimpleNamespace
from unittest.mock import Mock, patch

import wx

from Resources.Trajectory import Trajectory


class TrajectoryWidthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = wx.App.Get() or wx.App(False)

    def make_trajectory(self, points, width=2):
        surface = SimpleNamespace(parent=SimpleNamespace(sg_audio=Mock()),
                                  GetSize=lambda: (800, 600))
        trajectory = Trajectory(surface, 1)
        trajectory._random.seed(123)
        trajectory.resetWander()
        trajectory.setWidth(width)
        trajectory.setPoints(points)
        return trajectory

    def test_default_width_preserves_positions_and_timing(self):
        trajectory = self.make_trajectory([(10, 20), (30, 40), (50, 60)])
        trajectory.setStep(2)
        for index in (0, 2, 1, 0):
            trajectory.clock()
            self.assertEqual(trajectory.circlePos, trajectory.points[index])
        self.assertEqual(trajectory.counter, 8)

    def test_displacement_is_perpendicular_and_bounded(self):
        for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1)):
            with self.subTest(direction=(dx, dy)):
                points = [(300 + dx * i, 300 + dy * i) for i in range(30)]
                trajectory = self.make_trajectory(points, 60)
                displacements = []
                for tick in range(500):
                    center = points[tick % len(points)]
                    trajectory.clock()
                    x, y = trajectory.circlePos
                    ox, oy = x - center[0], y - center[1]
                    self.assertAlmostEqual(ox * dx + oy * dy, 0)
                    self.assertLessEqual(math.hypot(ox, oy), 29 + 1e-9)
                    displacements.append((ox, oy))
                self.assertGreater(max(math.hypot(*p) for p in displacements), 10)

    def test_noise_is_smooth_and_independent_of_point_step(self):
        first = self.make_trajectory([(200, 200), (201, 200)], 100)
        second = self.make_trajectory([(200, 200), (201, 200)], 100)
        second.setStep(7)
        previous = 0
        for tick in range(300):
            first.clock()
            second.clock()
            offset = first.circlePos[1] - 200
            self.assertAlmostEqual(first.circlePos[1], second.circlePos[1])
            self.assertLess(abs(offset - previous), 10)
            previous = offset
        self.assertEqual(second.counter, first.counter * 7)

    def test_freeze_and_moving_frozen_trajectory(self):
        trajectory = self.make_trajectory([(200, 200), (210, 200)], 50)
        trajectory.clock()
        trajectory.setFreeze(True)
        before = (trajectory.circlePos, trajectory.counter, trajectory._wanderElapsed)
        for _ in range(20):
            trajectory.clock()
        self.assertEqual(before, (trajectory.circlePos, trajectory.counter, trajectory._wanderElapsed))
        trajectory.move((5, 10))
        self.assertEqual(trajectory.circlePos, (before[0][0] - 5, before[0][1] - 10))
        trajectory.setFreeze(False)
        trajectory.clock()
        self.assertEqual(trajectory.counter, before[1] + trajectory.step)

    def test_canvas_edges_keep_perpendicular_displacement(self):
        for points in ([(0, i) for i in range(30)],
                       [(800, i) for i in range(30)],
                       [(i, 0) for i in range(30)],
                       [(i, 600) for i in range(30)]):
            trajectory = self.make_trajectory(points, 100)
            for _ in range(300):
                trajectory.clock()
                x, y = trajectory.circlePos
                self.assertTrue(0 <= x <= 800)
                self.assertTrue(0 <= y <= 600)

    def test_closed_loop_seam_and_repeated_points(self):
        points = [(300 + 100 * math.cos(i * math.tau / 120),
                   300 + 100 * math.sin(i * math.tau / 120)) for i in range(120)]
        trajectory = self.make_trajectory(points, 50)
        trajectory.closed = True
        start = trajectory._getNormal(0)
        end = trajectory._getNormal(119)
        self.assertGreater(sum(a * b for a, b in zip(start, end)), .99)
        for _ in range(300):
            trajectory.clock()
        trajectory.setPoints([(200, 200)] * 10)
        for _ in range(50):
            trajectory.clock()
            self.assertTrue(all(math.isfinite(v) for v in trajectory.circlePos))

    def test_drawing_captures_width_once_and_copies_keep_it(self):
        # The FX controls depend on pyo; this drawing-only test needs no FX balls.
        import sys
        with patch.dict(sys.modules, {'Resources.FxBall': SimpleNamespace(FxBall=Mock())}):
            from Resources.DrawingSurface import DrawingSurface
        frame = wx.Frame(None)
        frame.sg_audio = Mock()
        frame.lowpass = False
        frame.fillPoints = False
        frame.editionLevel = 2
        frame.createTempFile = Mock()
        from Resources.ControlPanel import VariationParameters
        host = wx.Panel(frame)
        host.handleSelected = Mock()
        host.handleWidth = Mock()
        host.handleWanderSpeed = Mock()
        host.handleWanderPeriodicity = Mock()
        variation = VariationParameters(wx.Notebook(host))
        width = variation.sl_width
        width.SetValue(40)
        speed = variation.sl_speed
        speed.SetValue(3)
        periodicity = variation.sl_periodicity
        periodicity.SetValue(0.25)
        frame.controls = SimpleNamespace(penWidth=width, wanderSpeed=speed,
                                         wanderPeriodicity=periodicity, setSelected=Mock(),
                                         drawWaveform=Mock(), getSelected=lambda: 0)
        surface = DrawingSurface(frame, size=(800, 600))
        surface.CaptureMouse = Mock()
        surface.ReleaseMouse = Mock()
        surface.HasCapture = lambda: True
        event = Mock()
        event.GetPosition.return_value = (200, 200)
        event.AltDown.return_value = False
        try:
            surface.MouseDown(event)
            original = surface.traj
            width.SetValue(90)
            speed.SetValue(0.5)
            periodicity.SetValue(0.75)
            original.setPoints([(200, 200), (300, 200)])
            surface.MouseUp(event)
            self.assertEqual(original.getWidth(), 40)
            self.assertAlmostEqual(original.getWanderSpeed(), 3)
            self.assertAlmostEqual(original.getWanderPeriodicity(), 0.25)
            surface.MouseDoubleClick(event)
            copy = surface.selected
            self.assertIsNot(copy, original)
            self.assertEqual(copy.getWidth(), 40)
            self.assertAlmostEqual(copy.getWanderSpeed(), 3)
            self.assertAlmostEqual(copy.getWanderPeriodicity(), 0.25)
            surface.Memorize()
            self.assertEqual(surface.memorizedTrajectory.getWidth(), 40)
            self.assertAlmostEqual(surface.memorizedTrajectory.getWanderSpeed(), 3)
            self.assertAlmostEqual(surface.memorizedTrajectory.getWanderPeriodicity(), 0.25)
            event.GetPosition.return_value = (400, 400)
            surface.MouseDown(event)
            self.assertEqual(surface.traj.getWidth(), 90)
            self.assertAlmostEqual(surface.traj.getWanderSpeed(), 0.5)
            self.assertAlmostEqual(surface.traj.getWanderPeriodicity(), 0.75)
            self.assertEqual(original.getWidth(), 40)
            # The same displayed displaced position is sent to the audio engine.
            surface.clock(original.getId())
            x, y = original.getPointPos()
            frame.sg_audio.setXposition.assert_called_with(original.getId(), x / 800)
            frame.sg_audio.setYposition.assert_called_with(original.getId(), 1 - y / 600)
        finally:
            frame.Destroy()

    def test_live_variation_selection_all_and_read_only_refresh(self):
        from Resources.ControlPanel import ControlPanel
        from Resources.constants import MAX_STREAMS
        trajectories = [self.make_trajectory([(200, 200), (300, 200)], width)
                        for width in (40, 60, 20)]
        trajectories[0].setWanderSpeed(2)
        trajectories[1].setWanderSpeed(3)
        trajectories[1].setWanderPeriodicity(0.8)
        surface = Mock()
        surface.getTrajectory.side_effect = lambda index: trajectories[index]
        surface.getActiveTrajectories.return_value = trajectories[:2]
        frame = wx.Frame(None)
        frame.sg_audio = Mock()
        controls = ControlPanel(frame, surface)
        try:
            controls.setSelected(0)
            self.assertEqual(controls.penWidth.GetValue(), 40)
            controls.handleWidth(80)
            controls.handleWanderSpeed(4)
            controls.handleWanderPeriodicity(0.2)
            self.assertAlmostEqual(trajectories[0].getWanderPeriodicity(), 0.2)
            self.assertAlmostEqual(trajectories[1].getWanderPeriodicity(), 0.8)
            self.assertEqual(trajectories[0].getWidth(), 80)
            self.assertEqual(trajectories[1].getWidth(), 60)
            self.assertEqual(trajectories[0].getWanderSpeed(), 4)
            controls.setSelected(1)
            self.assertEqual(controls.variation.tog_traj.GetSelection(), 1)
            self.assertEqual(controls.playback.tog_traj.GetSelection(), 1)
            self.assertEqual(controls.penWidth.GetValue(), 60)
            self.assertAlmostEqual(controls.wanderSpeed.GetValue(), 3)
            self.assertAlmostEqual(controls.wanderPeriodicity.GetValue(), 0.8)
            # Programmatic refresh/repaint must not write the displayed values
            # back to the selected trajectories or touch another trajectory.
            controls.handleWidth(controls.penWidth.GetValue())
            controls.handleWanderSpeed(controls.wanderSpeed.GetValue())
            controls.handleWanderPeriodicity(controls.wanderPeriodicity.GetValue())
            self.assertAlmostEqual(trajectories[0].getWanderPeriodicity(), 0.2)
            self.assertEqual(trajectories[0].getWidth(), 80)
            self.assertEqual(trajectories[1].getWidth(), 60)
            controls.setSelected(MAX_STREAMS)
            self.assertEqual(controls.variation.tog_traj.GetStringSelection(), 'all')
            controls.handleWidth(120)
            controls.handleWanderSpeed(0.5)
            controls.handleWanderPeriodicity(0.4)
            self.assertEqual([t.getWanderPeriodicity() for t in trajectories], [0.4, 0.4, 0])
            self.assertEqual([t.getWidth() for t in trajectories], [120, 120, 20])
            self.assertEqual([t.getWanderSpeed() for t in trajectories], [0.5, 0.5, 1])
            self.assertTrue(frame.is_unsaved)
            self.assertTrue(surface.needBitmap)
            # Persist two different settings through the real project format.
            controls.setSelected(1)
            controls.handleWidth(300)
            controls.handleWanderSpeed(6)
            controls.handleWanderPeriodicity(0.9)
            records = [t.getAttributes() for t in trajectories]
            records = xmlrpc.client.loads(xmlrpc.client.dumps((records,), allow_none=True))[0][0]
            for t, record in zip(trajectories, records):
                t.setWidth(2)
                t.setWanderSpeed(1)
                t.setWanderPeriodicity(1)
                t.setAttributes(record)
            self.assertEqual([t.getWidth() for t in trajectories], [120, 300, 20])
            self.assertEqual([t.getWanderSpeed() for t in trajectories], [0.5, 6, 1])
            self.assertEqual([t.getWanderPeriodicity() for t in trajectories], [0.4, 0.9, 0])
        finally:
            frame.Destroy()

    def test_live_width_preserves_random_phase_and_updates_frozen_ball(self):
        trajectory = self.make_trajectory([(200, 200), (300, 200)], 100)
        for _ in range(20):
            trajectory.clock()
        trajectory.setFreeze(True)
        elapsed, counter = trajectory._wanderElapsed, trajectory.counter
        trajectory.setWidth(2)
        self.assertEqual(trajectory.circlePos, trajectory.points[(counter - 1) % 2])
        trajectory.setWidth(200)
        self.assertNotEqual(trajectory.circlePos[1], 200)
        self.assertEqual(trajectory._wanderElapsed, elapsed)
        self.assertEqual(trajectory.counter, counter)

    def test_width_500_and_random_speed_multiplier(self):
        first = self.make_trajectory([(200, 300), (400, 300)], 500)
        second = self.make_trajectory([(200, 300), (400, 300)], 500)
        self.assertEqual(first.getWidth(), 500)
        first.setWanderSpeed(4)
        second.setTimeSpeed(100)
        # Four times the noise speed has the same effect as four times the
        # elapsed time, while leaving the trajectory point counter untouched.
        for _ in range(100):
            first.clock()
            second.clock()
            self.assertAlmostEqual(first.circlePos[1], second.circlePos[1])
            self.assertLessEqual(abs(first.circlePos[1] - 300), 249)
        self.assertEqual(first.counter, 100)
        self.assertEqual(second.counter, 100)
        self.assertEqual(first.getTimeSpeed(), 25)

    def test_periodicity_defaults_to_zero(self):
        trajectory = self.make_trajectory([(200, 200), (300, 200)], 100)
        self.assertEqual(trajectory.getWanderPeriodicity(), 0)
        trajectory.setWanderPeriodicity(0.7)
        trajectory.clear()
        self.assertEqual(trajectory.getWanderPeriodicity(), 0)

    def test_periodicity_sine_endpoint_and_continuous_blend(self):
        points = [(200, 300), (400, 300)]
        trajectories = [self.make_trajectory(points, 100) for _ in range(3)]
        for trajectory, value in zip(trajectories, (0, 0.3, 1)):
            trajectory.setWanderPeriodicity(value)
        sine_values = []
        for tick in range(1, 129):
            sine, mixed, noise = [t._advanceWander() for t in trajectories]
            self.assertAlmostEqual(sine, math.sin(2 * math.pi * tick * .025 / 1.6))
            self.assertAlmostEqual(mixed, sine * .7 + noise * .3)
            self.assertTrue(-1 <= mixed <= 1)
            sine_values.append(sine)
        for first, second in zip(sine_values[:64], sine_values[64:]):
            self.assertAlmostEqual(first, second)
        # Live edits re-evaluate the marker without resetting either phase or
        # advancing the trajectory, including when it is frozen.
        trajectory = trajectories[0]
        trajectory.clock()
        trajectory.setFreeze(True)
        phase, elapsed, counter = trajectory._wanderPhase, trajectory._wanderElapsed, trajectory.counter
        trajectory.setWanderPeriodicity(0.5)
        self.assertEqual((trajectory._wanderPhase, trajectory._wanderElapsed, trajectory.counter),
                         (phase, elapsed, counter))
        trajectory.setWanderPeriodicity(-1)
        self.assertEqual(trajectory.getWanderPeriodicity(), 0)
        trajectory.setWanderPeriodicity(2)
        self.assertEqual(trajectory.getWanderPeriodicity(), 1)

    def test_band_ends_have_fixed_small_rounded_corners(self):
        for width in (40, 80, 160):
            with self.subTest(width=width):
                trajectory = self.make_trajectory([(200, 200), (500, 200)], width)
                trajectory._normal = (0, 1)
                bitmap = wx.Bitmap(800, 600)
                dc = wx.MemoryDC(bitmap)
                dc.SetBackground(wx.Brush(wx.BLACK))
                dc.Clear()
                gc = wx.GraphicsContext.Create(dc)
                trajectory.draw(gc)
                del gc
                dc.SelectObject(wx.NullBitmap)
                image = bitmap.ConvertToImage()
                def lit(x, y):
                    return image.GetRed(x, y) + image.GetGreen(x, y) + image.GetBlue(x, y)
                # The seven-pixel number allowance is independent of width.
                self.assertEqual(lit(191, 200), 0)
                self.assertGreater(lit(194, 200), 0)
                # The far end never extends beyond the last point.
                self.assertGreater(lit(498, 200), 0)
                self.assertEqual(lit(502, 200), 0)
                # Corner pixels are rounded away, while the adjacent edge fills.
                top = 200 - width // 2
                self.assertEqual(lit(193, top), 0)
                self.assertGreater(lit(210, top + 1), 0)
                self.assertEqual(trajectory._normal, (0, 1))

    def test_crossings_and_retraced_bands_do_not_cancel(self):
        def render(trajectory):
            bitmap = wx.Bitmap(800, 600)
            dc = wx.MemoryDC(bitmap)
            dc.SetBackground(wx.Brush(wx.BLACK))
            dc.Clear()
            gc = wx.GraphicsContext.Create(dc)
            trajectory.draw(gc)
            del gc
            dc.SelectObject(wx.NullBitmap)
            return bitmap.ConvertToImage()

        crossing = [(400 + 180 * math.sin(i * math.tau / 240 + math.pi / 4),
                     300 + 120 * math.sin(2 * (i * math.tau / 240 + math.pi / 4)))
                    for i in range(240)]
        retraced = [(100 + i * 2, 300) for i in range(301)]
        retraced += list(reversed(retraced))
        for points, closed in ((crossing, True), (list(reversed(crossing)), True),
                               (retraced, False)):
            with self.subTest(closed=closed, start=points[0]):
                trajectory = self.make_trajectory(points, 100)
                trajectory.closed = closed
                image = render(trajectory)
                # Crossings retain exactly one layer of the translucent colour.
                expected = trajectory.getColour().Red() * 100 / 255
                self.assertAlmostEqual(image.GetRed(400, 300), expected, delta=1)
                self.assertEqual(image.GetRed(10, 10), 0)
        # The genuine hollow center of a circular band must remain empty.
        points = [(400 + 150 * math.cos(i * math.tau / 180),
                   300 + 150 * math.sin(i * math.tau / 180)) for i in range(180)]
        trajectory = self.make_trajectory(points, 80)
        trajectory.closed = True
        image = render(trajectory)
        self.assertEqual(image.GetRed(400, 300), 0)
        self.assertGreater(image.GetRed(550, 300), 0)

    def test_save_restore_undo_and_legacy_defaults(self):
        original = self.make_trajectory([(100, 100), (150, 100)], 42)
        original.closed = True
        original.setWanderSpeed(2.5)
        original.setWanderPeriodicity(0.35)
        attributes = original.getAttributes()
        encoded = xmlrpc.client.dumps((attributes,), allow_none=True)
        decoded = xmlrpc.client.loads(encoded)[0][0]
        restored = self.make_trajectory([(1, 1), (2, 2)])
        restored.setAttributes(decoded)
        self.assertEqual(restored.getWidth(), 42)
        self.assertEqual(restored.getWanderSpeed(), 2.5)
        self.assertEqual(restored.getWanderPeriodicity(), 0.35)
        self.assertTrue(restored.closed)
        restored.setWidth(90)
        restored.setAttributes(attributes)
        self.assertEqual(restored.getWidth(), 42)
        del decoded['wanderPeriodicity']
        del decoded['wanderSpeed']
        del decoded['width']
        del decoded['closed']
        restored.setAttributes(decoded)
        self.assertEqual(restored.getWidth(), 2)
        self.assertFalse(restored.closed)
        self.assertEqual(restored.getWanderSpeed(), 1)
        self.assertEqual(restored.getWanderPeriodicity(), 0)


if __name__ == '__main__':
    unittest.main()
