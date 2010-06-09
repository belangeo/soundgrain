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

from math import sin, pi, sqrt
import os, sys, time, tempfile, xmlrpclib
import wx
from wx.lib.wordwrap import wordwrap
import  wx.lib.scrolledpanel as scrolled

from Resources.constants import *
from Resources.audio import *
from Resources.Biquad_Filter import BiquadLP
from Resources.Modules import *
from Resources.Meter import VuMeter
from Resources.Slider import ControlSlider

trajTypes = {0: 'free', 1: 'circle', 2: 'oscil', 3: 'line'}

def mapper(input, inmin=0, inmax=127, outmin=0, outmax=1, met=0):
    """Maps input values inside inmin - inmax range according to output range outmin - outmax.

input : Incoming value (must be in the range inmin et inmax).
inmin : Minimum input value.
inmax : Maximum input value.
outmin : Minimum value of the resultant scale operation.
outmax : Maximum value of the resultant scale operation.
met : 0 = linear, 1 = log, 2 = sqrt
"""    
    inrev = False
    outrev = False
    if inmin > inmax:
        inmin, inmax = inmax, inmin
        inrev = True
    if input < inmin: input = inmin
    if input > inmax: input = inmax
    inRange = float(inmax - inmin)
    if inrev: firstscale = (inmax - input) / inRange
    else: firstscale = (input - inmin) / inRange

    if met == 1:
        firstscale = pow(firstscale,2)
    elif met == 2:
        firstscale = sqrt(firstscale)    
        
    if outmin > outmax:
        outmin, outmax = outmax, outmin
        outrev = True
    outRange = float(outmax - outmin)

    if outrev: val = outmax - (firstscale * outRange)
    else: val = firstscale * outRange + outmin
    return val

###########################

class Trajectory:
    def __init__(self, label, parent):
        self.parent = parent
        self.label = label
        self.activeLp = True
        self.editLevel = 2
        self.timeSpeed = 25
        self.type = None
        self.center = None
        self.radius = None
        self.active = False
        self.freeze = False
        self.initPoints = []
        self.points = []
        self.mario = 0
        self.lastCirclePos = (0,0)
        self.circlePos = None
        self.counter = 0
        self.filterCut = 5000
        self.step = 1
        self.lpx = BiquadLP()
        self.lpy = BiquadLP()

    def clear(self):
        self.type = None
        self.center = None
        self.radius = None
        self.setActive(False)
        self.initPoints = []
        self.points = []
        self.circlePos = None

    def getAttributes(self):
        return {'activeLp': self.activeLp, 
                'editLevel': self.editLevel, 
                'timeSpeed': self.timeSpeed,
                'step': self.step,
                'type': self.type, 
                'center': self.center, 
                'radius': self.radius, 
                'active': self.active, 
                'freeze': self.freeze,
                'circlePos': self.circlePos, 
                'counter': self.counter,
                'filterCut': self.filterCut,
                'points': self.getPoints()}

    def setAttributes(self, dict):
        self.activeLp = dict['activeLp']
        self.editLevel = dict['editLevel']
        self.setTimeSpeed(dict['timeSpeed'])
        self.step = dict['step']
        self.type = dict['type']
        self.center = dict['center']
        self.radius = dict['radius']
        self.setActive(dict['active'])
        self.freeze = dict['freeze']
        self.circlePos = dict['circlePos']
        self.counter = dict['counter']
        self.filterCut = dict['filterCut']
        self.setPoints(dict['points'])

    def getFreeze(self):
        return self.freeze

    def setFreeze(self, freeze):
        self.freeze = freeze

    def getLabel(self):
        return self.label

    def setTimeSpeed(self, speed):
        self.timeSpeed = speed
        self.parent.parent.sg_audio.setMetroTime(self.label-1, speed * 0.001)

    def getTimeSpeed(self):
        return self.timeSpeed
        
    def setEditionLevel(self, level):
        self.editLevel = level

    def activateLp(self, state):
        self.activeLp = state

    def setFilterFreq(self, freq):
        self.filterCut = freq
        self.lpx.setFreq(freq)
        self.lpy.setFreq(freq)

    def setFilterQ(self, q):
        self.lpx.setQ(q)
        self.lpy.setQ(q)

    def setType(self, t):
        self.type = t

    def getType(self):
        return self.type

    def setActive(self, state=None):
        if state != None:
            self.active = state
        if self.active:
            self.parent.parent.sg_audio.setActive(self.label-1, 1)
        else:
            self.parent.parent.sg_audio.setActive(self.label-1, 0)
            
    def getActive(self):
        return self.active
        
    def addPoint(self, point):
        if len(self.points) > 1:
            if point == self.points[-1]:
                return
            if self.activeLp:
                point = (int(round(self.lpx.filter(point[0]))), int(round(self.lpy.filter(point[1]))))
            self.points.append(point)
        else:
            self.points.append(point)

    def addFinalPoint(self, point, closed):
        if closed:
            self.points.append(point)
        
            maxstep = max(abs(point[0]-self.points[0][0]), abs(point[1]-self.points[0][1]))
            xscale = abs(point[0]-self.points[0][0])
            yscale = abs(point[1]-self.points[0][1])
        
            if point[0] < self.points[0][0]: xdir = 1
            else: xdir = -1
            if point[1] < self.points[0][1]: ydir = 1
            else: ydir = -1
        
            for i in range(0, maxstep, 2):
                xpt = point[0] + xdir * int( xscale * ((i+1) / float(maxstep)))
                ypt = point[1] + ydir * int( yscale * ((i+1) / float(maxstep)))
                self.points.append((int(round(xpt)),int(round(ypt))))
                 
        self.setInitPoints()

    def fillPoints(self, closed): 
        filllpx = BiquadLP(freq=self.filterCut)
        filllpy = BiquadLP(freq=self.filterCut)
        templist = []  
        if closed: length = len(self.points)
        else: length = len(self.points) - 1
        for i in range(length):
            if closed: 
                first = i-1
                second = i
            else:
                first = i
                second = i+1
            a = self.points[first][0]-self.points[second][0]
            b = self.points[first][1]-self.points[second][1]
            step = sqrt(a*a+b*b)
            xscale = abs(self.points[first][0]-self.points[second][0]) * 0.5
            yscale = abs(self.points[first][1]-self.points[second][1]) * 0.5
 
            if self.points[first][0] == self.points[second][0]: xdir = 0            
            elif self.points[first][0] < self.points[second][0]: xdir = 1
            else: xdir = -1
            if self.points[first][1] == self.points[second][1]: ydir = 0
            elif self.points[first][1] < self.points[second][1]: ydir = 1
            else: ydir = -1
            
            p = (int(round(filllpx.filter(self.points[first][0]))), int(round(filllpy.filter(self.points[first][1]))))
            if not templist:
                templist.append(p)
            else:
                gate = self.removeMatch(templist, p)
                if gate:
                    templist.append(p)
            if step > 3:       
                xpt = self.points[first][0] + xdir * xscale
                ypt = self.points[first][1] + ydir * yscale
                p = (int(round(filllpx.filter(xpt))),int(round(filllpy.filter(ypt))))
                gate = self.removeMatch(templist, p)
                if gate:
                    templist.append(p)
        templist.append((int(round(filllpx.filter(self.points[-1][0]))), int(round(filllpy.filter(self.points[-1][1])))))
        templist.append(self.points[-1])
        self.points = [(p[0], p[1]) for p in templist]

    def removeMatch(self, templist, p):
        if templist:
            if p == templist[-1]: return False
            else: return True
        else:
            return True

    def setInitPoints(self):
        self.initPoints = [(p[0], p[1]) for p in self.points]

    def editTraj(self, index, offset):
        p_off = len(self.initPoints) / self.editLevel
        # clicked point
        self.points[index] = [self.initPoints[index][0] - offset[0], self.initPoints[index][1] - offset[1]]
        #for i in range(1,p_off2):
        for i in range(1, p_off):    
            # sigmoid scaling function 
            off = (p_off-i) / float(p_off) * 0.5
            mult = .5 + (sin((off + .75) * 2 * pi) * .5)
            # scales i points each side of clicked point
            if index+i < len(self.initPoints): iplus = index+i
            else: iplus = index+i - len(self.initPoints)
            self.points[index-i] = [int(round(self.initPoints[index-i][0] - offset[0] * mult)), int(round(self.initPoints[index-i][1] - offset[1] * mult))]
            self.points[iplus] = [int(round(self.initPoints[iplus][0] - offset[0] * mult)), int(round(self.initPoints[iplus][1] - offset[1] * mult))]

    def move(self, offset):
        self.points = [(p[0]-offset[0], p[1]-offset[1]) for p in self.initPoints]
        if self.getFreeze():
            self.circlePos = self.points[(self.counter-self.step) % len(self.points)]

    def getInsideRect(self, point):
        return wx.Rect(self.getFirstPoint()[0], self.getFirstPoint()[1], 10, 10).Contains(point)
        
    def getFirstPoint(self):
        return self.points[0]
        
    def getPoints(self):
        return self.points

    def setPoints(self, plist):
        if not plist:
            self.clear()
        else:
            self.points = [p for p in plist]
            self.setInitPoints()
        
    def getPointPos(self):
        return self.circlePos
        
    def setStep(self, step):
        self.step = step

    def getStep(self):
        return self.step

    def initCounter(self):
        self.counter = 0

    def clock(self):
        if not self.freeze:
            if self.points:
                if self.circlePos != None:
                    self.lastCirclePos = self.circlePos
                self.circlePos = self.points[self.counter % len(self.points)]
                self.counter += self.step
                self.mario = (self.mario+1) % 4

    ### Circle functions ###
    def addCirclePoint(self, point):
        if len(self.points) > 1:
            if point == self.points[-1]:
                return
            if self.activeLp:
                point = (int(round(self.lpx.filter(point[0]))), int(round(self.lpy.filter(point[1]))))
        self.points.append(point)

    def getLosangePoint(self):
        return self.points[int(len(self.points)*2/3)]

    def getInsideLosange(self, point):
        if self.type == 'circle' or self.type == 'oscil':
            return wx.Rect(self.getLosangePoint()[0]-5, self.getLosangePoint()[1]-5, 10, 10).Contains(point)
        else:
            return False

    def getCenter(self):
        return self.center

    def setCenter(self, c):
        self.center = c

    def getRadius(self):
        return self.radius

    def setRadius(self, r):
        self.radius = r
        
class DrawingSurface(wx.Panel):
    def __init__(self, parent, pos=(0,0), size=wx.DefaultSize):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, pos=pos, size=size, style = wx.EXPAND)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.SetBackgroundColour(BACKGROUND_COLOUR)
        self.parent = parent
        self.useMario = False
        self.marios = [
                        wx.Bitmap(os.path.join(IMAGES_PATH, 'Mario1.png'), wx.BITMAP_TYPE_PNG),
                        wx.Bitmap(os.path.join(IMAGES_PATH, 'Mario2.png'), wx.BITMAP_TYPE_PNG),
                        wx.Bitmap(os.path.join(IMAGES_PATH, 'Mario3.png'), wx.BITMAP_TYPE_PNG),
                        wx.Bitmap(os.path.join(IMAGES_PATH, 'Mario2.png'), wx.BITMAP_TYPE_PNG),
                        wx.Bitmap(os.path.join(IMAGES_PATH, 'Mario4.png'), wx.BITMAP_TYPE_PNG),
                        wx.Bitmap(os.path.join(IMAGES_PATH, 'Mario5.png'), wx.BITMAP_TYPE_PNG),
                        wx.Bitmap(os.path.join(IMAGES_PATH, 'Mario6.png'), wx.BITMAP_TYPE_PNG),
                        wx.Bitmap(os.path.join(IMAGES_PATH, 'Mario5.png'), wx.BITMAP_TYPE_PNG)
                        ]
        if PLATFORM in ['win32', 'linux2']:
            self.font = wx.Font(7, wx.NORMAL, wx.NORMAL, wx.NORMAL)
        else:
            self.font = wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL)
        self.trajectoriesBank = [Trajectory(i+1, self) for i in range(24)]
        self.numOfTrajectories(24)
        self.screenOffset = 2
        self.sndBitmap = None
        self.bitmapDict = {}
        self.closed = 0
        self.oscilPeriod = 2
        self.oscilScaling = 1
        self.mode = trajTypes[0]
        self.SetColors(outline=(255,255,255), bg=(30,30,30), fill=(255,0,0), rect=(0,255,0), losa=(0,0,255), wave=(70,70,70))
        self.currentSize = self.GetSizeTuple()
    
        self.Bind(wx.EVT_KEY_DOWN, self.KeyDown)
        self.Bind(wx.EVT_LEFT_DOWN, self.MouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.MouseUp)
        self.Bind(wx.EVT_RIGHT_DOWN, self.deleteTraj)
        self.Bind(wx.EVT_MOTION, self.MouseMotion)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnResize)

    def setCurrentSize(self, size):
        self.currentSize = size

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
        self.currentSize = (w,h)

    def clock(self, which):
        t = self.trajectoriesBank[which]
        t.clock()
        if t.getActive():
            w,h = self.GetSizeTuple()
            w,h = float(w), float(h)
            if t.getPointPos() != None:
                x = t.getPointPos()[0]/w
                y = 1 - t.getPointPos()[1]/h
                self.parent.sg_audio.setXposition(which, x)
                self.parent.sg_audio.setYposition(which, y)
                
    def setOscilPeriod(self, period):
        self.oscilPeriod = period

    def getOscilPeriod(self):
        return self.oscilPeriod

    def setOscilScaling(self, scaling):
        self.oscilScaling = scaling

    def getOscilScaling(self):
        return self.oscilScaling
        
    def numOfTrajectories(self, num):
        self.trajectories = self.trajectoriesBank[0:num]
                
    def SetColors(self, outline, bg, fill, rect, losa, wave):
        self.outlinecolor = wx.Color(*outline)
        self.backgroundcolor = wx.Color(*bg)
        self.fillcolor = wx.Color(*fill)
        self.rectcolor = wx.Color(*rect)
        self.losacolor = wx.Color(*losa)
        self.wavecolor = wx.Color(*wave)
            
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
        self.mode = trajTypes[mode]

    def setClosed(self, closed):
        self.closed = closed

    def getTrajectory(self, which):
        return self.trajectoriesBank[which]

    def getAllTrajectories(self):
        return self.trajectories

    def getActiveTrajectories(self):
        return [t for t in self.trajectories if t.getActive()]
   
    def deleteTraj(self, evt):
        for t in self.getActiveTrajectories():
            if t.getInsideRect(evt.GetPosition()):
                t.clear()
                self.Refresh()
                return

    def KeyDown(self, evt):
        off = {wx.WXK_UP: [0,1], wx.WXK_DOWN: [0,-1], wx.WXK_LEFT: [1,0], wx.WXK_RIGHT: [-1,0]}.get(evt.GetKeyCode(), [0,0])
        if evt.ShiftDown() and off != [0,0]:
            traj = self.trajectoriesBank[self.parent.controls.getSelected()-1]
            if traj.getType() in ['circle', 'oscil']:
                center = traj.getCenter()
                traj.setCenter((center[0]-off[0], center[1]-off[1]))
            traj.move(off)
            traj.setInitPoints()
        elif off != [0,0]:
            for traj in self.getActiveTrajectories():
                if traj.getType() in ['circle', 'oscil']:
                    center = traj.getCenter()
                    traj.setCenter((center[0]-off[0], center[1]-off[1]))
                traj.move(off)
                traj.setInitPoints()

        if evt.GetKeyCode() < 256:
            c = chr(evt.GetKeyCode())
            if c in ['1', '2', '3', '4', '5', '6', '7', '8']:
                if self.trajectoriesBank[int(c)-1].getFreeze():
                    self.trajectoriesBank[int(c)-1].setFreeze(False)
                else:
                    self.trajectoriesBank[int(c)-1].setFreeze(True)
            elif c == '0': 
                for i in range(8): 
                    if self.trajectoriesBank[i].getFreeze():
                        self.trajectoriesBank[i].setFreeze(False)
                    else:
                        self.trajectoriesBank[i].setFreeze(True)
            elif c == '9':
                if not self.useMario:
                    self.useMario = True
                else:
                    self.useMario = False                
                      
        self.Refresh()
     
    def MouseDown(self, evt):
        self.downPos = evt.GetPositionTuple()
        for t in self.getActiveTrajectories():
            if t.getInsideRect(self.downPos):
                if evt.AltDown():
                    for new_t in self.trajectories:
                        if not new_t.getActive():
                            self.selected = new_t
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
                    self.selected = t
                Xs = [p[0] for p in self.selected.getPoints()]
                self.extremeXs = (min(Xs), max(Xs))
                Ys = [p[1] for p in self.selected.getPoints()]
                self.extremeYs = (min(Ys), max(Ys))                
                self.action = 'drag'
                if self.selected.getType() not in  ['free', 'line']:
                    self.curCenter = self.selected.getCenter()
                self.CaptureMouse()
                return
            if t.getInsideLosange(self.downPos):
                self.selected = t
                self.action = 'rescale'
                self.CaptureMouse()
                return

            for p in t.getPoints():
                if wx.Rect(p[0]-5, p[1]-5, 10, 10).Contains(self.downPos):
                    self.pindex = t.getPoints().index(p)
                    self.selected = t
                    self.action = 'edit'
                    self.CaptureMouse()
                    return

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
                if self.traj.getType() == 'circle':
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

            self.Refresh()  
            self.ReleaseMouse()
            self.parent.createTempFile()
        evt.Skip()

    def MouseMotion(self, evt):
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
                    maxstep = int(sqrt(x2*x2+y2*y2))
        
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
                self.traj.lpx.reinit()
                self.traj.lpy.reinit()
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
            self.Refresh()
        evt.Skip()
    
    def OnPaint(self, evt):
        x,y = (0,0)
        w,h = self.GetSizeTuple()
        dc = wx.AutoBufferedPaintDC(self)

        if not self.sndBitmap:
            dc.SetBrush(wx.Brush(self.backgroundcolor, wx.SOLID))
            dc.Clear()
            
            dc.SetPen(wx.Pen(self.outlinecolor, width=1, style=wx.SOLID))
            dc.DrawRectangle(x, y, w, h)
    
            dc.SetBrush(wx.Brush(self.fillcolor, wx.SOLID))
            dc.SetPen(wx.Pen(self.fillcolor, width=1, style=wx.SOLID))
        else:
            dc.DrawBitmap(self.sndBitmap,0,0)
             
        for t in self.getActiveTrajectories():
            dc.SetBrush(wx.Brush(self.fillcolor, wx.SOLID))
            dc.SetPen(wx.Pen(self.fillcolor, width=1, style=wx.SOLID))
            if len(t.getPoints()) > 1:
                dc.DrawLines(t.getPoints())
                if t.circlePos:
                    if not self.useMario:    
                        dc.DrawCirclePoint(t.circlePos, 4)
                    else:
                        if t.lastCirclePos[0] < t.circlePos[0]: marioff = 0
                        else: marioff = 4
                        bitmario = self.marios[t.mario + marioff]
                        dc.DrawBitmap(bitmario, t.circlePos[0]-8, t.circlePos[1]-8, True)
                dc.DrawRoundedRectanglePointSize((t.getFirstPoint()[0],t.getFirstPoint()[1]), (10,10), 2)
                dc.SetTextForeground("#FFFFFF")
                dc.SetFont(self.font)
                dc.DrawLabel(str(t.getLabel()), wx.Rect(t.getFirstPoint()[0],t.getFirstPoint()[1], 10, 10), wx.ALIGN_CENTER)
                if t.getType() not in ['free', 'line']:
                    dc.SetBrush(wx.Brush(self.losacolor, wx.SOLID))
                    dc.SetPen(wx.Pen(self.losacolor, width=1, style=wx.SOLID))
                    dc.DrawRoundedRectanglePointSize((t.getLosangePoint()[0]-5,t.getLosangePoint()[1]-5), (10,10), 1)
 
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
                        rec = wx.Rect(i, halfY+off, 1, val)
                        self.memory.GradientFillLinear(rec, "#999999", "#222222", wx.BOTTOM)
                        rec = wx.Rect(i, halfY+off-val, 1, val)
                        self.memory.GradientFillLinear(rec, "#999999", "#222222", wx.UP)
                        last = val                
            else:    
                if self.list[chan]:
                    last = 0
                    for i in range(X):
                        y = int(round(i / scalar))
                        val = int(((halfY * self.list[chan][y]) + last) / 2)
                        append((i,halfY+off,i,halfY+off+val))
                        append((i,halfY+off,i,halfY+off-val))
                        last = val
        if not gradient:                
            self.memory.DrawLineList(l)
        self.memory.SelectObject(wx.NullBitmap)
        self.Refresh()

class ControlPanel(scrolled.ScrolledPanel):
    def __init__(self, parent, surface):
        scrolled.ScrolledPanel.__init__(self, parent, -1)
        self.SetBackgroundColour(BACKGROUND_COLOUR)
        self.parent = parent
        self.surface = surface
        self.type = 0
        self.selected = 0
        self.server_booted = False
        self.cue_snd = None
        self.sndPath = None
        self.amplitude = 1
        self.nchnls = 2

        box = wx.BoxSizer(wx.VERTICAL)

        typeBox = wx.BoxSizer(wx.HORIZONTAL)

        box.Add(wx.StaticText(self, -1, "Trajectories"), 0, wx.CENTER|wx.TOP, 3)

        popupBox = wx.BoxSizer(wx.VERTICAL)
        popupBox.Add(wx.StaticText(self, -1, "Type"), 0, wx.CENTER|wx.ALL, 2)
        self.trajType = wx.Choice(self, -1, choices = ['Free', 'Circle', 'Oscil', 'Line'])
        self.trajType.SetSelection(0)
        popupBox.Add(self.trajType)
        typeBox.Add(popupBox, 0, wx.CENTER|wx.RIGHT, 5)
     
        self.closedToggle = wx.ToggleButton(self, -1, 'Closed', size=(55,-1))
        if PLATFORM in ['win32', 'linux2']:
            self.closedToggle.SetFont(wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL))
        if PLATFORM == 'win32':
            typeBox.Add(self.closedToggle, 0, wx.TOP, 15 )
        else:    
            typeBox.Add(self.closedToggle, 0, wx.TOP, 21 )

        box.Add(typeBox, 0, wx.CENTER|wx.ALL, 5)

        self.notebook = wx.Notebook(self, -1, style=wx.BK_DEFAULT | wx.EXPAND)
        self.drawing = DrawingParameters(self.notebook)
        self.playback = PlaybackParameters(self.notebook)
        self.notebook.AddPage(self.drawing, "Drawing")
        self.notebook.AddPage(self.playback, "Playback")
        box.Add(self.notebook, 0, wx.ALL, 5)

        box.Add(wx.StaticText(self, -1, "Global amplitude"), 0, wx.LEFT | wx.TOP, 10)
        ampBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_amp = ControlSlider(self, 0, 4, 1, size=(200, 16), outFunction=self.handleAmp)
        ampBox.Add(self.sl_amp, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(ampBox, 0, wx.LEFT | wx.RIGHT, 5)
        box.AddSpacer(10)
        self.meter = VuMeter(self, size=(200,11))
        self.meter.setNumSliders(self.nchnls)
        box.Add(self.meter, 0, wx.BOTTOM|wx.LEFT, 10)

        chnlsBox = wx.BoxSizer(wx.HORIZONTAL)
        chnlsBox.Add(wx.StaticText(self, -1, "# of channels :"), 0, wx.LEFT | wx.TOP, 12)
        self.tx_chnls = wx.TextCtrl(self, -1, "2", size=(40, -1), style=wx.TE_PROCESS_ENTER)
        self.tx_chnls.Bind(wx.EVT_TEXT_ENTER, self.handleNchnls)
        chnlsBox.Add(self.tx_chnls, 0, wx.TOP|wx.LEFT, 10)
        box.Add(chnlsBox, 0, wx.ALL, 0)

        soundBox = wx.BoxSizer(wx.HORIZONTAL)
        self.tog_server = wx.ToggleButton(self, -1, "Audio on", size=(80,-1))
        if PLATFORM in ['win32', 'linux2']:
            self.tog_server.SetFont(wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL))
        soundBox.Add(self.tog_server, 0, wx.ALL, 10)
        self.tog_audio = wx.ToggleButton(self, -1, "Start", size=(80,-1))
        if PLATFORM in ['win32', 'linux2']:
            self.tog_audio.SetFont(wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL))
        self.tog_audio.Disable()    
        soundBox.Add(self.tog_audio, 0, wx.ALL, 10)
        box.Add(soundBox, 0, wx.ALL, 5)

        box.Add(wx.StaticText(self, -1, "Record to disk"), 0, wx.CENTER, 5)
        recBox = wx.BoxSizer(wx.HORIZONTAL)
        self.tx_output = wx.TextCtrl( self, -1, "snd", size=(120, -1))
        recBox.Add(self.tx_output, 0, wx.LEFT | wx.RIGHT, 10)
        self.tog_record = wx.ToggleButton(self, -1, "Start", size=(50,-1))
        if PLATFORM in ['win32', 'linux2']:
            self.tog_record.SetFont(wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL))
        self.tog_record.Disable()
        recBox.Add(self.tog_record, 0, wx.ALIGN_CENTER)
        box.Add(recBox, 0, wx.ALL, 5)


        self.Bind(wx.EVT_CHOICE, self.handleType, self.trajType)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.handleClosed, self.closedToggle)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.handleServer, self.tog_server)
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

    def handleSelected(self, event):
        self.selected = event.GetInt()
        timeSpeed = self.surface.getTrajectory(self.selected).getTimeSpeed()
        step = self.surface.getTrajectory(self.selected).getStep()
        self.setTimerSpeed(timeSpeed)
        self.setStep(step)

    def setSelected(self, selected):
        self.playback.tog_traj.SetSelection(selected)
        self.selected = selected
        timeSpeed = self.surface.getTrajectory(selected).getTimeSpeed()
        step = self.surface.getTrajectory(selected).getStep()
        self.setTimerSpeed(timeSpeed)
        self.setStep(step)

    def getSelected(self):
        return self.selected

    def handleTimerSpeed(self, val):
        self.surface.getTrajectory(self.selected).setTimeSpeed(val)
  
    def setTimerSpeed(self, timeSpeed):
        self.playback.sl_timespeed.SetValue(timeSpeed)

    def sendTrajSpeed(self, which, speed):
        self.parent.sg_audio.setMetroTime(which, speed * 0.001)
              
    def handleStep(self, val):
        self.surface.getTrajectory(self.selected).setStep(val)

    def setStep(self, step):
        self.playback.sl_step.SetValue(step)

    def handleAmp(self, val):
        self.amplitude = val
        self.sendAmp()

    def getAmp(self):
        return self.amplitude

    def setAmp(self, amp):
        self.sl_amp.SetValue(amp)
        self.amplitude = amp

    def sendAmp(self):
        self.parent.sg_audio.server.amp = self.amplitude
            
    def handleLoad(self):
        dlg = wx.FileDialog(self, message="Choose a sound file",
                            defaultDir=os.path.expanduser('~'), 
                            defaultFile="",
                            wildcard="AIFF file |*.aif;*.aiff;*.aifc;*.AIF;*.AIFF;*.Aif;*.Aiff|" \
                                     "Wave file |*.wav;*.wave;*.WAV;*.WAVE;*.Wav;*.Wave",
                            style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            sndPath = dlg.GetPath()
            if self.server_booted:
                self.loadSound(sndPath)
            else:
                self.cue_snd = sndPath   
        dlg.Destroy()

    def loadSound(self, sndPath, force=False):
        self.sndPath = sndPath
        if self.sndPath:
            if os.path.isfile(self.sndPath):
                self.parent.sg_audio.loadSnd(self.sndPath)
                chnls, samprate, dur = soundInfo(self.sndPath)
                self.sndDur = dur
                self.chnls = chnls
                self.sndInfoStr = 'Loaded sound: %s,    Sr: %s Hz,    Channels: %s,    Duration: %s sec' % (self.sndPath, samprate, chnls, dur)
                if self.parent.draw:
                    if not self.sndPath in self.surface.bitmapDict.keys() or force:
                        self.parent.log("Drawing waveform...")
                        self.surface.analyse(self.sndPath)
                    else:
                        self.surface.list = self.surface.bitmapDict[self.sndPath]
                        self.surface.create_bitmap()
                self.logSndInfo()
            elif os.path.isfile(os.path.join(self.parent.currentPath, os.path.split(self.sndPath)[1])):
                self.loadSound(os.path.join(self.parent.currentPath, os.path.split(self.sndPath)[1]), force)  
            else:
                self.parent.log('Sound file "%s" does not exist!' % self.sndPath)        

    def drawWaveform(self):
        if self.surface.sndBitmap and self.parent.draw:
            self.surface.create_bitmap()

    def getNchnls(self):
        return self.nchnls
        
    def setNchnls(self, x):
        self.nchnls = x
        self.tx_chnls.SetValue(str(x))
        self.meter.setNumSliders(self.nchnls)
            
    def handleNchnls(self, event):
        self.nchnls = int(self.tx_chnls.GetValue())
        self.meter.setNumSliders(self.nchnls)
        
    def handleServer(self, event):
        if event.GetInt() == 1:
            self.server_booted = True
            self.parent.sg_audio.boot(self.parent.audioDriver, self.nchnls)
            self.tog_server.SetLabel("Audio off")
            self.tog_server.SetValue(1)
            self.tog_audio.Enable()    
            self.tx_chnls.Disable()
            if self.cue_snd != None:
                self.loadSound(self.cue_snd)
                self.cue_snd = None
        else:    
            self.server_booted = False
            self.parent.sg_audio.shutdown()
            self.tog_server.SetLabel("Audio on")            
            self.tog_server.SetValue(0)
            self.tog_audio.Disable()  
            self.tx_chnls.Enable()
            self.surface.sndBitmap = None
            self.sndPath = None
            self.surface.Refresh()  
            
    def handleAudio(self, event):
        if event.GetInt() == 1:
            if not self.sndPath:
                self.parent.log('*** No sound loaded! ***')
                self.tog_audio.SetValue(0)
                self.parent.menu.Check(7, False)
            else:    
                self.tog_server.Disable()
                self.tog_audio.SetValue(1)
                self.tog_audio.SetLabel('Stop')
                self.parent.menu.Check(7, True)
                self.tog_record.Enable()

                for t in self.surface.getAllTrajectories():
                    t.initCounter()
                self.parent.sg_audio.start()
        else:    
            self.tog_server.Enable()
            self.tog_audio.SetValue(0)
            self.tog_audio.SetLabel('Start')
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
            path = self.tx_output.GetValue()
            if not path.endswith('.aif'):
                path = path + '.aif'
            if os.path.isabs(path):   
                self.parent.sg_audio.server.recstart(path)        
            else:
                self.parent.sg_audio.server.recstart(os.path.join(os.path.expanduser('~'), path))        
            self.tog_record.SetLabel('Stop')
        else:
            self.tog_record.SetLabel('Start')
            self.parent.sg_audio.server.recstop()

    def logSndInfo(self):
        self.parent.log(self.sndInfoStr)

class DrawingParameters(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.SetBackgroundColour(BACKGROUND_COLOUR)

        self.parent = parent
        box = wx.BoxSizer(wx.VERTICAL)

        box.Add(wx.StaticText(self, -1, "Lowpass cutoff"), 0, wx.LEFT|wx.TOP, 5)
        cutoffBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_cutoff = ControlSlider(self, 100, 15000, 5000, size=(195, 16), integer=True, log=True, outFunction=self.parent.GetParent().handleCutoff)
        cutoffBox.Add(self.sl_cutoff)
        box.Add(cutoffBox, 0, wx.LEFT | wx.RIGHT, 5)

        box.AddSpacer(5)

        box.Add(wx.StaticText(self, -1, "Lowpass Q"), 0, wx.LEFT, 5)
        qBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_q = ControlSlider(self, 0.5, 1000, 0.5, size=(195, 16), outFunction=self.parent.GetParent().handleQ)
        qBox.Add(self.sl_q)
        box.Add(qBox, 0, wx.LEFT | wx.RIGHT, 5)

        box.AddSpacer(5)
        
        box.Add(wx.StaticText(self, -1, "Oscil period"), 0, wx.LEFT, 5)
        periodBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_period = ControlSlider(self, 0, 5, 2, size=(195, 16), outFunction=self.parent.GetParent().handlePeriod)
        periodBox.Add(self.sl_period)
        self.sl_period.Disable()
        box.Add(periodBox, 0, wx.LEFT | wx.RIGHT, 5)

        box.AddSpacer(5)

        box.Add(wx.StaticText(self, -1, "Oscil scaling"), 0, wx.LEFT, 5)
        scalingBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_scaling = ControlSlider(self, 0, 4, 1, size=(195, 16), outFunction=self.parent.GetParent().handleScaling)
        scalingBox.Add(self.sl_scaling)
        self.sl_scaling.Disable()
        box.Add(scalingBox, 0, wx.LEFT | wx.RIGHT, 5)                   

        box.AddSpacer(5)

        self.SetAutoLayout(True)

        self.SetSizer(box)

class PlaybackParameters(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.SetBackgroundColour(BACKGROUND_COLOUR)

        self.parent = parent
        box = wx.BoxSizer(wx.VERTICAL)

        box.Add(wx.StaticText(self, -1, "Selected trajectory"), 0, wx.CENTER | wx.TOP | wx.BOTTOM, 5)
        self.tog_traj = wx.Choice(self, -1, choices = [str(i+1) for i in range(24)])
        self.tog_traj.SetSelection(0)
        self.tog_traj.Bind(wx.EVT_CHOICE, self.parent.GetParent().handleSelected)
        box.Add(self.tog_traj, 0, wx.CENTER, 5)

        box.AddSpacer(10)

        box.Add(wx.StaticText(self, -1, "Timer speed"), 0, wx.LEFT, 5)
        timespeedBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_timespeed = ControlSlider(self, 10, 500, 25, size=(195, 16), outFunction=self.parent.GetParent().handleTimerSpeed)
        timespeedBox.Add(self.sl_timespeed)
        box.Add(timespeedBox, 0, wx.LEFT | wx.RIGHT, 5)

        box.AddSpacer(5)
        
        box.Add(wx.StaticText(self, -1, "Point step"), 0, wx.LEFT, 5)
        stepBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_step = ControlSlider(self, 1, 100, 1, size=(195, 16), integer=True, outFunction=self.parent.GetParent().handleStep)
        stepBox.Add(self.sl_step)
        box.Add(stepBox, 0, wx.LEFT | wx.RIGHT, 5)

        self.SetAutoLayout(True)

        self.SetSizer(box)

class MainFrame(wx.Frame):
    def __init__(self, parent, id, pos, size, file):
        wx.Frame.__init__(self, parent, id, "", pos, size)

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
        self.menu1.AppendMenu(103, "Edition levels", self.submenu1)
        self.menu1.InsertSeparator(7)
        self.menu1.Append(103, "Reinit counters\tCtrl+T", "")
        self.Bind(wx.EVT_MENU, self.handleReinit, id=103)
        self.menuBar.Append(self.menu1, "&Drawing")

        self.menu2 = wx.Menu()
        self.menuBar.Append(self.menu2, "&Audio Drivers")

        menu4 = wx.Menu()
        helpItem = menu4.Append(400, '&About %s %s' % (NAME, VERSION), 'wxPython RULES!!!')
        wx.App.SetMacAboutMenuItemId(helpItem.GetId())
        self.Bind(wx.EVT_MENU, self.showAbout, helpItem)
        self.menuBar.Append(menu4, '&Help')

        self.SetMenuBar(self.menuBar)
       
        mainBox = wx.BoxSizer(wx.HORIZONTAL)
        self.panel = DrawingSurface(self)
        self.controls = ControlPanel(self, self.panel)
        mainBox.Add(self.panel, 20, wx.EXPAND, 5)
        mainBox.Add(self.controls, 0, wx.EXPAND, 5)
        self.SetSizer(mainBox)
        
        self.Bind(wx.EVT_SIZE, self.OnResize)        
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.SetTitle('Granulator')

        self.sg_audio = SG_Audio(self.panel.clock, self.panel.Refresh, self.controls)
        
        self.granulatorControls = GranulatorFrame(self, self.panel, self.sg_audio)
        
        self.createInitTempFile()

        if file:
            self.loadFile(file)

        self.Show()
        wx.CallAfter(self.check)
 
    def onRun(self, event):
        self.controls.handleAudio(event)
        
    def check(self):
        self.status.SetStatusText('Scanning audio drivers...')
        self.driversList, self.driverIndexes, selected = checkForDrivers()
        self.audioDriver = selected
        
        for i, driver in enumerate(self.driversList):
            menuId = 200 + i
            self.menu2.Append(menuId, driver, "", wx.ITEM_RADIO)
            self.Bind(wx.EVT_MENU, self.handleDriver, id=menuId)
            if driver == selected:
                self.menu2.Check(menuId, True)
        self.status.SetStatusText('Audio drivers loaded')

    def handleReinit(self, evt):
        for t in self.panel.getAllTrajectories():
            t.initCounter()

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
        
    def openFxWindow(self, evt):
        if self.granulatorControls.IsShown():
            self.granulatorControls.Hide()
        else:
            self.granulatorControls.SetTitle('Granulator controls')
            self.granulatorControls.Show()

    def OnResize(self, evt):
        self.controls.drawWaveform()
        evt.Skip()

    def handleUndo(self, evt):
        self.recallTempFile(evt.GetId())

    def handleNew(self, evt):
        self.panel.sndBitmap = None
        self.loadFile(os.path.join(RESOURCES_PATH, 'new_soundgrain_file.sg'))
        
    def handleOpen(self, evt):
        dlg = wx.FileDialog(self, message="Open SoundGrain file...",
                            defaultDir=os.path.expanduser('~'), 
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
                            defaultDir=os.path.expanduser('~'),
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

    def saveFile(self, path):
        self.currentFile = path
        self.currentPath = os.path.split(path)[0]
        saveDict = {}

        ### Main Frame ###
        saveDict['MainFrame'] = {}
        saveDict['MainFrame']['draw'] = self.draw
        saveDict['MainFrame']['lowpass'] = self.lowpass
        saveDict['MainFrame']['fillPoints'] = self.fillPoints
        saveDict['MainFrame']['editionLevel'] = self.editionLevel
        saveDict['MainFrame']['size'] = self.GetSizeTuple()

        ### Controls Frame ###
        saveDict['ControlFrame'] = self.granulatorControls.save()

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
        saveDict['ControlPanel']['sound'] = self.controls.sndPath

        ### Trajectories ###
        saveDict['Trajectories'] = {}
        for i, t in enumerate(self.panel.getAllTrajectories()):
            saveDict['Trajectories'][str(i)] = t.getAttributes()
        msg = xmlrpclib.dumps((saveDict, ), allow_none=True)
        f = open(path, 'w')
        f.write(msg)
        f.close()

        self.SetTitle(os.path.split(self.currentFile)[1])

    def loadFile(self, path):
        if not self.controls.server_booted:
            command = wx.CommandEvent(wx.wxEVT_COMMAND_TOGGLEBUTTON_CLICKED)
            command.SetInt(1)
            self.controls.handleServer(command) 
        f = open(path, 'r')
        msg = f.read()
        f.close()
        result, method = xmlrpclib.loads(msg)
        dict = result[0]
        self.currentFile = path
        self.currentPath = os.path.split(path)[0]

        ### Main Frame ###
        self.setDraw(dict['MainFrame']['draw'])
        self.setLowpass(dict['MainFrame']['lowpass'])
        self.setFillPoints(dict['MainFrame']['fillPoints'])
        self.setEditionLevel(dict['MainFrame']['editionLevel'])
        self.SetSize(dict['MainFrame']['size'])
        self.OnResize(wx.SizeEvent(dict['MainFrame']['size']))

        ### Control Frame ###
        self.granulatorControls.load(dict['ControlFrame'])

        ### Control panel ###
        self.controls.setType(dict['ControlPanel']['type'])
        self.controls.setClosed(dict['ControlPanel']['closed'])
        self.controls.setCutoff(dict['ControlPanel']['cutoff'])
        self.controls.setQ(dict['ControlPanel']['q'])
        self.controls.setPeriod(dict['ControlPanel']['period'])
        self.controls.setScaling(dict['ControlPanel']['scaling'])
        self.controls.setAmp(dict['ControlPanel']['globalamp'])
        self.controls.setNchnls(dict['ControlPanel']['nchnls'])
        self.controls.loadSound(dict['ControlPanel']['sound'])
        ### Trajectories ###
        for i, t in enumerate(self.panel.getAllTrajectories()):
            t.setAttributes(dict['Trajectories'][str(i)])
            
        self.controls.setSelected(0)    
        self.panel.Refresh()

        self.SetTitle(os.path.split(self.currentFile)[1])

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
        if self.recall >= len(self.temps) - 1:
            self.menu1.Enable(110, False)
        else:
            self.menu1.Enable(110, True)
        if self.undos == 0:
            self.menu1.Enable(111, False)
        else:
            self.menu1.Enable(111, True) 

    def OnClose(self, evt):
        self.controls.meter.OnClose(evt)
        self.sg_audio.server.stop()
        tmpFiles = os.listdir(TEMP_PATH)
        for file in tmpFiles:
            os.remove(os.path.join(TEMP_PATH, file))
        self.Destroy()
        sys.exit()

    def log(self, text):
        self.status.SetStatusText(text)

    def showAbout(self, evt):
        info = wx.AboutDialogInfo()

        description = wordwrap(
"Sound Grain is a graphical interface where " 
"users can draw and edit trajectories to " 
"control granular sound synthesis modules.\n"

"Sound Grain is written with Python and " 
"uses pyo as its audio engine.",350, wx.ClientDC(self))

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
        info.SetVersion('%s' % VERSION)
        info.SetDescription(description)
        info.SetCopyright('(C) 2009 Olivier Belanger')
        info.SetWebSite('http://code.google.com/p/soundgrain')
        info.SetLicence(licence)
        wx.AboutBox(info)
              
if __name__ == '__main__': 
    try:
        import psyco
        psyco.full()
        print "SoundGrain Uses Psyco"
    except ImportError:
        print "Psyco not found"

    file = None
    if len(sys.argv) > 1:
        file = sys.argv[1]

    app = wx.PySimpleApp()
    X,Y = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X), wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
    if X < 900: sizex = X - 40
    else: sizex = 900
    if PLATFORM in ['win32', 'linux2']: defaultY = 550
    else: defaultY = 530
    if Y < defaultY: sizey = Y - 40
    else: sizey = defaultY
    f = MainFrame(None, -1, pos=(20,20), size=(sizex,sizey), file=file)
    app.MainLoop()
