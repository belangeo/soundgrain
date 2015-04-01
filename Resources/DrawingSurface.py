import wx, os, math
from Resources.constants import *
from Resources.FxBall import FxBall
from Resources.Trajectory import Trajectory
from pyolib._wxwidgets import BACKGROUND_COLOUR

class MyFileDropTarget(wx.FileDropTarget):
    def __init__(self, window):
        wx.FileDropTarget.__init__(self)
        self.window = window

    def OnDropFiles(self, x, y, filenames):
        for file in filenames:
            ext = os.path.splitext(file)[1].replace(".", "")
            if ext.lower() == "sg":
                self.window.GetTopLevelParent().loadFile(ensureNFD(file))
            elif ext.lower() in ALLOWED_EXTENSIONS:
                self.window.GetTopLevelParent().controls.loadSound(ensureNFD(file))

class DrawingSurface(wx.Panel):
    def __init__(self, parent, pos=(0,0), size=wx.DefaultSize):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, pos=pos, size=size, style = wx.EXPAND)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.SetBackgroundColour(BACKGROUND_COLOUR)
        self.parent = parent
        dt = MyFileDropTarget(self)
        self.SetDropTarget(dt)
        self.useMario = False
        self.backBitmap = None
        self.needBitmap = True
        self.onMotion = False
        self.marios = [wx.Bitmap(os.path.join(IMAGES_PATH, 'Mario%d.png' % i), wx.BITMAP_TYPE_PNG) for i in [1,2,3,2,4,5,6,5]]
        if PLATFORM == 'linux2':
            self.font = wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL, face="Monospace")
            self.font_pos = wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL)
        elif PLATFORM == 'win32':
            self.font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL, face="Monospace")
            self.font_pos = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
        else:
            self.font = wx.Font(10, wx.NORMAL, wx.NORMAL, wx.NORMAL, face="Monospace")
            self.font_pos = wx.Font(10, wx.NORMAL, wx.NORMAL, wx.NORMAL)
        self.trajectories = [Trajectory(self, i+1) for i in range(MAX_STREAMS)]
        self.memorizedTrajectory = Trajectory(self, -1)
        self.memorizedId = {}
        self.midiTranspose = True
        self.midiXposition = 0
        self.midiOctaveSpread = 2
        self.fxballs = {}
        if len(self.fxballs) != 0:
            self.fxball = self.fxballs[0]
        self.fxballValues = [fx for fx in self.fxballs.values()]
        self.screenOffset = 2
        self.sndBitmap = None
        self.selected = self.trajectories[0]
        self.bitmapDict = {}
        self.closed = 0
        self.oscilPeriod = 2
        self.oscilScaling = 1
        self.mode = TRAJTYPES[0]
        self.pointerPos = None
        self.SetColors(outline=(255,255,255), bg=(30,30,30), fill=(184,32,32), rect=(0,255,0), losa=(0,0,255), wave=(70,70,70))
        self.currentSize = self.GetSizeTuple()

        self.Bind(wx.EVT_KEY_DOWN, self.KeyDown)
        self.Bind(wx.EVT_KEY_UP, self.KeyUp)
        self.Bind(wx.EVT_LEFT_DOWN, self.MouseDown)
        self.Bind(wx.EVT_LEFT_DCLICK, self.MouseDoubleClick)
        self.Bind(wx.EVT_LEFT_UP, self.MouseUp)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_MOTION, self.MouseMotion)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)

        if sys.platform == "win32":
            self.dcref = wx.BufferedPaintDC
        else:
            self.dcref = wx.PaintDC

    def setCurrentSize(self, size):
        self.currentSize = size
        self.needBitmap = True
        self.Refresh()

    def OnLeave(self, evt):
        self.pointerPos = None
        self.Refresh()
        evt.Skip()

    def OnResize(self, evt):
        w,h = self.GetSizeTuple()
        cX, cY = self.currentSize[0], self.currentSize[1]
        for t in self.getActiveTrajectories():
            for i, p in enumerate(t.getPoints()):
                xscl = p[0] / float(cX)
                yscl = p[1] / float(cY)
                t.points[i] = (w * xscl, h * yscl)
            t.setPointPos(t.getFirstPoint())
            if t.getType() in ['circle', 'oscil']:
                center = t.getCenter()
                xscl = center[0] / float(cX)
                yscl = center[1] / float(cY)
                t.setCenter((w * xscl, h * yscl))
                t.setRadius(t.getCenter()[0] - t.getFirstPoint()[0])
            t.setInitPoints()
        for fxball in self.fxballs.values():
            center = fxball.getCenter()
            size = fxball.getSize()
            scl = (w / (float(cX)) + (h / float(cY))) * 0.5
            fxball.setSize(int(size * scl))
            xscl = center[0] / float(cX)
            yscl = center[1] / float(cY)
            fxball.setCenter((w * xscl, h * yscl))

        self.currentSize = (w,h)
        self.needBitmap = True
        self.parent.controls.drawWaveform()
        wx.CallAfter(self.Refresh)

    def restoreFxBall(self, dict):
        self.fxballs[dict["id"]] = FxBall(dict["fx"], dict["id"], self.parent.sg_audio, dict["pos"], dict["size"], dict["gradient"], dict["fader"])
        self.parent.sg_audio.addFx(dict["fx"], dict["id"])
        self.fxballs[dict["id"]].load(dict["controls"])
        self.fxballValues = [fx for fx in self.fxballs.values()]
        self.needBitmap = True
        self.Refresh()

    def restoreFxBalls(self, dict, xfac=1.0, yfac=1.0):
        if dict != {}:
            for dic in dict.values():
                self.fxballs[dic["id"]] = FxBall(dic["fx"], dic["id"], self.parent.sg_audio, dic["pos"], 
                                            dic["size"], dic["gradient"], dic["fader"], xfac, yfac)
                self.parent.sg_audio.addFx(dic["fx"], dic["id"])
                self.fxballs[dic["id"]].load(dic["controls"])
            self.fxballValues = [fx for fx in self.fxballs.values()]
            self.needBitmap = True
            self.Refresh()

    def addFxBall(self, fx):
        key = -1
        fxkeys = self.fxballs.keys()
        for i in range(10):
            if i not in fxkeys:
                key = i
                break
        if key != -1:
            self.fxballs[key] = FxBall(fx, key, self.parent.sg_audio, (100,100))
            self.parent.sg_audio.addFx(fx, key)
            self.fxballValues = [fx for fx in self.fxballs.values()]
            self.needBitmap = True
            self.Refresh()

    def removeAllFxBalls(self):
        for key in self.fxballs.keys():
            self.fxballs[key].hideControls()
            del self.fxballs[key]
            self.parent.sg_audio.removeFx(key)
        self.fxballValues = [fx for fx in self.fxballs.values()]
        self.needBitmap = True
        self.Refresh()

    def removeFxBall(self, key):
        self.fxballs[key].hideControls()
        del self.fxballs[key]
        self.parent.sg_audio.removeFx(key)
        self.fxballValues = [fx for fx in self.fxballs.values()]
        self.needBitmap = True
        self.Refresh()

    def clock(self, which):
        t = self.trajectories[which]
        t.clock()
        if t.getActive():
            w,h = self.GetSizeTuple()
            w,h = float(w), float(h)
            if t.getPointPos() != None:
                x = t.getPointPos()[0]/w
                y = 1 - t.getPointPos()[1]/h
                self.parent.sg_audio.setXposition(which, x)
                self.parent.sg_audio.setYposition(which, y)

    def setMidiTranspose(self, value):
        self.midiTranspose = value

    def setMidiXposition(self, value):
        self.midiXposition = value

    def setMidiOctaveSpread(self, value):
        self.midiOctaveSpread = value

    def setOscilPeriod(self, period):
        self.oscilPeriod = period

    def getOscilPeriod(self):
        return self.oscilPeriod

    def setOscilScaling(self, scaling):
        self.oscilScaling = scaling

    def getOscilScaling(self):
        return self.oscilScaling

    def SetColors(self, outline, bg, fill, rect, losa, wave):
        self.outlinecolor = wx.Colour(*outline)
        self.backgroundcolor = wx.Colour(*bg)
        self.fillcolor = wx.Colour(*fill)
        self.rectcolor = wx.Colour(*rect)
        self.losacolor = wx.Colour(*losa)
        self.wavecolor = wx.Colour(*wave)
        self.losaBrush = wx.Brush(self.losacolor, wx.SOLID)
        self.losaPen = wx.Pen(self.losacolor, width=1, style=wx.SOLID)

    def getValues(self):
        w,h = self.GetSizeTuple()
        w,h = float(w), float(h)
        vals = []
        for t in self.trajectories:
            if t.getPointPos() != None:
                x = t.getPointPos()[0]/w
                y = 1 - t.getPointPos()[1]/h
                vals.append([x,y])
            else:
                vals.append([])
        return vals

    def setMode(self, mode):
        self.mode = TRAJTYPES[mode]

    def setClosed(self, closed):
        self.closed = closed

    def getTrajectory(self, which):
        return self.trajectories[which]

    def getAllTrajectories(self):
        return self.trajectories

    def getActiveTrajectories(self):
        return [t for t in self.trajectories if t.getActive()]

    def OnRightDown(self, evt):
        self.SetFocus()
        for t in self.getActiveTrajectories():
            if t.getInsideRect(evt.GetPosition()):
                t.clear()
                if len(self.getActiveTrajectories()) > 0:
                    self.setSelected(self.getActiveTrajectories()[0])
                else:
                    self.setSelected(self.getTrajectory(0))
                self.needBitmap = True
                self.Refresh()
                return
        mouseState = wx.GetMouseState()
        mousePos = (mouseState.GetX(), mouseState.GetY())
        for fxball in self.fxballs.values():
            if fxball.getInside(evt.GetPosition(), small=True):
                fxball.openControls(mousePos)
                return

    def setSelectedById(self, id):
        self.selected = self.trajectories[id]

    def setSelected(self, traj):
        self.selected = traj
        self.parent.controls.setSelected(self.selected.getId())

    def Memorize(self):
        w,h = self.GetSize()
        t = self.selected
        self.memorizedTrajectory.setType(t.getType())
        self.memorizedTrajectory.setTimeSpeed(t.getTimeSpeed())
        self.memorizedTrajectory.setStep(t.getStep())
        self.memorizedTrajectory.activateLp(self.parent.lowpass)
        self.memorizedTrajectory.setEditionLevel(self.parent.editionLevel)
        self.memorizedTrajectory.setPoints(t.getPoints())
        self.memorizedTrajectory.setInitPoints()
        if self.memorizedTrajectory.getType() not in  ['free', 'line']:
            self.memorizedTrajectory.setRadius(t.getRadius())
            self.memorizedTrajectory.setCenter(t.getCenter())
        if self.midiXposition:
            off = (w/2) - self.memorizedTrajectory.getFirstPoint()[0]
            self.memorizedTrajectory.move((off, 0))
            self.memorizedTrajectory.setInitPoints()

    def addTrajFromMemory(self, index, pitch, normy, midinote):
        t = self.memorizedTrajectory
        for new_t in self.trajectories:
            if not new_t.getActive():
                self.memorizedId[index] = new_t.getId()
                new_t.setTimeSpeed(t.getTimeSpeed())
                if self.midiTranspose:
                    new_t.setTranspo(pitch)
                else:
                    new_t.setTranspo(1.0)
                new_t.setStep(t.getStep())
                new_t.setActive(True)
                new_t.setType(self.mode)
                new_t.lpx.reinit()
                new_t.lpy.reinit()
                new_t.activateLp(self.parent.lowpass)
                new_t.setEditionLevel(self.parent.editionLevel)
                new_t.setPoints(t.getPoints())
                new_t.setInitPoints()
                if new_t.getType() == 'free':
                    pass
                else:
                    new_t.setCenter(t.getCenter())
                    new_t.setRadius(t.getRadius())
                break
        Xs = [p[0] for p in new_t.getPoints()]
        extremeXs = (min(Xs), max(Xs))
        Ys = [p[1] for p in new_t.getPoints()]
        extremeYs = (min(Ys), max(Ys))
        if new_t.getType() not in  ['free', 'line']:
            curCenter = new_t.getCenter()
        downPos = new_t.getFirstPoint()
        w,h = self.GetSize()
        if not self.midiXposition:
            x, y = downPos[0], int((1.-normy)*h)
        else:
            if pitch <= 1:
                normx = int((w/2) - (w * (60 - midinote) / 12. / self.midiOctaveSpread))
            else:
                normx = int((w/2) + (w * (midinote - 60) / 12. / self.midiOctaveSpread))
            x,y = normx, int((1.-normy)*h)
        if new_t.getType() in ['free', 'line']:
            offset = (downPos[0] - x, downPos[1] - y)
            clipedOffset = self.clip(offset, extremeXs, extremeYs)
            new_t.move(clipedOffset)
        else:
            offset = (downPos[0] - x, downPos[1] - y)
            center, clipedOffset = self.clipCircleMove(new_t.getRadius(), curCenter, offset)
            new_t.setCenter(center)
            new_t.move(clipedOffset)
        self.needBitmap = True
        self.Refresh()

    def deleteMemorizedTraj(self, index):
        id = self.memorizedId[index]
        t = self.trajectories[id]
        t.clear()
        if len(self.getActiveTrajectories()) > 0:
            self.setSelected(self.getActiveTrajectories()[0])
        else:
            self.setSelected(self.getTrajectory(0))
        self.needBitmap = True
        self.Refresh()

    def KeyDown(self, evt):
        if evt.GetKeyCode() in [wx.WXK_BACK, wx.WXK_DELETE, wx.WXK_NUMPAD_DELETE]:
            if self.selected != None:
                self.selected.clear()
                if len(self.getActiveTrajectories()) > 0:
                    self.setSelected(self.getActiveTrajectories()[0])
                else:
                    self.setSelected(self.getTrajectory(0))
            evt.StopPropagation()
            return

        off = {wx.WXK_UP: [0,1], wx.WXK_DOWN: [0,-1], wx.WXK_LEFT: [1,0], wx.WXK_RIGHT: [-1,0]}.get(evt.GetKeyCode(), [0,0])
        # Move selected trajectory
        if evt.ShiftDown() and off != [0,0]:
            traj = self.trajectories[self.parent.controls.getSelected()]
            if traj.getType() in ['circle', 'oscil']:
                center = traj.getCenter()
                traj.setCenter((center[0]-off[0], center[1]-off[1]))
            traj.move(off)
            traj.setInitPoints()
            self.onMotion = True
            evt.StopPropagation()
            return
        # Move all trajectories
        elif off != [0,0]:
            for traj in self.getActiveTrajectories():
                if traj.getType() in ['circle', 'oscil']:
                    center = traj.getCenter()
                    traj.setCenter((center[0]-off[0], center[1]-off[1]))
                traj.move(off)
                traj.setInitPoints()
            self.onMotion = True
            evt.StopPropagation()
            return
        # Set freeze mode
        if evt.GetKeyCode() < 256:
            c = chr(evt.GetKeyCode())
            if c in ['1', '2', '3', '4', '5', '6', '7', '8']:
                if self.trajectories[int(c)-1].getFreeze():
                    self.trajectories[int(c)-1].setFreeze(False)
                else:
                    self.trajectories[int(c)-1].setFreeze(True)
            elif c == '0':
                for i in range(8):
                    if self.trajectories[i].getFreeze():
                        self.trajectories[i].setFreeze(False)
                    else:
                        self.trajectories[i].setFreeze(True)
            elif c == '9':
                if not self.useMario:
                    self.useMario = True
                else:
                    self.useMario = False
        evt.Skip()

    def KeyUp(self, evt):
        self.onMotion = False
        if evt.GetKeyCode() in [wx.WXK_BACK, wx.WXK_DELETE, wx.WXK_NUMPAD_DELETE, wx.WXK_UP, wx.WXK_DOWN, wx.WXK_LEFT, wx.WXK_RIGHT]:
            self.needBitmap = True
            self.Refresh()

    def MouseDoubleClick(self, evt):
        self.SetFocus()
        self.downPos = evt.GetPositionTuple()
        for t in self.getActiveTrajectories():
            # Select or duplicate trajectory
            if t.getInsideRect(self.downPos):
                for new_t in self.trajectories:
                    if not new_t.getActive():
                        self.setSelected(new_t)
                        self.selected.setActive(True)
                        self.selected.setType(t.getType())
                        self.selected.lpx.reinit()
                        self.selected.lpy.reinit()
                        self.selected.activateLp(self.parent.lowpass)
                        self.selected.setEditionLevel(self.parent.editionLevel)
                        self.selected.setPoints(t.getPoints())
                        self.selected.setInitPoints()
                        if self.selected.getType() not in  ['free', 'line']:
                            self.selected.setRadius(t.getRadius())
                            self.selected.setCenter(t.getCenter())
                        break
                else:
                    self.setSelected(t)
                Xs = [p[0] for p in self.selected.getPoints()]
                self.extremeXs = (min(Xs), max(Xs))
                Ys = [p[1] for p in self.selected.getPoints()]
                self.extremeYs = (min(Ys), max(Ys))
                self.action = 'drag'
                if self.selected.getType() not in  ['free', 'line']:
                    self.curCenter = self.selected.getCenter()
                self.CaptureMouse()
                return

        for key, fxball in self.fxballs.items():
            if fxball.getInside(self.downPos, small=True):
                self.removeFxBall(key)
                break

        evt.Skip()

    def MouseDown(self, evt):
        self.SetFocus()
        self.downPos = evt.GetPositionTuple()
        for t in self.getActiveTrajectories():
            # Select or duplicate trajectory
            if t.getInsideRect(self.downPos):
                if evt.AltDown():
                    for new_t in self.trajectories:
                        if not new_t.getActive():
                            self.setSelected(new_t)
                            self.selected.setActive(True)
                            self.selected.setType(t.getType())
                            self.selected.lpx.reinit()
                            self.selected.lpy.reinit()
                            self.selected.activateLp(self.parent.lowpass)
                            self.selected.setEditionLevel(self.parent.editionLevel)
                            self.selected.setPoints(t.getPoints())
                            self.selected.setInitPoints()
                            if self.selected.getType() not in  ['free', 'line']:
                                self.selected.setRadius(t.getRadius())
                                self.selected.setCenter(t.getCenter())
                            break
                else:
                    self.setSelected(t)
                Xs = [p[0] for p in self.selected.getPoints()]
                self.extremeXs = (min(Xs), max(Xs))
                Ys = [p[1] for p in self.selected.getPoints()]
                self.extremeYs = (min(Ys), max(Ys))
                self.curCenters = [traj.getCenter() for traj in self.getActiveTrajectories()]
                self.action = 'drag'
                if self.selected.getType() not in  ['free', 'line']:
                    self.curCenter = self.selected.getCenter()
                self.CaptureMouse()
                return
            # Rescale circle or oscil trajectory
            if t.getInsideLosange(self.downPos):
                self.setSelected(t)
                self.action = 'rescale'
                self.CaptureMouse()
                return
            # Check for trajectory transformation
            for p in t.getPoints():
                if wx.Rect(p[0]-5, p[1]-5, 10, 10).Contains(self.downPos):
                    self.pindex = t.getPoints().index(p)
                    self.setSelected(t)
                    self.action = 'edit'
                    self.CaptureMouse()
                    return
        # Check if inside an FxBall
        for key, fxball in self.fxballs.items():
            if fxball.getInside(self.downPos, small=True):
                if evt.AltDown():
                    self.removeFxBall(key)
                else:
                    self.fxball = fxball
                    self.action = 'drag_ball'
                    self.CaptureMouse()
                return
            elif fxball.getInside(self.downPos, small=False):
                if evt.AltDown():
                    self.removeFxBall(key)
                    self.Refresh()
                else:
                    self.fxball = fxball
                    self.action = 'rescale_ball'
                    self.CaptureMouse()
                return

        # Click in an empty space, draw a new trajectory
        self.action = 'draw'
        for t in self.trajectories:
            if not t.getActive():
                self.traj = t
                self.traj.setActive(True)
                self.traj.setType(self.mode)
                self.traj.lpx.reinit()
                self.traj.lpy.reinit()
                self.traj.activateLp(self.parent.lowpass)
                self.traj.setEditionLevel(self.parent.editionLevel)
                if self.traj.getType() == 'free':
                    self.traj.addPoint(self.clipPos(self.downPos))
                else:
                    self.traj.setCenter(self.downPos)
                    self.traj.setRadius(0)
                self.CaptureMouse()
                self.Refresh()
                break
            else:
                self.traj = None
        evt.Skip()

    def MouseUp(self, evt):
        if self.HasCapture():
            if self.action == 'draw' and self.traj:
                if len(self.traj.getPoints()) <= 1:
                    self.traj.clear()
                    self.ReleaseMouse()
                    return
                if self.traj.getType() == 'free':
                    self.traj.addFinalPoint(self.clipPos(evt.GetPositionTuple()), self.closed)
                    if self.parent.fillPoints:
                        self.traj.fillPoints(self.closed)
                    self.traj.setInitPoints()
                elif self.traj.getType() in ['circle', 'oscil']:
                    if self.parent.fillPoints:
                        self.traj.fillPoints(False)
                    self.traj.setInitPoints()
                else:
                    if self.parent.fillPoints:
                        self.traj.fillPoints(False)
                    self.traj.setInitPoints()
            elif self.action == 'drag':
                self.selected.setInitPoints()
            elif self.action == 'rescale':
                if self.selected.getType() == 'circle':
                    if self.parent.fillPoints:
                        self.selected.fillPoints(True)
                else:
                    if self.parent.fillPoints:
                        self.selected.fillPoints(False)
                self.selected.setInitPoints()
            elif self.action == 'edit':
                if self.parent.fillPoints:
                    self.selected.fillPoints(False)
                self.selected.setInitPoints()
                self.selected.setType('free')
            elif self.action in ['drag_ball', 'rescale_ball']:
                self.fxball.restoreGradient()
                self.fxball.restoreCenter()

            self.Refresh()
            self.ReleaseMouse()
            if self.action not in ['drag_ball', 'rescale_ball']:
                self.parent.createTempFile()
            self.onMotion = False
            self.needBitmap = True
        evt.Skip()

    def MouseMotion(self, evt):
        self.pointerPos = evt.GetPositionTuple()
        if self.HasCapture() and evt.Dragging() and evt.LeftIsDown():
            if self.action == 'draw' and self.traj:
                if self.traj.getType() == 'free':
                    self.traj.addPoint(self.clipPos(evt.GetPositionTuple()))
                elif self.traj.getType() == 'line':
                    self.traj.points = []
                    self.traj.lpx.reinit()
                    self.traj.lpy.reinit()
                    x,y = self.clipPos(evt.GetPositionTuple())

                    x2 = abs(x-self.downPos[0])
                    y2 = abs(y-self.downPos[1])
                    maxstep = int(math.sqrt(x2*x2+y2*y2))

                    if self.downPos[0] == x: xdir = 0
                    elif self.downPos[0] < x: xdir = 1
                    else: xdir = -1
                    if self.downPos[1] == y: ydir = 0
                    elif self.downPos[1] < y: ydir = 1
                    else: ydir = -1

                    for i in range(0, maxstep, 2):
                        xpt = self.downPos[0] + xdir * int(x2 * i / float(maxstep))
                        ypt = self.downPos[1] + ydir * int(y2 * i / float(maxstep))
                        self.traj.addPoint((int(round(xpt)),int(round(ypt))))
                else:
                    Xlen = abs(self.downPos[0] - evt.GetPosition()[0])
                    Ylen = abs(self.downPos[1] - evt.GetPosition()[1])
                    self.traj.setRadius(self.clipCirclePos(math.sqrt( Xlen**2 + Ylen**2 ), self.traj.getCenter(), self.traj.getRadius()))
                    r = self.traj.getRadius()
                    halfR = int(round(r/2.))
                    if halfR <= 1: scaleR = 1
                    else: scaleR = 1./(halfR-1)
                    self.traj.points = []
                    self.traj.lpx.reinit()
                    self.traj.lpy.reinit()
                    if self.traj.getType() == 'circle':
                        for i in range(-halfR,halfR+1):
                            a = i * scaleR * r
                            x = math.cos(math.pi * i * scaleR) * r
                            y = math.sin(math.pi * i * scaleR) * r
                            self.traj.addCirclePoint((int(round(x + self.downPos[0])), int(round(y + self.downPos[1]))))
                    else:
                        for i in range(int(-halfR * self.oscilScaling), int(halfR * self.oscilScaling + 1)):
                            a = i * scaleR * r
                            x = math.cos(math.pi * i * scaleR) * r
                            y = math.sin(math.pi * self.oscilPeriod * i * scaleR) * r
                            self.traj.addCirclePoint((int(round(x + self.downPos[0])), int(round(y + self.downPos[1]))))

            elif self.action == 'drag':
                if self.selected.getType() in ['free', 'line']:
                    x,y = evt.GetPositionTuple()
                    offset = (self.downPos[0] - x, self.downPos[1] - y)
                    clipedOffset = self.clip(offset, self.extremeXs, self.extremeYs)
                    self.selected.move(clipedOffset)
                else:
                    x,y = self.clipPos(evt.GetPositionTuple())
                    offset = (self.downPos[0] - x, self.downPos[1] - y)
                    center, clipedOffset = self.clipCircleMove(self.selected.getRadius(), self.curCenter, offset)
                    self.selected.setCenter(center)
                    self.selected.move(clipedOffset)
                if evt.ShiftDown():
                    for traj in self.getActiveTrajectories():
                        if traj != self.selected:
                            if traj.getType() in ['free', 'line']:
                                clipedOffset = self.clip(offset, self.extremeXs, self.extremeYs)
                                traj.move(clipedOffset)
                            else:
                                center, clipedOffset = self.clipCircleMove(traj.getRadius(), self.curCenters[traj.getId()], offset)
                                traj.setCenter(center)
                                traj.move(clipedOffset)

            elif self.action == 'rescale':
                Xlen = abs(self.selected.getCenter()[0] - evt.GetPosition()[0])
                Ylen = abs(self.selected.getCenter()[1] - evt.GetPosition()[1])
                self.selected.setRadius(self.clipCirclePos(math.sqrt( Xlen**2 + Ylen**2 ), self.selected.getCenter(), self.selected.getRadius()))
                r = self.selected.getRadius()
                halfR = int(round(r/2.))
                if halfR <= 1: scaleR = 1
                else: scaleR = 1./(halfR-1)
                self.selected.points = []
                self.selected.lpx.reinit()
                self.selected.lpy.reinit()
                if self.selected.getType() == 'circle':
                    for i in range(-halfR,halfR+1):
                        a = i * scaleR * r
                        x = math.cos(math.pi * i * scaleR) * r
                        y = math.sin(math.pi * i * scaleR) * r
                        self.selected.addCirclePoint((int(round(x + self.selected.getCenter()[0])), int(round(y + self.selected.getCenter()[1]))))
                else:
                    for i in range(int(-halfR * self.oscilScaling), int(halfR * self.oscilScaling + 1)):
                        a = i * scaleR * r
                        x = math.cos(math.pi * i * scaleR) * r
                        y = math.sin(math.pi * self.oscilPeriod * i * scaleR) * r
                        self.selected.addCirclePoint((int(round(x + self.selected.getCenter()[0])), int(round(y + self.selected.getCenter()[1]))))
            elif self.action == 'edit':
                x,y = evt.GetPositionTuple()
                offset = (self.downPos[0] - x, self.downPos[1] - y)
                self.selected.editTraj(self.pindex, offset)
            elif self.action == 'drag_ball':
                pos = evt.GetPositionTuple()
                if evt.ShiftDown():
                    off = (self.downPos[1] - pos[1])
                    self.fxball.setGradient(off)
                else:
                    self.fxball.move(pos)
            elif self.action == 'rescale_ball':
                pos = evt.GetPositionTuple()
                x = self.fxball.center[0] - pos[0]
                y = self.fxball.center[1] - pos[1]
                hyp = math.sqrt(x*x+y*y)
                if hyp < 5: hyp = 5
                self.fxball.resize(hyp*2)

            self.onMotion = True
            self.Refresh()
        evt.Skip()

    def draw(self, dc):
        gc = wx.GraphicsContext_Create(dc)
        dc.BeginDrawing()
        dc.SetTextForeground("#000000")
        dc.SetFont(self.font)
        if not self.sndBitmap:
            w,h = self.GetSizeTuple()
            dc.SetBrush(wx.Brush(self.backgroundcolor, wx.SOLID))
            dc.Clear()
            dc.SetPen(wx.Pen(self.outlinecolor, width=1, style=wx.SOLID))
            dc.DrawRectangle(0, 0, w, h)
        else:
            dc.DrawBitmap(self.sndBitmap,0,0)

        [dc.DrawBitmap(fx.bit, fx.pos[0], fx.pos[1], True) for fx in self.fxballValues]

        selectedTraj = self.parent.controls.getSelected()
        activeTrajs = [t for t in self.getActiveTrajectories() if len(t.getPoints()) > 1]
        for t in activeTrajs:
            recsize = 14
            s2 = recsize / 2
            gc.SetBrush(t.getBrush(trans=True))
            gc.SetPen(t.getPen(big=True))
            if len(t.getPoints()) >= 2:
                gc.DrawLines(t.getPoints())
            if t.getId() == selectedTraj:
                recsize = 14
                s2 = recsize / 2
                self.selected = t
                gc.SetPen(wx.Pen("#EEEEEE", width=2, style=wx.SOLID))
            if t.getFirstPoint() != None:
                gc.SetBrush(t.getBrush())
                gc.DrawRoundedRectangle(t.getFirstPoint()[0]-s2, t.getFirstPoint()[1]-s2, recsize, recsize, 2)
                dc.DrawLabel(str(t.getLabel()), wx.Rect(t.getFirstPoint()[0]-s2,t.getFirstPoint()[1]-s2, recsize, recsize), wx.ALIGN_CENTER)
                if t.getType() in ['circle', 'oscil']:
                    gc.SetBrush(self.losaBrush)
                    gc.SetPen(self.losaPen)
                    gc.DrawRoundedRectangle(t.getLosangePoint()[0]-5, t.getLosangePoint()[1]-5, 10, 10, 2)
        dc.EndDrawing()

    def drawBackBitmap(self):
        w,h = self.currentSize
        if self.backBitmap == None or self.backBitmap.GetSize() != self.currentSize:
            self.backBitmap = wx.EmptyBitmap(w,h)
        dc = wx.MemoryDC(self.backBitmap)
        self.draw(dc)
        dc.SelectObject(wx.NullBitmap)
        self.needBitmap = False

    def OnPaint(self, evt):
        dc = self.dcref(self)
        gc = wx.GraphicsContext_Create(dc)
        dc.BeginDrawing()

        if self.onMotion or self.needBitmap:
            self.drawBackBitmap()
        dc.DrawBitmap(self.backBitmap,0,0)

        activeTrajs = [t for t in self.getActiveTrajectories() if len(t.getPoints()) > 1 and t.circlePos]
        self.parent.sg_audio.setMixerChannelAmps(activeTrajs, self.fxballValues)

        if not self.useMario:
            for t in activeTrajs:
                if t.circlePos != None:
                    gc.SetPen(t.getPen())
                    gc.SetBrush(t.getBrush())
                    gc.DrawEllipse(t.circlePos[0]-5, t.circlePos[1]-5, 10, 10)
                    gc.SetPen(t.getBorderPen())
                    gc.SetBrush(t.getBorderBrush())
                    gc.DrawEllipse(t.circlePos[0]-2, t.circlePos[1]-2, 4, 4)
        else:
            for t in activeTrajs:
                if t.lastCirclePos[0] < t.circlePos[0]: marioff = 0
                else: marioff = 4
                bitmario = self.marios[t.mario + marioff]
                dc.DrawBitmap(bitmario, t.circlePos[0]-8, t.circlePos[1]-8, True)

        if self.pointerPos != None:
            w,h = self.GetSizeTuple()
            dc.SetTextForeground("#FFFFFF")
            dc.SetFont(self.font_pos)
            xvalue = self.pointerPos[0] / float(w) * self.parent.controls.sndDur
            yvalue = (h - self.pointerPos[1]) / float(h)
            dc.DrawText("X: %.3f   Y: %.3f" % (xvalue, yvalue), w-100, h-13)
        dc.EndDrawing()

    def clip(self, off, exXs, exYs):
        Xs = [p[0] for p in self.selected.getPoints()]
        minX, maxX = min(Xs), max(Xs)
        Ys = [p[1] for p in self.selected.getPoints()]
        minY, maxY = min(Ys), max(Ys)
        x,y = off
        sizex, sizey = self.GetSizeTuple()
        offset = self.screenOffset
        if exXs[0] - off[0] >= offset and exXs[1] - off[0] <= sizex - offset:
            x = x
        elif exXs[1] - off[0] >= sizex - offset:
            x = exXs[1] - sizex + offset
        else:
            x = exXs[0] - offset - 1
        if exYs[0] - off[1] >= offset and exYs[1] - off[1] <= sizey - offset:
            y = y
        elif exYs[1] - off[1] >= sizey - offset:
            y = exYs[1] - sizey + offset
        else:
            y = exYs[0] - offset - 1
        return (x,y)

    def clipPos(self, pos):
        x,y = pos
        sizex, sizey = self.GetSizeTuple()
        offset = self.screenOffset
        if x < offset: x = offset
        elif x > (sizex-offset): x = sizex - offset
        else: x = x
        if y < offset: y = offset
        elif y > (sizey-offset): y = sizey - offset
        else: y = y
        return (x,y)

    def clipCirclePos(self, rad, center, lastRad):
        sizex, sizey = self.GetSizeTuple()
        offset = self.screenOffset
        flag = True
        radius1 = radius2 = radius3 = radius4 = 1000000
        if center[0] - rad <= 0 + offset:
            radius1 = center[0] - offset
            flag = False
        if center[1] - rad <= 0 + offset:
            radius2 = center[1] - offset
            flag = False
        if center[0] + rad >= sizex - offset:
            radius3 = sizex - offset - center[0]
            flag = False
        if center[1] + rad >= sizey - offset:
            radius4 = sizey - offset - center[1]
            flag = False
        if flag:
            return rad
        else:
            return min(radius1, radius2, radius3, radius4)

    def clipCircleMove(self, rad, center, offset):
        sizex, sizey = self.GetSizeTuple()
        off = self.screenOffset
        if center[0] - offset[0] - rad >= 0 + off and center[0] - offset[0] + rad <= sizex - off:
            cx = center[0] - offset[0]
            offx = offset[0]
        elif center[0] - offset[0] + rad >= sizex - off:
            cx = sizex - off - rad
            offx = center[0] - cx
        else:
            cx = 0 + off + rad
            offx = center[0] - cx
        if center[1] - offset[1] - rad >= 0 + off and center[1] - offset[1] + rad <= sizey - off:
            cy = center[1] - offset[1]
            offy = offset[1]
        elif center[1] - offset[1] + rad >= sizey - off:
            cy = sizey - off - rad
            offy = center[1] - cy
        else:
            cy = 0 + off + rad
            offy = center[1] - cy
        return [cx, cy], [offx, offy]

    def analyse(self, file):
        self.file = file
        self.list = self.parent.sg_audio.getViewTable(self.GetSizeTuple())
        self.bitmapDict[self.file] = self.list
        self.create_bitmap()

    def create_bitmap(self):
        size = self.GetSizeTuple()
        self.sndBitmap = wx.EmptyBitmap(size[0], size[1])
        memory = wx.MemoryDC()
        memory.SelectObject(self.sndBitmap)
        gc = wx.GraphicsContext_Create(memory)
        gc.SetPen(wx.Pen("#3F3F44"))
        gc.SetBrush(wx.Brush("#3F3F44", style=wx.TRANSPARENT))
        memory.SetBrush(wx.Brush(self.backgroundcolor))
        memory.DrawRectangle(0,0,size[0],size[1])
        for samples in self.list:
            if len(samples):
                gc.DrawLines(samples)
        memory.SelectObject(wx.NullBitmap)
        self.needBitmap = True
        self.Refresh()
