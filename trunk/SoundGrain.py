#!/usr/bin/env python
# encoding: utf-8
"""
Copyright 2009 Olivier Belanger

This file is part of SoundGrain.

SoundGrain is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

SoundGrain is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with SoundGrain.  If not, see <http://www.gnu.org/licenses/>.
"""

import os, sys, math, tempfile, xmlrpclib, time
import wx
from wx.lib.wordwrap import wordwrap
import  wx.lib.scrolledpanel as scrolled
import wx.html
import wx.richtext

from Resources.constants import *
from Resources.audio import *
from Resources.Modules import *
from pyolib._wxwidgets import ControlSlider, VuMeter, Grapher
from Resources.Trajectory import Trajectory
from Resources.FxBall import FxBall
from Resources.MidiSettings import MidiSettings

class DrawingSurface(wx.Panel):
    def __init__(self, parent, pos=(0,0), size=wx.DefaultSize):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, pos=pos, size=size, style = wx.EXPAND)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.SetBackgroundColour(BACKGROUND_COLOUR)
        self.parent = parent
        self.useMario = False
        self.backBitmap = None
        self.needBitmap = True
        self.onMotion = False
        self.pdc = wx.PseudoDC()
        self.marios = [wx.Bitmap(os.path.join(IMAGES_PATH, 'Mario%d.png' % i), wx.BITMAP_TYPE_PNG) for i in [1,2,3,2,4,5,6,5]]
        if PLATFORM in ['win32', 'linux2']:
            self.font = wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL)
            self.font_pos = wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL)
        else:
            self.font = wx.Font(10, wx.NORMAL, wx.NORMAL, wx.NORMAL)
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
        self.Bind(wx.EVT_LEFT_UP, self.MouseUp)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_MOTION, self.MouseMotion)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)

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

    def restoreFxBalls(self, dict):
        if dict != {}:
            for dic in dict.values():
                self.fxballs[dic["id"]] = FxBall(dic["fx"], dic["id"], self.parent.sg_audio, dic["pos"], dic["size"], dic["gradient"], dic["fader"])
                self.parent.sg_audio.addFx(dic["fx"], dic["id"])
                self.fxballs[dic["id"]].load(dic["controls"])
            self.fxballValues = [fx for fx in self.fxballs.values()]
            self.needBitmap = True
            self.Refresh()

    def addFxBall(self, fx):
        key = -1
        fxkeys = self.fxballs.keys()
        for i in range(8):
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
            del self.fxballs[key]
            self.parent.sg_audio.removeFx(key)
        self.fxballValues = [fx for fx in self.fxballs.values()]
        self.needBitmap = True
        self.Refresh()

    def removeFxBall(self, key):
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
        self.outlinecolor = wx.Color(*outline)
        self.backgroundcolor = wx.Color(*bg)
        self.fillcolor = wx.Color(*fill)
        self.rectcolor = wx.Color(*rect)
        self.losacolor = wx.Color(*losa)
        self.wavecolor = wx.Color(*wave)
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

    def addTrajFromMemory(self, index, pitch, normy):
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
                normx = int((w/2) - (w * (1. - pitch) / self.midiOctaveSpread))
            else:
                normx = int((w/2) + (w * (1. - (1. / pitch)) / self.midiOctaveSpread))
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
        # Move all trajectories
        elif off != [0,0]:
            for traj in self.getActiveTrajectories():
                if traj.getType() in ['circle', 'oscil']:
                    center = traj.getCenter()
                    traj.setCenter((center[0]-off[0], center[1]-off[1]))
                traj.move(off)
                traj.setInitPoints()
            self.onMotion = True
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

    def MouseDown(self, evt):
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
                        self.fxballs.remove(fxball)
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
            dc.SetBrush(t.getBrush())
            dc.SetPen(t.getPen())
            dc.DrawLines(t.getPoints())
            if t.getId() == selectedTraj:
                dc.SetPen(wx.Pen("#EEEEEE", width=2, style=wx.SOLID))
            dc.DrawRoundedRectanglePointSize(t.getFirstPoint(), (13,13), 2)
            dc.DrawLabel(str(t.getLabel()), wx.Rect(t.getFirstPoint()[0],t.getFirstPoint()[1], 13, 13), wx.ALIGN_CENTER)
            if t.getType() in ['circle', 'oscil']:
                dc.SetBrush(self.losaBrush)
                dc.SetPen(self.losaPen)
                dc.DrawRoundedRectanglePointSize((t.getLosangePoint()[0]-5,t.getLosangePoint()[1]-5), (10,10), 1)
        dc.EndDrawing()

    def drawBackBitmap(self):
        w,h = self.currentSize #self.GetSizeTuple()
        if self.backBitmap == None or self.backBitmap.GetSize() != self.currentSize:
            self.backBitmap = wx.EmptyBitmap(w,h)
        dc = wx.MemoryDC(self.backBitmap)
        self.draw(dc)
        dc.SelectObject(wx.NullBitmap)
        self.needBitmap = False

    def drawOnMotion(self):
        self.pdc.RemoveAll()
        self.draw(self.pdc)
        
    def OnPaint(self, evt):
        dc = wx.AutoBufferedPaintDC(self)
        dc.BeginDrawing()
        if self.needBitmap:
            self.drawBackBitmap()
            
        if self.onMotion:
            self.drawOnMotion()
            self.pdc.DrawToDC(dc)
        else:
            dc.DrawBitmap(self.backBitmap,0,0)

        activeTrajs = [t for t in self.getActiveTrajectories() if len(t.getPoints()) > 1 and t.circlePos]
        self.parent.sg_audio.setMixerChannelAmps(activeTrajs, self.fxballValues)

        if not self.useMario:
            for t in activeTrajs:
                dc.SetPen(t.getPen())
                dc.SetBrush(t.getBrush())
                dc.DrawCirclePoint(t.circlePos, 4)
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
        self.list = self.parent.sg_audio.getViewTable()
        self.bitmapDict[self.file] = self.list
        self.create_bitmap()
        
    def create_bitmap(self):
        gradient = True
        size = self.GetSizeTuple()
        X = size[0]
        self.length = len(self.list[0])
        scalar = float(X) / (self.length - 1)
        self.sndBitmap = wx.EmptyBitmap(size[0], size[1])
        self.memory = wx.MemoryDC()
        self.memory.SelectObject(self.sndBitmap)
        # dc background  
        self.memory.SetBrush(wx.Brush(self.backgroundcolor))
        self.memory.DrawRectangle(0,0,size[0],size[1])
        new_Y = size[1]  / float(len(self.list))
        l = []
        append = l.append
        for chan in range(len(self.list)):
            halfY = new_Y / 2
            off = new_Y * chan
            self.memory.SetPen(wx.Pen('#333333', 1))
            self.memory.DrawLine(0,halfY+off,size[0],halfY+off)
            
            # draw waveform    
            self.memory.SetPen(wx.Pen(self.wavecolor, 1)) 
            if gradient:
                if self.list[chan]:
                    last = 0
                    for i in range(X):
                        y = int(round(i / scalar))
                        val = int(((halfY * self.list[chan][y]) + last) / 2)
                        valToDraw = val * 1.5
                        rec = wx.Rect(i, halfY+off, 1, valToDraw)
                        self.memory.GradientFillLinear(rec, "#999999", "#222222", wx.BOTTOM)
                        rec = wx.Rect(i, halfY+off-valToDraw, 1, valToDraw)
                        self.memory.GradientFillLinear(rec, "#999999", "#222222", wx.UP)
                        last = val                
            else:    
                if self.list[chan]:
                    last = 0
                    for i in range(X):
                        y = int(round(i / scalar))
                        val = int(((halfY * self.list[chan][y]) + last) / 2)
                        valToDraw = val * 1.5
                        append((i,halfY+off,i,halfY+off+valToDraw))
                        append((i,halfY+off,i,halfY+off-valToDraw))
                        last = val
        if not gradient:                
            self.memory.DrawLineList(l)
        self.memory.SelectObject(wx.NullBitmap)
        self.needBitmap = True
        self.Refresh()

class ControlPanel(scrolled.ScrolledPanel):
    def __init__(self, parent, surface):
        scrolled.ScrolledPanel.__init__(self, parent, -1)
        self.SetBackgroundColour(BACKGROUND_COLOUR)
        self.parent = parent
        self.surface = surface
        self.type = 0
        self.selected = 0
        self.selectedOkToChange = True
        self.sndPath = None
        self.sndDur = 0.0
        self.amplitude = 1
        self.nchnls = 2
        self.samplingRate = 44100
        self.midiInterface = None
        self.fileformat = 0
        self.sampletype = 0
        self.tempState = None

        box = wx.BoxSizer(wx.VERTICAL)

        box.Add(wx.StaticText(self, -1, "Trajectories"), 0, wx.CENTER|wx.TOP, 3)

        typeBox = wx.BoxSizer(wx.HORIZONTAL)
        popupBox = wx.BoxSizer(wx.VERTICAL)
        self.trajType = wx.Choice(self, -1, choices = ['Free', 'Circle', 'Oscil', 'Line'])
        self.trajType.SetSelection(0)
        popupBox.Add(self.trajType)
        typeBox.Add(popupBox, 0, wx.CENTER|wx.RIGHT, 5)
     
        self.closedToggle = wx.ToggleButton(self, -1, 'Closed', size=(55,-1))
        font = self.closedToggle.GetFont()
        if PLATFORM in ['win32', 'linux2']:
            font = wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL)        
        self.closedToggle.SetFont(font)   
        typeBox.Add(self.closedToggle, wx.CENTER|wx.RIGHT, 5 )
        box.Add(typeBox, 0, wx.CENTER|wx.ALL, 5)

        self.notebook = wx.Notebook(self, -1, style=wx.BK_DEFAULT | wx.EXPAND)
        self.drawing = DrawingParameters(self.notebook)
        self.playback = PlaybackParameters(self.notebook)
        self.notebook.AddPage(self.drawing, "Drawing")
        self.notebook.AddPage(self.playback, "Playback")
        box.Add(self.notebook, 0, wx.ALL, 5)

        box.Add(wx.StaticText(self, -1, "Global amplitude (dB)"), 0, wx.LEFT | wx.TOP, 10)
        ampBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_amp = ControlSlider(self, -60, 18, 0, size=(200, 16), outFunction=self.handleAmp)
        ampBox.Add(self.sl_amp, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(ampBox, 0, wx.LEFT | wx.RIGHT, 5)
        box.AddSpacer(10)
        self.meter = VuMeter(self, size=(200,11))
        self.meter.setNumSliders(self.nchnls)
        box.Add(self.meter, 0, wx.LEFT, 10)
        box.AddSpacer(5)

        box.Add(wx.StaticLine(self, size=(210, 1)), 0, wx.ALL, 5)

        box.Add(wx.StaticText(self, -1, "Project Settings"), 0, wx.CENTER | wx.ALL, 5)

        projSettingsBox = wx.BoxSizer(wx.HORIZONTAL)
        srBox = wx.BoxSizer(wx.VERTICAL)
        srText = wx.StaticText(self, -1, "Sample Rate")
        srBox.Add(srText, 0, wx.CENTER | wx.LEFT | wx.RIGHT, 5)
        self.pop_sr = wx.Choice(self, -1, choices = ['44100', '48000', '96000'])
        self.pop_sr.SetSelection(0)
        self.pop_sr.Bind(wx.EVT_CHOICE, self.handleSamplingRate)
        srBox.Add(self.pop_sr, 0, wx.TOP|wx.ALL, 2)
        chnlsBox = wx.BoxSizer(wx.VERTICAL)
        chnlsText = wx.StaticText(self, -1, "Channels")
        chnlsBox.Add(chnlsText, 0, wx.CENTER  | wx.LEFT | wx.RIGHT, 5)
        self.tx_chnls = wx.TextCtrl(self, -1, "2", size=(80, -1), style=wx.TE_PROCESS_ENTER)
        self.tx_chnls.Bind(wx.EVT_TEXT_ENTER, self.handleNchnls)
        chnlsBox.Add(self.tx_chnls, 0, wx.TOP|wx.ALL, 2)
        projSettingsBox.Add(srBox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        projSettingsBox.Add(chnlsBox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        box.Add(projSettingsBox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        box.Add(wx.StaticLine(self, size=(210, 1)), 0, wx.ALL, 5)
        
        soundBox = wx.BoxSizer(wx.HORIZONTAL)
        self.tog_audio = wx.ToggleButton(self, -1, "Start", size=(80,-1))
        self.tog_audio.SetFont(font)
        self.tog_audio.Disable()    
        soundBox.Add(self.tog_audio, 0, wx.CENTER |  wx.LEFT | wx.RIGHT, 5)
        box.Add(soundBox, 0, wx.CENTER | wx.ALL, 5)

        box.Add(wx.StaticLine(self, size=(210, 1)), 0, wx.ALL, 5)

        box.Add(wx.StaticText(self, -1, "Record Settings"), 0, wx.CENTER | wx.ALL, 5)

        recSettingsBox = wx.BoxSizer(wx.HORIZONTAL)
        fileformatBox = wx.BoxSizer(wx.VERTICAL)
        fileformatText = wx.StaticText(self, -1, "File Format")
        fileformatBox.Add(fileformatText, 0, wx.CENTER | wx.LEFT | wx.RIGHT, 5)
        self.pop_fileformat = wx.Choice(self, -1, choices = ['WAV', 'AIFF'], size=(80,-1))
        self.pop_fileformat.SetSelection(0)
        self.pop_fileformat.Bind(wx.EVT_CHOICE, self.handleFileFormat)
        fileformatBox.Add(self.pop_fileformat, 0, wx.TOP|wx.ALL, 2)
        sampletypeBox = wx.BoxSizer(wx.VERTICAL)
        sampletypeText = wx.StaticText(self, -1, "Sample Type")
        sampletypeBox.Add(sampletypeText, 0, wx.CENTER  | wx.LEFT | wx.RIGHT, 5)
        self.pop_sampletype = wx.Choice(self, -1, choices = ['16 int', '24 int', '32 int', '32 float'])
        self.pop_sampletype.SetSelection(0)
        self.pop_sampletype.Bind(wx.EVT_CHOICE, self.handleSampleType)
        sampletypeBox.Add(self.pop_sampletype, 0, wx.TOP|wx.ALL, 2)
        recSettingsBox.Add(fileformatBox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        recSettingsBox.Add(sampletypeBox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        box.Add(recSettingsBox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        recBox = wx.BoxSizer(wx.HORIZONTAL)
        self.tx_output = wx.TextCtrl( self, -1, "snd", size=(120, -1))
        recBox.Add(self.tx_output, 0, wx.LEFT | wx.RIGHT, 10)
        self.tog_record = wx.ToggleButton(self, -1, "Start", size=(50,-1))
        self.tog_record.SetFont(font)
        self.tog_record.Disable()
        recBox.Add(self.tog_record, 0, wx.ALIGN_CENTER)
        box.Add(recBox, 0, wx.ALL, 5)


        self.Bind(wx.EVT_CHOICE, self.handleType, self.trajType)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.handleClosed, self.closedToggle)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.handleAudio, self.tog_audio)
        self.tx_output.Bind(wx.EVT_CHAR, self.handleOutput)        
        self.Bind(wx.EVT_TOGGLEBUTTON, self.handleRecord, self.tog_record)

        self.SetAutoLayout(True)

        self.SetSizer(box)
        self.SetBestSize()
        self.SetupScrolling(scroll_x = False)

    def checkEnableWidgets(self):
        if self.type == 0:
            self.closedToggle.Enable()
        else:
            self.closedToggle.Disable()
        if self.type == 2:
            self.drawing.sl_period.Enable()
            self.drawing.sl_scaling.Enable()
        else:
            self.drawing.sl_period.Disable()
            self.drawing.sl_scaling.Disable()

    def handleType(self, event):
        self.type = event.GetInt()
        self.surface.setMode(self.type)
        self.checkEnableWidgets()

    def getType(self):
        return self.type

    def setType(self, type):
        self.trajType.SetSelection(type)
        self.type = type
        self.surface.setMode(type)
        self.checkEnableWidgets()

    def handleClosed(self, event):
        self.surface.setClosed(event.GetInt())

    def getClosed(self):
        return self.closedToggle.GetValue()

    def setClosed(self, closed):
        self.closedToggle.SetValue(closed)
        self.surface.setClosed(closed)

    def handleCutoff(self, val):
        for traj in self.surface.getAllTrajectories():
            traj.setFilterFreq(val)

    def getCutoff(self):
        return self.drawing.sl_cutoff.GetValue()

    def setCutoff(self, cutoff):
        self.drawing.sl_cutoff.SetValue(cutoff)
        for traj in self.surface.getAllTrajectories():
            traj.setFilterFreq(cutoff)

    def handleQ(self, val):
        for traj in self.surface.getAllTrajectories():
            traj.setFilterQ(val)

    def getQ(self):
        return self.drawing.sl_q.GetValue()

    def setQ(self, q):
        self.drawing.sl_q.SetValue(q)  
        for traj in self.surface.getAllTrajectories():
            traj.setFilterQ(q)
      
    def handlePeriod(self, val):
        self.surface.setOscilPeriod(val)

    def getPeriod(self):
        return self.surface.getOscilPeriod()

    def setPeriod(self, period):
        self.drawing.sl_period.SetValue(period)
        self.surface.setOscilPeriod(period)

    def handleScaling(self, val):
        self.surface.setOscilScaling(val)

    def getScaling(self):
        return self.surface.getOscilScaling()

    def setScaling(self, scaling):
        self.drawing.sl_scaling.SetValue(scaling)
        self.surface.setOscilScaling(scaling)

    def resetPlaybackSliders(self):
        selToMax = False
        if self.selected == MAX_STREAMS:
            self.selected = 0
            selToMax = True
        timeSpeed = self.surface.getTrajectory(self.selected).getTimeSpeed()
        self.setTimerSpeed(timeSpeed)
        step = self.surface.getTrajectory(self.selected).getStep()
        self.setStep(step)
        amp = self.surface.getTrajectory(self.selected).getAmplitude()
        self.setTrajAmp(amp)
        if selToMax:
            self.selected = MAX_STREAMS

    def handleSelected(self, event):
        if event.GetInt() != self.selected:
            self.selected = event.GetInt()
            self.selectedOkToChange = False
            if self.selected == MAX_STREAMS:
                self.selectedOkToChange = False
            self.resetPlaybackSliders()
        
    def setSelected(self, selected):
        self.playback.tog_traj.SetSelection(selected)
        self.selected = selected
        self.surface.setSelectedById(selected)
        self.resetPlaybackSliders()

    def getSelected(self):
        return self.selected

    def handlePopupFocus(self, evt):
        self.selectedOkToChange = False
        evt.Skip()

    def handleTimerSpeed(self, val):
        if self.selectedOkToChange:
            if self.selected == MAX_STREAMS:
                for t in self.surface.getActiveTrajectories():
                    t.setTimeSpeed(val)
            else:
                self.surface.getTrajectory(self.selected).setTimeSpeed(val)
        else:
            self.selectedOkToChange = True

    def setTimerSpeed(self, timeSpeed):
        self.playback.sl_timespeed.SetValue(timeSpeed, self.selectedOkToChange)

    def sendTrajSpeed(self, which, speed):
        self.parent.sg_audio.setMetroTime(which, speed * 0.001)
              
    def handleStep(self, val):
        if self.selectedOkToChange:
            if self.selected == MAX_STREAMS:
                for t in self.surface.getActiveTrajectories():
                    t.setStep(val)
            else:
                self.surface.getTrajectory(self.selected).setStep(val)
        else:
            self.selectedOkToChange = True

    def setStep(self, step):
        self.playback.sl_step.SetValue(step, self.selectedOkToChange)

    def handleTrajAmp(self, val):
        val = pow(10.0, float(val) * 0.05)
        if self.selectedOkToChange:
            if self.selected == MAX_STREAMS:
                for t in self.surface.getActiveTrajectories():
                    t.setAmplitude(val)
                    self.parent.sg_audio.setTrajAmplitude(t.label-1, val)
            else:
                self.surface.getTrajectory(self.selected).setAmplitude(val)
                self.parent.sg_audio.setTrajAmplitude(self.selected, val)
        else:
            self.selectedOkToChange = True

    def setTrajAmp(self, val):
        if val <= 0.0:
            val = 0.0001
        self.playback.sl_amp.SetValue(20.0 * math.log10(val), self.selectedOkToChange)

    def handleAmp(self, val):
        self.amplitude = pow(10.0, float(val) * 0.05)
        self.sendAmp()

    def getAmp(self):
        return self.amplitude

    def setAmp(self, amp):
        if amp <= 0.0:
            amp = 0.0001
        self.sl_amp.SetValue(20.0 * math.log10(amp))
        self.amplitude = amp

    def sendAmp(self):
        self.parent.sg_audio.setGlobalAmp(self.amplitude)
            
    def handleLoad(self):
        dlg = wx.FileDialog(self, message="Choose a sound file",
                            defaultFile="",
                            wildcard="AIFF file |*.aif;*.aiff;*.aifc;*.AIF;*.AIFF;*.Aif;*.Aiff|" \
                                     "Wave file |*.wav;*.wave;*.WAV;*.WAVE;*.Wav;*.Wave",
                            style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            sndPath = dlg.GetPath()
            self.loadSound(sndPath)
        dlg.Destroy()

    def loadSound(self, sndPath, force=False):
        if sndPath:
            if os.path.isfile(sndPath):
                self.sndPath = sndPath.encode(ENCODING)
                self.parent.sg_audio.loadSnd(self.sndPath)
                chnls, samprate, dur = soundInfo(self.sndPath)
                self.sndDur = dur
                self.chnls = chnls
                self.sndInfoStr = u'Loaded sound: %s,    Sr: %s Hz,    Channels: %s,    Duration: %s sec' % (self.sndPath.decode(ENCODING), samprate, chnls, dur)
                if self.parent.draw:
                    if not self.sndPath in self.surface.bitmapDict.keys() or force:
                        self.parent.log("Drawing waveform...")
                        self.surface.analyse(self.sndPath)
                    else:
                        self.surface.list = self.surface.bitmapDict[self.sndPath]
                        self.surface.create_bitmap()
                self.logSndInfo()
            elif os.path.isfile(os.path.join(self.parent.currentPath, os.path.split(sndPath)[1])):
                self.loadSound(os.path.join(self.parent.currentPath, os.path.split(sndPath)[1]), force)
            elif ":\\" in sndPath:
                # Handle windows path...
                self.loadSound(os.path.join(self.parent.currentPath, sndPath.split("\\")[-1]), force)
            else:
                self.parent.log('Sound file "%s" does not exist!' % sndPath)        

    def drawWaveform(self):
        if self.surface.sndBitmap and self.parent.draw:
            self.surface.create_bitmap()

    def getNchnls(self):
        return self.nchnls
        
    def setNchnls(self, x):
        if x != self.nchnls:
            self.nchnls = x
            self.tx_chnls.SetValue(str(x))
            self.meter.setNumSliders(self.nchnls)
            self.shutdownServer()
            self.bootServer()
            
    def handleNchnls(self, event):
        x = int(self.tx_chnls.GetValue())
        if x != self.nchnls:
            self.nchnls = x
            self.meter.setNumSliders(self.nchnls)
            self.shutdownServer()
            self.bootServer()

    def getSamplingRate(self):
        return self.samplingRate

    def setSamplingRate(self, x):
        SR = {44100: 0, 48000: 1, 96000: 2}
        if x != self.samplingRate:
            self.samplingRate = x
            self.pop_sr.SetValue(SR[self.samplingRate])
            self.shutdownServer()
            self.bootServer()

    def handleSamplingRate(self, event):
        SR = {0: 44100, 1: 48000, 2: 96000}
        x = SR[event.GetInt()]
        if x != self.samplingRate:
            self.samplingRate = x
            self.shutdownServer()
            self.bootServer()

    def getFileFormat(self):
        return self.fileformat

    def setFileFormat(self, x):
        self.fileformat = x
        self.pop_fileformat.SetSelection(self.fileformat)

    def handleFileFormat(self, event):
        self.fileformat = event.GetInt()

    def getSampleType(self):
        return self.sampletype

    def setSampleType(self, x):
        self.sampletype = x
        self.pop_sampletype.SetSelection(self.sampletype)

    def handleSampleType(self, event):
        self.sampletype = event.GetInt()

    def bootServer(self):
        self.parent.sg_audio.boot(self.parent.audioDriver, self.nchnls, self.samplingRate, self.midiInterface)
        self.tog_audio.Enable()    
        if self.sndPath != None:
            self.loadSound(self.sndPath)
        if self.tempState != None:
            self.parent.setState(self.tempState)
            self.tempState = None

    def shutdownServer(self):
        self.tempState = self.parent.getState()
        self.parent.sg_audio.shutdown()
        self.tog_audio.Disable()  
        self.surface.Refresh()  
            
    def handleAudio(self, event):
        if event.GetInt() == 1:
            if not self.sndPath:
                self.parent.log('*** No sound loaded! ***')
                self.tog_audio.SetValue(0)
                self.parent.menu.Check(7, False)
            else:  
                self.tx_chnls.Disable()
                self.tx_chnls.SetBackgroundColour("#EEEEEE")
                self.pop_sr.Disable()
                self.parent.enableDrivers(False)
                self.parent.midiSettings.popupInterface.Disable()
                self.tog_audio.SetLabel('Stop')
                self.tog_audio.SetValue(1)
                self.parent.menu.Check(7, True)
                self.tog_record.Enable()

                for t in self.surface.getAllTrajectories():
                    t.initCounter()
                self.parent.sg_audio.start()
        else:    
            self.tx_chnls.Enable()
            self.tx_chnls.SetBackgroundColour("#FFFFFF")
            self.pop_sr.Enable()
            self.parent.enableDrivers(True)
            self.parent.midiSettings.popupInterface.Enable()
            self.tog_audio.SetLabel('Start')
            self.tog_audio.SetValue(0)
            self.parent.menu.Check(7, False)
            self.tog_record.SetValue(0)
            self.tog_record.SetLabel('Start')
            self.tog_record.Disable()
            self.parent.sg_audio.stop()

    def handleOutput(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_TAB or key == wx.WXK_RETURN:
            self.surface.SetFocus()
        event.Skip()
                
    def handleRecord(self, event):
        if event.GetInt() == 1:
            filename = self.tx_output.GetValue()
            self.parent.sg_audio.recStart(filename, self.fileformat, self.sampletype)
            self.tog_record.SetLabel('Stop')
        else:
            self.tog_record.SetLabel('Start')
            self.parent.sg_audio.recStop()

    def logSndInfo(self):
        self.parent.log(self.sndInfoStr)

class DrawingParameters(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.SetBackgroundColour(BACKGROUND_COLOUR)
        self.parent = parent
        box = wx.BoxSizer(wx.VERTICAL)

        lpcutText = wx.StaticText(self, -1, "Lowpass cutoff", size=(195,15))
        font, psize = lpcutText.GetFont(), lpcutText.GetFont().GetPointSize()
        if sys.platform == "win32":
            font.SetPointSize(psize-1)
        else:
            font.SetPointSize(psize-2)
        box.Add(lpcutText, 0, wx.LEFT|wx.TOP, 5)
        cutoffBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_cutoff = ControlSlider(self, 100, 15000, 5000, size=(195, 16), integer=True, log=True, outFunction=self.parent.GetParent().handleCutoff)
        cutoffBox.Add(self.sl_cutoff)
        box.Add(cutoffBox, 0, wx.LEFT | wx.RIGHT, 5)
        box.AddSpacer(5)

        lpqText = wx.StaticText(self, -1, "Lowpass Q", size=(195,15))
        box.Add(lpqText, 0, wx.LEFT, 5)
        qBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_q = ControlSlider(self, 0.5, 1000, 0.5, size=(195, 16), outFunction=self.parent.GetParent().handleQ)
        qBox.Add(self.sl_q)
        box.Add(qBox, 0, wx.LEFT | wx.RIGHT, 5)
        box.AddSpacer(5)
        
        oscpText = wx.StaticText(self, -1, "Oscil period", size=(195,15))
        box.Add(oscpText, 0, wx.LEFT, 5)
        periodBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_period = ControlSlider(self, 0, 5, 2, size=(195, 16), outFunction=self.parent.GetParent().handlePeriod)
        periodBox.Add(self.sl_period)
        self.sl_period.Disable()
        box.Add(periodBox, 0, wx.LEFT | wx.RIGHT, 5)
        box.AddSpacer(5)

        oscsclText = wx.StaticText(self, -1, "Oscil scaling", size=(195,15))
        box.Add(oscsclText, 0, wx.LEFT, 5)
        scalingBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_scaling = ControlSlider(self, 0, 4, 1, size=(195, 16), outFunction=self.parent.GetParent().handleScaling)
        scalingBox.Add(self.sl_scaling)
        self.sl_scaling.Disable()
        box.Add(scalingBox, 0, wx.LEFT | wx.RIGHT, 5)                   
        box.AddSpacer(5)

        for obj in [lpcutText, lpqText, oscpText, oscsclText]:
            obj.SetFont(font)

        self.SetAutoLayout(True)
        self.SetSizer(box)

class PlaybackParameters(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.SetBackgroundColour(BACKGROUND_COLOUR)
        self.parent = parent
        box = wx.BoxSizer(wx.VERTICAL)

        seltrajText = wx.StaticText(self, -1, "Selected trajectory")
        font, psize = seltrajText.GetFont(), seltrajText.GetFont().GetPointSize()
        if sys.platform == "win32":
            font.SetPointSize(psize-1)
        else:
            font.SetPointSize(psize-2)
        box.Add(seltrajText, 0, wx.CENTER | wx.TOP | wx.BOTTOM, 2)

        trajChoices = [str(i+1) for i in range(MAX_STREAMS)]
        trajChoices.append("all")
        self.tog_traj = wx.Choice(self, -1, choices=trajChoices)
        self.tog_traj.SetSelection(0)
        self.tog_traj.Bind(wx.EVT_CHOICE, self.parent.GetParent().handleSelected)
        self.tog_traj.Bind(wx.EVT_LEFT_DOWN, self.parent.GetParent().handlePopupFocus)
        box.Add(self.tog_traj, 0, wx.CENTER, 5)
        box.AddSpacer(5)

        spdText = wx.StaticText(self, -1, "Timer speed", size=(195,15))
        box.Add(spdText, 0, wx.LEFT, 5)
        timespeedBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_timespeed = ControlSlider(self, 5, 1000, 25, size=(195, 16), log=True, outFunction=self.parent.GetParent().handleTimerSpeed)
        timespeedBox.Add(self.sl_timespeed)
        box.Add(timespeedBox, 0, wx.LEFT | wx.RIGHT, 5)
        box.AddSpacer(5)
        
        ptstepText = wx.StaticText(self, -1, "Point step", size=(195,15))
        box.Add(ptstepText, 0, wx.LEFT, 5)
        stepBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_step = ControlSlider(self, 1, 100, 1, size=(195, 16), integer=True, outFunction=self.parent.GetParent().handleStep)
        stepBox.Add(self.sl_step)
        box.Add(stepBox, 0, wx.LEFT | wx.RIGHT, 5)
        box.AddSpacer(5)

        ampText = wx.StaticText(self, -1, "Amplitude (dB)", size=(195,15))
        box.Add(ampText, 0, wx.LEFT, 5)
        ampBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_amp = ControlSlider(self, -60, 18, 0, size=(195, 16), integer=False, outFunction=self.parent.GetParent().handleTrajAmp)
        ampBox.Add(self.sl_amp)
        box.Add(ampBox, 0, wx.LEFT | wx.RIGHT, 5)

        for obj in [seltrajText, self.tog_traj, spdText, ptstepText, ampText]:
            obj.SetFont(font)

        self.SetAutoLayout(True)
        self.SetSizer(box)

class EnvelopeFrame(wx.Frame):
    def __init__(self, parent, size=(600, 300)):
        wx.Frame.__init__(self, parent, -1, "Envelope Shape", size=size)
        self.parent = parent
        self.env = None
        menuBar = wx.MenuBar()
        self.menu = wx.Menu()
        self.menu.Append(200, 'Close\tCtrl+W', "")
        menuBar.Append(self.menu, "&File")
        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_CLOSE, self.handleClose)
        self.Bind(wx.EVT_MENU, self.handleClose, id=200)

        self.graph = Grapher(self, init=[(0.0,0),(0.3,1),(0.7,1),(1.0,0)], mode=1)

        self.Show(False)

    def setEnv(self, env):
        self.env = env
        self.env.replace(self.graph.getValues())
        self.graph.outFunction = self.env.replace

    def handleClose(self, event):
        self.Show(False)

    def save(self):
        return {'envelope': self.graph.getPoints()}

    def load(self, dict):
        self.graph.setInitPoints(dict.get('envelope', [(0.0,0),(0.3,1),(0.7,1),(1.0,0)]))
        if self.env != None:
            self.env.replace(self.graph.getValues())

class MainFrame(wx.Frame):
    def __init__(self, parent, id, pos, size, file):
        wx.Frame.__init__(self, parent, id, "", pos, size)
        self.SetMinSize((600,300))

        self.currentFile = None
        self.currentPath = None
        self.temps = []
        self.draw = True
        self.lowpass = True
        self.fillPoints = True
        self.editionLevels = [2, 4, 8, 12, 16, 24, 32, 50]
        self.editionLevel = 2
        self.audioDriver = None
        self.recall = self.undos = 0

        self.status = wx.StatusBar(self, -1)
        self.SetStatusBar(self.status)

        self.menuBar = wx.MenuBar()
        self.menu = wx.Menu()
        self.menu.Append(11, "New...\tCtrl+N")
        self.Bind(wx.EVT_MENU, self.handleNew, id=11)
        self.menu.Append(1, "Open...\tCtrl+O")
        self.Bind(wx.EVT_MENU, self.handleOpen, id=1)
        self.menu.Append(2, "Open Soundfile...\tShift+Ctrl+O")
        self.Bind(wx.EVT_MENU, self.handleLoad, id=2)
        self.menu.Append(3, "Save\tCtrl+S")
        self.Bind(wx.EVT_MENU, self.handleSave, id=3)
        self.menu.Append(4, "Save as...\tShift+Ctrl+S")
        self.Bind(wx.EVT_MENU, self.handleSaveAs, id=4)
        self.menu.AppendSeparator()
        self.menu.Append(6, "Open FX Window\tCtrl+P")
        self.Bind(wx.EVT_MENU, self.openFxWindow, id=6)
        self.menu.Append(5, "Open Envelope Window\tCtrl+E")
        self.Bind(wx.EVT_MENU, self.openEnvelopeWindow, id=5)
        self.menu.AppendSeparator()
        self.menu.Append(7, "Run\tCtrl+R", "", wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.onRun, id=7)
        self.menu.AppendSeparator()
        quit_item = self.menu.Append(8, "Quit\tCtrl+Q")  
        self.Bind(wx.EVT_MENU, self.OnClose, id=8)
        self.menuBar.Append(self.menu, "&File")

        if wx.Platform=="__WXMAC__":
            wx.App.SetMacExitMenuItemId(quit_item.GetId())

        self.menu1 = wx.Menu()
        self.menu1.Append(110, "Undo\tCtrl+Z", "")
        self.menu1.Enable(110, False)
        self.Bind(wx.EVT_MENU, self.handleUndo, id=110)
        self.menu1.Append(111, "Redo\tShift+Ctrl+Z", "")
        self.menu1.Enable(111, False)
        self.Bind(wx.EVT_MENU, self.handleUndo, id=111)
        self.menu1.InsertSeparator(2)
        self.menu1.Append(100, "Draw Waveform", "", wx.ITEM_CHECK)
        self.menu1.Check(100, True)
        self.Bind(wx.EVT_MENU, self.handleDrawWave, id=100)
        self.menu1.Append(101, "Activate Lowpass filter", "", wx.ITEM_CHECK)
        self.menu1.Check(101, True)
        self.Bind(wx.EVT_MENU, self.handleActivateLp, id=101)
        self.menu1.Append(102, "Fill points", "", wx.ITEM_CHECK)
        self.menu1.Check(102, True)
        self.Bind(wx.EVT_MENU, self.handleActivateFill, id=102)
        self.submenu1 = wx.Menu()
        for i, level in enumerate(self.editionLevels):
            menuId = 1000 + i
            self.submenu1.Append(menuId, str(level), "", wx.ITEM_RADIO)
            self.Bind(wx.EVT_MENU, self.handlesEditionLevels, id=menuId)
        self.menu1.AppendMenu(999, "Edition levels", self.submenu1)
        self.menu1.InsertSeparator(7)
        self.menu1.Append(103, "Reinit counters\tCtrl+T", "")
        self.Bind(wx.EVT_MENU, self.handleReinit, id=103)
        self.menuBar.Append(self.menu1, "&Drawing")

        self.menu2 = wx.Menu()
        self.menuBar.Append(self.menu2, "&Audio Drivers")

        self.menu3 = wx.Menu()
        self.menu3.Append(204, "Memorize Trajectory\tShift+Ctrl+M", "")
        self.Bind(wx.EVT_MENU, self.handleMemorize, id=204)
        self.menu3.Append(2005, "Midi Settings...\tShift+Alt+Ctrl+M", "")
        self.Bind(wx.EVT_MENU, self.showMidiSettings, id=2005)
        self.menuBar.Append(self.menu3, "&Midi")

        self.menu4 = wx.Menu()
        self.menu4.Append(400, "Add Reverb ball\tCtrl+1", "")
        self.menu4.Append(401, "Add Delay ball\tCtrl+2", "")
        self.menu4.Append(402, "Add Disto ball\tCtrl+3", "")
        self.menu4.Append(403, "Add Waveguide ball\tCtrl+4", "")
        self.menu4.Append(404, "Add RingMod ball\tCtrl+5", "")
        self.menu4.Append(405, "Add Degrade ball\tCtrl+6", "")
        self.menu4.Append(406, "Add Harmonizer ball\tCtrl+7", "")
        for i in range(7):
            self.Bind(wx.EVT_MENU, self.addFxBall, id=400+i)
        self.menuBar.Append(self.menu4, "&FxBall")

        menu5 = wx.Menu()
        helpItem = menu5.Append(500, '&About %s %s' % (NAME, SG_VERSION), 'wxPython RULES!!!')
        wx.App.SetMacAboutMenuItemId(helpItem.GetId())
        self.Bind(wx.EVT_MENU, self.showAbout, helpItem)
        commands = menu5.Append(501, "Opens SoundGrain commands page")
        self.Bind(wx.EVT_MENU, self.openCommandsPage, commands)
        self.menuBar.Append(menu5, '&Help')

        self.SetMenuBar(self.menuBar)

        preffile = os.path.join(os.path.expanduser("~"), ".soundgrain-init")
        if os.path.isfile(preffile):
            with open(preffile, "r") as f:
                lines = f.readlines()
                auDriver = lines[0].split("=")[1].replace("\n", "")
                miDriver = lines[1].split("=")[1].replace("\n", "")
        else:
            auDriver = None
            miDriver = None

        mainBox = wx.BoxSizer(wx.HORIZONTAL)
        self.panel = DrawingSurface(self)
        self.controls = ControlPanel(self, self.panel)
        mainBox.Add(self.panel, 20, wx.EXPAND, 5)
        mainBox.Add(self.controls, 0, wx.EXPAND, 5)
        self.SetSizer(mainBox)
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.SetTitle('Granulator')
        self.envelopeFrame = EnvelopeFrame(self)
        self.sg_audio = SG_Audio(self.panel.clock, self.panel.Refresh, self.controls, self.panel.addTrajFromMemory,
                                 self.panel.deleteMemorizedTraj, self.envelopeFrame)
        self.granulatorControls = GranulatorFrame(self, self.panel, self.sg_audio)
        self.midiSettings = MidiSettings(self, self.panel, self.sg_audio, miDriver)
        self.createInitTempFile()

        self.Show()
        self.check(auDriver)
        
        if file:
            wx.CallAfter(self.loadFile, file)

    def onRun(self, event):
        self.controls.handleAudio(event)
        
    def check(self, pref=None):
        self.status.SetStatusText('Scanning audio drivers...')
        self.driversList, self.driverIndexes, selected = checkForDrivers()
        if pref == None:
            self.audioDriver = selected
        else:
            if pref in self.driversList:
                self.audioDriver = self.driverIndexes[self.driversList.index(pref)]
            else:
                self.audioDriver = selected
        
        for i, driver in enumerate(self.driversList):
            menuId = 200 + i
            self.menu2.Append(menuId, driver.decode(ENCODING), "", wx.ITEM_RADIO)
            self.Bind(wx.EVT_MENU, self.handleDriver, id=menuId)
            if driver == self.driversList[self.driverIndexes.index(self.audioDriver)]:
                self.menu2.Check(menuId, True)
        self.status.SetStatusText('Audio drivers loaded')
        self.controls.bootServer()

    def showMidiSettings(self, evt):
        self.midiSettings.show()

    def enableDrivers(self, state):
        for i in range(len(self.driversList)):
            self.menu2.FindItemById(200+i).Enable(state)
            
    def handleReinit(self, evt):
        for t in self.panel.getAllTrajectories():
            t.initCounter()

    def addFxBall(self, evt):
        self.panel.addFxBall(evt.GetId() - 400)

    def handleMemorize(self, evt):
        self.panel.Memorize()

    def handleDrawWave(self, evt):
        self.draw = self.menu1.IsChecked(100)
        self.drawing()

    def setDraw(self, state):
        self.menu1.Check(100, state)
        self.draw = state

    def drawing(self):
        if not self.draw:
            self.panel.sndBitmap = None
        else:
            if self.controls.sndPath:
                if self.controls.sndPath in self.panel.bitmapDict:
                    self.panel.list = self.panel.bitmapDict[self.controls.sndPath]
                    self.panel.create_bitmap()
                else:
                    self.panel.analyse(self.controls.sndPath)

    def handleActivateLp(self, evt):
        self.lowpass = self.menu1.IsChecked(101)
        self.checkLowpass()

    def setLowpass(self, state):
        self.menu1.Check(101, state)
        self.lowpass = state
        self.checkLowpass()

    def checkLowpass(self):
        for t in self.panel.getAllTrajectories():
            t.activateLp(self.lowpass)
        if self.lowpass:
            self.controls.drawing.sl_cutoff.Enable()
            self.controls.drawing.sl_q.Enable()
        else:
            self.controls.drawing.sl_cutoff.Disable()
            self.controls.drawing.sl_q.Disable()

    def handleActivateFill(self, evt):
        self.fillPoints = self.menu1.IsChecked(102)

    def setFillPoints(self, state):
        self.menu1.Check(102, state)
        self.fillPoints = state

    def handlesEditionLevels(self, evt):
        menuId = evt.GetId()
        self.editionLevel = self.editionLevels[menuId - 1000]
        self.pushEditionLevel()

    def setEditionLevel(self, level):
        self.submenu1.Check(self.editionLevels.index(level)+1000, True)
        self.editionLevel = level
        self.pushEditionLevel()

    def pushEditionLevel(self):
        for t in self.panel.getAllTrajectories():
            t.setEditionLevel(self.editionLevel)

    def handleDriver(self, evt):
        menuId = evt.GetId()
        self.audioDriver = self.driverIndexes[menuId - 200]
        self.controls.shutdownServer()
        self.controls.bootServer()
        
    def openFxWindow(self, evt):
        if self.granulatorControls.IsShown():
            self.granulatorControls.Hide()
        else:
            self.granulatorControls.SetTitle('Granulator controls')
            self.granulatorControls.Show()

    def openEnvelopeWindow(self, evt):
        if self.envelopeFrame.IsShown():
            self.envelopeFrame.Hide()
        else:
            self.envelopeFrame.Show()

    def handleUndo(self, evt):
        self.recallTempFile(evt.GetId())

    def handleNew(self, evt):
        self.panel.sndBitmap = None
        self.loadFile(os.path.join(RESOURCES_PATH, 'new_soundgrain_file.sg'))
        
    def handleOpen(self, evt):
        dlg = wx.FileDialog(self, message="Open SoundGrain file...",
                            defaultFile="",
                            wildcard="SoundGrain file (*.sg)|*.sg",
                            style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.loadFile(path)
        dlg.Destroy()

    def handleLoad(self, evt):
        self.controls.handleLoad()
        
    def handleSave(self, evt):
        if self.currentFile:
            self.saveFile(self.currentFile)
        else:
            self.handleSaveAs(None)

    def handleSaveAs(self, evt):
        dlg = wx.FileDialog(self, message="Save file as ...", 
                            defaultFile="Granulator.sg", 
                            style=wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if os.path.isfile(path):
                dlg2 = wx.MessageDialog(self,
                      '"%s" already exists. Do you want to replace it?' % os.path.split(path)[1],
                      'Warning!', wx.OK | wx.ICON_INFORMATION | wx.CANCEL)
                if dlg2.ShowModal() == wx.ID_OK:
                    dlg2.Destroy()
                    self.saveFile(path)
                    dlg.Destroy()
                else:
                    dlg2.Destroy()
                    dlg.Destroy()
                    self.handleSaveAs(None)
            else:
                self.saveFile(path)
                dlg.Destroy()

    def getState(self):
        saveDict = {}
        ### Main Frame ###
        saveDict['version'] = SG_VERSION
        saveDict['platform'] = PLATFORM
        saveDict['MainFrame'] = {}
        saveDict['MainFrame']['draw'] = self.draw
        saveDict['MainFrame']['lowpass'] = self.lowpass
        saveDict['MainFrame']['fillPoints'] = self.fillPoints
        saveDict['MainFrame']['editionLevel'] = self.editionLevel
        saveDict['MainFrame']['size'] = self.GetSizeTuple()
        ### Surface Panel ###
        saveDict["SurfaceSize"] = self.panel.GetSizeTuple()
        ### Controls Frame ###
        saveDict['ControlFrame'] = self.granulatorControls.save()
        ### Midi Frame ###
        saveDict['MidiSettings'] = self.midiSettings.save()
        ### Control Panel ###
        saveDict['ControlPanel'] = {}
        saveDict['ControlPanel']['type'] = self.controls.getType()
        saveDict['ControlPanel']['closed'] = self.controls.getClosed()
        saveDict['ControlPanel']['cutoff'] = self.controls.getCutoff()
        saveDict['ControlPanel']['q'] = self.controls.getQ()
        saveDict['ControlPanel']['period'] = self.controls.getPeriod()
        saveDict['ControlPanel']['scaling'] = self.controls.getScaling()
        saveDict['ControlPanel']['globalamp'] = self.controls.getAmp()
        saveDict['ControlPanel']['nchnls'] = self.controls.getNchnls()
        saveDict['ControlPanel']['sr'] = self.controls.getSamplingRate()
        saveDict['ControlPanel']['fileformat'] = self.controls.getFileFormat()
        saveDict['ControlPanel']['sampletype'] = self.controls.getSampleType()
        saveDict['ControlPanel']['sound'] = self.controls.sndPath
        ### Trajectories ###
        saveDict['Trajectories'] = {}
        for i, t in enumerate(self.panel.getAllTrajectories()):
            saveDict['Trajectories'][str(i)] = t.getAttributes()
        saveDict['MemorizedTrajectory'] = self.panel.memorizedTrajectory.getAttributes()
        ### Grain Envelope ###
        saveDict['Envelope'] = self.envelopeFrame.save()
        ### Fx Balls ###
        saveDict['fxballs'] = {}
        for key, value in self.panel.fxballs.items():
            saveDict['fxballs'][str(key)] = value.save()
        return saveDict
        
    def saveFile(self, path):
        self.currentFile = path
        self.currentPath = os.path.split(path)[0]
        saveDict = self.getState()   
        msg = xmlrpclib.dumps((saveDict, ), allow_none=True)
        f = open(path, 'w')
        f.write(msg)
        f.close()
        self.SetTitle(os.path.split(self.currentFile)[1])

    def setState(self, dict):
        version = dict.get('version', '3.0')
        platform = dict.get('platform', 'darwin')
        ### Surface panel ###
        surfaceSize = dict.get('SurfaceSize', None)
        if surfaceSize != None:
            self.panel.SetSize(surfaceSize)
        ### Main Frame ###
        self.setDraw(dict['MainFrame']['draw'])
        self.setLowpass(dict['MainFrame']['lowpass'])
        self.setFillPoints(dict['MainFrame']['fillPoints'])
        self.setEditionLevel(dict['MainFrame']['editionLevel'])
        size = dict['MainFrame']['size']
        if platform == 'darwin':
            if sys.platform == 'darwin':
                self.SetSize(size)
            elif sys.platform == "win32":
                self.SetSize((size[0]+10, size[1]+38))
            else:
                self.SetSize((size[0]+3, size[1]+13))
        elif platform == "win32":
            if sys.platform == 'darwin':
                self.SetSize((size[0]-10, size[1]-38))
            elif sys.platform == "win32":
                self.SetSize(size)
            else:
                self.SetSize((size[0]-7, size[1]-25))
        else:
            if sys.platform == 'darwin':
                self.SetSize((size[0]-3, size[1]-13))
            elif sys.platform == "win32":
                self.SetSize((size[0]+7, size[1]+25))
            else:
                self.SetSize(size)
        ### Control Frame ###
        self.granulatorControls.load(dict['ControlFrame'])
        ### Midi Frame ###
        self.midiSettings.load(dict.get("MidiSettings", None))
        ### Control panel ###
        self.controls.setType(dict['ControlPanel']['type'])
        self.controls.setClosed(dict['ControlPanel']['closed'])
        self.controls.setCutoff(dict['ControlPanel']['cutoff'])
        self.controls.setQ(dict['ControlPanel']['q'])
        self.controls.setPeriod(dict['ControlPanel']['period'])
        self.controls.setScaling(dict['ControlPanel']['scaling'])
        self.controls.setAmp(dict['ControlPanel']['globalamp'])
        self.controls.setNchnls(dict['ControlPanel'].get('nchnls', "2"))
        self.controls.setSamplingRate(dict['ControlPanel'].get('sr', 44100))
        self.controls.setFileFormat(dict['ControlPanel'].get('fileformat', 0))
        self.controls.setSampleType(dict['ControlPanel'].get('sampletype', 0))
        self.controls.loadSound(dict['ControlPanel']['sound'])
        ### Trajectories ###
        for i, t in enumerate(self.panel.getAllTrajectories()):
            t.setAttributes(dict['Trajectories'][str(i)])
        if dict.has_key('MemorizedTrajectory'):
            self.panel.memorizedTrajectory.setAttributes(dict['MemorizedTrajectory'])
        ### Grain Envelope ###
        if dict.has_key("Envelope"):
            self.envelopeFrame.load(dict["Envelope"])
        if dict.has_key('fxballs'):
            self.panel.restoreFxBalls(dict["fxballs"])

    def loadFile(self, path):
        if self.midiSettings.IsShown():
            self.midiSettings.Hide()
        self.panel.removeAllFxBalls()
        f = open(path, 'r')
        msg = f.read()
        f.close()
        result, method = xmlrpclib.loads(msg)
        dict = result[0]
        if 'new_soundgrain_file.sg' in path:
            self.currentFile = None
            self.currentPath = None
            title = "Granulator"
            self.status.SetStatusText("")
        else:
            self.currentFile = path
            self.currentPath = os.path.split(path)[0]
            title = os.path.split(self.currentFile)[1]
        self.panel.trajectories = [Trajectory(self.panel, i+1) for i in range(MAX_STREAMS)]
        self.panel.memorizedTrajectory = Trajectory(self.panel, -1)
        self.panel.memorizedId = {}
        self.controls.setSelected(0)
        self.setState(dict)
        self.SetTitle(title)
        self.panel.needBitmap = True
        wx.CallAfter(self.panel.Refresh)

    def createInitTempFile(self):
        d = {}
        for i, t in enumerate(self.panel.getAllTrajectories()):
            d[i] = str(t.getAttributes())
        self.temps.insert(0, d)

    def createTempFile(self):
        d = {}
        for i, t in enumerate(self.panel.getAllTrajectories()):
            d[i] = str(t.getAttributes())
        self.temps.insert(0, d)
        self.recall = self.undos = 0
        self.menu1.Enable(110, True)
        self.menu1.Enable(111, False)

    def recallTempFile(self, id):
        if self.temps and self.recall < len(self.temps):
            if id == 110: 
                self.recall += 1
                self.undos += 1
            else: 
                self.recall -= 1
                self.undos -= 1
            d = self.temps[self.recall]
            for i, t in enumerate(self.panel.getAllTrajectories()):
                t.setAttributes(eval(d[i]))
            self.panel.needBitmap = True
            self.Refresh()    
        if self.recall >= len(self.temps) - 1:
            self.menu1.Enable(110, False)
        else:
            self.menu1.Enable(110, True)
        if self.undos == 0:
            self.menu1.Enable(111, False)
        else:
            self.menu1.Enable(111, True) 

    def OnClose(self, evt):
        auDriver = self.driversList[self.driverIndexes.index(self.audioDriver)]
        miDriver = self.midiSettings.getInterface()
        with open(os.path.join(os.path.expanduser("~"), ".soundgrain-init"), "w") as f:
            f.write("audioDriver=%s\n" % auDriver)
            f.write("midiDriver=%s\n" % miDriver)
        if self.granulatorControls.IsShown():
            self.granulatorControls.Hide()
        self.controls.meter.OnClose(evt)
        self.sg_audio.server.stop()
        self.controls.shutdownServer()
        self.Destroy()
        sys.exit()

    def log(self, text):
        self.status.SetStatusText(text)

    def openCommandsPage(self, event):
        f = os.path.join(RESOURCES_PATH, "commands.pdf")
        if sys.platform == 'win32':
            os.startfile(f)
        else:
            os.system('open %s' % f)

    def showAbout(self, evt):
        info = wx.AboutDialogInfo()

        description = wordwrap(
"Sound Grain is a graphical interface where " 
"users can draw and edit trajectories to " 
"control granular sound synthesis.\n"

"Sound Grain is written with Python and " 
"WxPython and uses pyo as its audio engine.",350, wx.ClientDC(self))

        licence = wordwrap(
"SoundGrain is free software: you can "
"redistribute it and/or modify it under "
"the terms of the GNU General Public "
"License as published by the Free Software " 
"Foundation, either version 3 of the License, " 
"or (at your option) any later version.\n"

"SoundGrain is distributed in the hope that "
"it will be useful, but WITHOUT ANY WARRANTY; "
"without even the implied warranty of "
"MERCHANTABILITY or FITNESS FOR A PARTICULAR "
"PURPOSE. See the GNU General Public License "
"for more details.", 350, wx.ClientDC(self)) 

        info.SetIcon(wx.Icon(os.path.join(IMAGES_PATH, 'SoundGrain.png'), wx.BITMAP_TYPE_PNG))
        info.SetName('Sound Grain')
        info.SetVersion('%s' % SG_VERSION)
        info.SetDescription(description)
        info.SetCopyright('(C) 2009 Olivier Belanger')
        info.SetWebSite('http://code.google.com/p/soundgrain')
        info.SetLicence(licence)
        wx.AboutBox(info)

class SoundGrainApp(wx.PySimpleApp):
    def __init__(self, *args, **kwargs):
        wx.PySimpleApp.__init__(self, *args, **kwargs)
        self.loadFile = None
    
    def setLoadFileFunc(self, func):
        self.loadFile = func
            
    def MacOpenFile(self, filename):
        self.loadFile(filename)
              
if __name__ == '__main__': 

    file = None
    if len(sys.argv) > 1:
        file = sys.argv[1]

    app = SoundGrainApp()
    X,Y = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X), wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
    if X < 900: sizex = X - 40
    else: sizex = 900
    if PLATFORM in ['win32', 'linux2']: defaultY = 670
    else: defaultY = 650
    if Y < defaultY: sizey = Y - 40
    else: sizey = defaultY
    f = MainFrame(None, -1, pos=(20,20), size=(sizex,sizey), file=file)
    app.setLoadFileFunc(f.loadFile)
    app.MainLoop()
