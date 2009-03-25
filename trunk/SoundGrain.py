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

systemPlatform = sys.platform

print os.getcwd()
if '/SoundGrain.app' in os.getcwd():
    RESOURCES_PATH = os.getcwd()
    currentw = os.getcwd()
    spindex = currentw.index('/SoundGrain.app')
    os.chdir(currentw[:spindex])
else:
    RESOURCES_PATH = os.path.join(os.getcwd(), 'Resources')

from Resources.audio import *
from Resources.Biquad import BiquadLP
from Resources.Modules import *

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
    def __init__(self, firstTime):
        self.activeLp = True
        self.editLevel = 2
        self.type = None
        self.center = None
        self.radius = None
        self.active = False
        self.initPoints = []
        self.points = []
        self.circlePos = None
        self.counter = 0
        self.filterCut = 5000
        if firstTime:
            self.step = 1
            self.lpx = BiquadLP()
            self.lpy = BiquadLP()

    def getAttributes(self):
        return {'activeLp': self.activeLp, 
                'editLevel': self.editLevel, 
                'type': self.type, 
                'center': self.center, 
                'radius': self.radius, 
                'active': self.active, 
                'circlePos': self.circlePos, 
                'counter': self.counter,
                'filterCut': self.filterCut,
                'points': self.getPoints()}

    def setAttributes(self, dict):
        self.activeLp = dict['activeLp']
        self.editLevel = dict['editLevel']
        self.type = dict['type']
        self.center = dict['center']
        self.radius = dict['radius']
        self.active = dict['active']
        self.circlePos = dict['circlePos']
        self.counter = dict['counter']
        self.filterCut = dict['filterCut']
        self.setPoints(dict['points'])

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

    def clear(self):
        self.__init__(False)

    def setActive(self, state):
        self.active = state

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

    def initCounter(self):
        self.counter = 0

    def clock(self):
        if self.points:
            self.circlePos = self.points[self.counter % len(self.points)]
            self.counter += self.step

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
        self.parent = parent
        self.numOfTrajectories(3)
        self.screenOffset = 2
        self.sndBitmap = None
        self.bitmapDict = {}
        self.closed = 0
        self.timeSpeed = 25
        self.step = 1
        self.oscilPeriod = 2
        self.oscilScaling = 1
        self.ymin = 0
        self.ymax = 1
        self.ymethod = 0
        self.altKey = False
        self.mode = trajTypes[0]
        self.SetColors(outline=(255,255,255), bg=(20,20,20), fill=(255,0,0), rect=(0,255,0), losa=(0,0,255), wave=(70,70,70))
        self.currentSize = self.GetSize()
    
        self.Bind(wx.EVT_LEFT_DOWN, self.MouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.MouseUp)
        self.Bind(wx.EVT_RIGHT_DOWN, self.deleteTraj)
        self.Bind(wx.EVT_MOTION, self.MouseMotion)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseEvent)
        self.startTimer()

    def OnEraseEvent(self, evt):
        pass

    def setCurrentSize(self, size):
        self.currentSize = size

    def OnResize(self, evt):
        w,h = self.GetSize()
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

    def getTimerSpeed(self):
        return self.timeSpeed

    def setStep(self, step):
        self.step = step

    def setTimerSpeed(self, speed):
        self.timeSpeed = speed
        if self.timer.IsRunning():
            self.stopTimer()
            self.startTimer()
        
    def startTimer(self):
        self.timer = wx.PyTimer(self.clock)
        self.timer.Start(self.timeSpeed)
        
    def stopTimer(self):
        self.timer.Stop()
        del self.timer

    def clock(self):
        for traj in self.getActiveTrajectories():
            traj.clock()
        #self.OnPaint(None)
        self.Refresh()

    def setYMin(self, ymin):
        self.ymin = ymin
        
    def setYMax(self, ymax):
        self.ymax = ymax
        
    def setYMethod(self, met):
        self.ymethod = met
                
    def setOscilPeriod(self, period):
        self.oscilPeriod = period

    def getOscilPeriod(self):
        return self.oscilPeriod

    def setOscilScaling(self, scaling):
        self.oscilScaling = scaling

    def getOscilScaling(self):
        return self.oscilScaling
        
    def numOfTrajectories(self, num):
        try:
            current = len(self.trajectories)
            if num < current:
                del self.trajectories[num-current:]
            elif num > current:    
                self.trajectories.extend([Trajectory(True) for i in range(num-current)])
            else:
                pass
        except:
            self.trajectories = [Trajectory(True) for i in range(num)]        
                
    def SetColors(self, outline, bg, fill, rect, losa, wave):
        self.outlinecolor = wx.Color(*outline)
        self.backgroundcolor = wx.Color(*bg)
        self.fillcolor = wx.Color(*fill)
        self.rectcolor = wx.Color(*rect)
        self.losacolor = wx.Color(*losa)
        self.wavecolor = wx.Color(*wave)
            
    def getValues(self):
        w,h = self.GetSize()
        w,h = float(w), float(h)
        vals = []
        for t in self.trajectories:
            if t.getPointPos() != None:
                x = t.getPointPos()[0]/w
                y = mapper(1-(t.getPointPos()[1]/h), 0, 1, self.ymin, self.ymax, self.ymethod)
                vals.append([x,y])
            else:
                vals.append([])
        return vals

    def setMode(self, mode):
        self.mode = trajTypes[mode]

    def setClosed(self, closed):
        self.closed = closed

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
     
    def OnKeyDown(self, evt):
        if evt.GetKeyCode() == wx.WXK_ALT:
            self.altKey = True

    def OnKeyUp(self, evt):
        if evt.GetKeyCode() == wx.WXK_ALT:
            self.altKey = False
            
    def MouseDown(self, evt):
        self.downPos = evt.GetPosition().Get()
        for t in self.getActiveTrajectories():
            if t.getInsideRect(self.downPos):
                if self.altKey:
                    for new_t in self.trajectories:
                        if not new_t.getActive():
                            self.selected = new_t
                            self.selected.setActive(True)
                            self.selected.setType(t.getType())
                            self.selected.lpx.reinit()
                            self.selected.lpy.reinit()
                            self.selected.activateLp(self.parent.lowpass)
                            self.selected.setEditionLevel(self.parent.editionLevel)
                            self.selected.setStep(self.step)
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
                self.traj.setStep(self.step)
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

    def MouseUp(self, evt):
        if self.HasCapture():
            if self.action == 'draw' and self.traj:
                if len(self.traj.getPoints()) <= 1:
                    self.traj.clear()
                    return
                if self.traj.getType() == 'free':
                    self.traj.addFinalPoint(self.clipPos(evt.GetPosition().Get()), self.closed)
                    if self.parent.fillPoints:
                        self.traj.fillPoints(self.closed)
                    self.traj.setInitPoints()
                elif self.traj.getType() == 'circle':
                    if self.parent.fillPoints:
                        self.traj.fillPoints(True)
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

            #self.OnPaint(None)      
            self.Refresh()  
            self.ReleaseMouse()
            self.parent.createTempFile()

    def MouseMotion(self, evt):
        if self.HasCapture() and evt.Dragging() and evt.LeftIsDown():
            if self.action == 'draw' and self.traj:
                if self.traj.getType() == 'free':
                    self.traj.addPoint(self.clipPos(evt.GetPosition().Get()))
                elif self.traj.getType() == 'line':
                    self.traj.points = []
                    self.traj.lpx.reinit()
                    self.traj.lpy.reinit()
                    x,y = self.clipPos(evt.GetPosition().Get())

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
                    halfR = int(round(r/2))
                    if halfR == 0: scaleR = 1
                    else: scaleR = 1./halfR
                    self.traj.points = []
                    self.traj.lpx.reinit()
                    self.traj.lpy.reinit()
                    if self.traj.getType() == 'circle':
                        for i in range(-halfR,halfR):
                            a = i * scaleR * r
                            x = math.cos(math.pi * i * scaleR) * r
                            y = math.sin(math.pi * i * scaleR) * r
                            self.traj.addCirclePoint((int(round(x + self.downPos[0])), int(round(y + self.downPos[1]))))
                    else:
                        for i in range(int(-halfR * self.oscilScaling), int(halfR * self.oscilScaling)):
                            a = i * scaleR * r
                            x = math.cos(math.pi * i * scaleR) * r
                            y = math.sin(math.pi * self.oscilPeriod * i * scaleR) * r
                            self.traj.addCirclePoint((int(round(x + self.downPos[0])), int(round(y + self.downPos[1]))))

            elif self.action == 'drag':
                if self.selected.getType() in ['free', 'line']:
                    x,y = evt.GetPosition()
                    offset = (self.downPos[0] - x, self.downPos[1] - y)
                    clipedOffset = self.clip(offset, self.extremeXs, self.extremeYs)
                    self.selected.move(clipedOffset)
                else:
                    x,y = self.clipPos(evt.GetPosition())
                    offset = (self.downPos[0] - x, self.downPos[1] - y)
                    center, clipedOffset = self.clipCircleMove(self.selected.getRadius(), self.curCenter, offset)
                    self.selected.setCenter(center)
                    self.selected.move(clipedOffset)

            elif self.action == 'rescale':
                Xlen = abs(self.selected.getCenter()[0] - evt.GetPosition()[0])
                Ylen = abs(self.selected.getCenter()[1] - evt.GetPosition()[1])
                self.selected.setRadius(self.clipCirclePos(math.sqrt( Xlen**2 + Ylen**2 ), self.selected.getCenter(), self.selected.getRadius()))
                r = self.selected.getRadius()
                halfR = int(round(r/2))
                if halfR == 0: scaleR = 1
                else: scaleR = 1./halfR
                self.selected.points = []
                self.traj.lpx.reinit()
                self.traj.lpy.reinit()
                if self.selected.getType() == 'circle':
                    for i in range(-halfR,halfR):
                        a = i * scaleR * r
                        x = math.cos(math.pi * i * scaleR) * r
                        y = math.sin(math.pi * i * scaleR) * r
                        self.selected.addCirclePoint((int(round(x + self.selected.getCenter()[0])), int(round(y + self.selected.getCenter()[1]))))
                else:
                    for i in range(int(-halfR * self.oscilScaling), int(halfR * self.oscilScaling)):
                        a = i * scaleR * r
                        x = math.cos(math.pi * i * scaleR) * r
                        y = math.sin(math.pi * self.oscilPeriod * i * scaleR) * r
                        self.selected.addCirclePoint((int(round(x + self.selected.getCenter()[0])), int(round(y + self.selected.getCenter()[1]))))
            elif self.action == 'edit':
                x,y = evt.GetPosition()
                offset = (self.downPos[0] - x, self.downPos[1] - y)
                self.selected.editTraj(self.pindex, offset)            
            self.Refresh()
    
    def OnPaint(self, evt):
        x,y = (0,0)
        w,h = self.GetSize()
        dc = wx.PaintDC(self)

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
                    dc.DrawCirclePoint(t.circlePos, 4)
                dc.DrawRoundedRectanglePointSize((t.getFirstPoint()[0],t.getFirstPoint()[1]), (10,10), 2)
                if t.getType() not in ['free', 'line']:
                    dc.SetBrush(wx.Brush(self.losacolor, wx.SOLID))
                    dc.SetPen(wx.Pen(self.losacolor, width=1, style=wx.SOLID))
                    dc.DrawRoundedRectanglePointSize((t.getLosangePoint()[0]-5,t.getLosangePoint()[1]-5), (10,10), 1)
 
        sendXYControls(self.getValues())
        evt.Skip()

    def clip(self, off, exXs, exYs):
        Xs = [p[0] for p in self.selected.getPoints()]
        minX, maxX = min(Xs), max(Xs)
        Ys = [p[1] for p in self.selected.getPoints()]
        minY, maxY = min(Ys), max(Ys)
        x,y = off
        sizex, sizey = self.GetSize()
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
        sizex, sizey = self.GetSize()
        offset = self.screenOffset      
        if x < offset: x = offset
        elif x > (sizex-offset): x = sizex - offset
        else: x = x 
        if y < offset: y = offset
        elif y > (sizey-offset): y = sizey - offset
        else: y = y
        return (x,y)

    def clipCirclePos(self, rad, center, lastRad):
        sizex, sizey = self.GetSize()
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
        sizex, sizey = self.GetSize()
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

    def analyse(self, file, chnls):
        self.file = file
        self.chnls = chnls
        splitSnd(file)
        for i in range(chnls):
            monofile = os.path.join(os.path.expanduser('~'), os.path.split(file)[1].rsplit('.',1)[0] + '-' + str(i) + '.aif')
            if systemPlatform == 'darwin':    
                cspipe3 = Popen('/usr/local/bin/csound -U envext -o "%s/anal%s" -w .001 "%s"' % (os.path.expanduser('~'),i,monofile), shell=True, stdin=PIPE)
            elif systemPlatform == 'win32':
                cspipe3 = Popen('start /REALTIME /WAIT csound -U envext -o "%s/anal%s" -w .001 "%s"' % (os.path.expanduser('~'),i,monofile), shell=True, stdin=PIPE)
            cspipe3.wait()  
            os.remove(os.path.join(os.path.expanduser('~'), monofile))      
        self.make_list()        

    def make_list(self):
        list = []
        for i in range(self.chnls):
            file = "%s/anal%s" % (os.path.expanduser('~'),i)
            f = open(file, "r")
            self.l = [li.strip('\n').split('\t') for li in f.readlines()]
            f.close()
            os.remove(file)
            list.append([[eval(i[0]), eval(i[1])] for i in self.l])
        #self.length = len(list[0])
        self.bitmapDict[self.file] = list
        self.list = list
        self.create_bitmap()

    def create_bitmap(self):
        size = self.GetSize()
        X = size[0]
        self.length = len(self.list[0])
        scalar = float(X) / (self.length - 1)
        self.sndBitmap = wx.EmptyBitmap(size[0], size[1])
        self.memory = wx.MemoryDC()
        self.memory.SelectObject(self.sndBitmap)
        # dc background  
        new_Y = size[1]  / float(len(self.list))
        l = []
        append = l.append
        for chan in range(len(self.list)):
            halfY = new_Y / 2
            off = new_Y * chan
            self.memory.SetBrush(wx.Brush(self.backgroundcolor))
            self.memory.DrawRectangle(0,0,size[0],size[1])
            self.memory.SetPen(wx.Pen('black', 1))
            self.memory.DrawLine(0,halfY+off,size[0],halfY+off)
            
            # draw waveform    
            self.memory.SetPen(wx.Pen(self.wavecolor, 1)) 
            if self.list[chan]:
                last = 0
                for i in range(X):
                    y = int(round(i / scalar))
                    val = int(((halfY * self.list[chan][y][1]) + last) / 2)
                    append((i,halfY+off,i,halfY+off+val))
                    append((i,halfY+off,i,halfY+off-val))
                    last = val
        self.memory.DrawLineList(l)
        self.memory.SelectObject(wx.NullBitmap)

class ControlPanel(wx.Panel):
    def __init__(self, parent, surface):
        wx.Panel.__init__(self, parent, -1)

        self.parent = parent
        self.surface = surface
        
        self.type = 0
        self.numTraj = 3
        self.linLogSqrt = 0
        self.sndPath = None

        box = wx.BoxSizer(wx.VERTICAL)

        typeBox = wx.BoxSizer(wx.HORIZONTAL)

        box.Add(wx.StaticText(self, -1, "Trajectories"), 0, wx.CENTER|wx.TOP, 3)

        popupBox = wx.BoxSizer(wx.VERTICAL)
        popupBox.Add(wx.StaticText(self, -1, "Type"), 0, wx.CENTER|wx.ALL, 2)
        self.trajType = wx.Choice(self, -1, choices = ['Free', 'Circle', 'Oscil', 'Line'])
        popupBox.Add(self.trajType)
        typeBox.Add(popupBox, 0, wx.RIGHT, 5)

        popup2Box = wx.BoxSizer(wx.VERTICAL)
        popup2Box.Add(wx.StaticText(self, -1, "Max"), 0, wx.CENTER|wx.ALL, 2)
        self.trajMax = wx.Choice(self, -1, choices = ['1', '2', '3', '4', '5', '6', '7', '8'])
        self.trajMax.SetSelection(2)
        popup2Box.Add(self.trajMax)
        typeBox.Add(popup2Box, 0, wx.RIGHT, 5)
        
        self.closedToggle = wx.ToggleButton(self, -1, 'Closed', size=(50,20))
        typeBox.Add(self.closedToggle, 0, wx.TOP, 21 )

        box.Add(typeBox, 0, wx.ALL, 5)

        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)

        box.Add(wx.StaticText(self, -1, "Drawing parameters"), 0, wx.CENTER|wx.TOP, 5)

        box.Add(wx.StaticText(self, -1, "Lowpass cutoff"), 0, wx.LEFT|wx.TOP, 5)
        cutoffBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_cutoff = wx.Slider( self, 102, 50, 1, 150, size=(150, -1), style=wx.SL_HORIZONTAL)
        cutoffBox.Add(self.sl_cutoff, 0, wx.RIGHT, 10)
        self.cutoffValue = wx.StaticText(self, -1, str(self.sl_cutoff.GetValue() * 100) + ' Hz')
        cutoffBox.Add(self.cutoffValue, 0, wx.RIGHT, 10)
        box.Add(cutoffBox, 0, wx.ALL, 5)

        box.Add(wx.StaticText(self, -1, "Lowpass Q"), 0, wx.LEFT, 5)
        qBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_q = wx.Slider( self, 103, 0, 0, 1000, size=(150, -1), style=wx.SL_HORIZONTAL)
        qBox.Add(self.sl_q, 0, wx.RIGHT, 10)
        self.qValue = wx.StaticText(self, -1, str(self.sl_q.GetValue() + 0.5))
        qBox.Add(self.qValue, 0, wx.RIGHT, 10)
        box.Add(qBox, 0, wx.ALL, 5)
        
        box.Add(wx.StaticText(self, -1, "Oscil period"), 0, wx.LEFT, 5)
        periodBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_period = wx.Slider( self, -1, 40, 0, 100, size=(150, -1), style=wx.SL_HORIZONTAL)
        periodBox.Add(self.sl_period, 0, wx.RIGHT, 10)
        self.periodValue = wx.StaticText(self, -1, str(self.sl_period.GetValue() * 0.05))
        self.sl_period.Disable()
        periodBox.Add(self.periodValue, 0, wx.RIGHT, 10)
        box.Add(periodBox, 0, wx.ALL, 5)

        box.Add(wx.StaticText(self, -1, "Oscil scaling"), 0, wx.LEFT, 5)
        scalingBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_scaling = wx.Slider( self, -1, 100, 0, 400, size=(150, -1), style=wx.SL_HORIZONTAL)
        scalingBox.Add(self.sl_scaling, 0, wx.RIGHT, 10)
        self.scalingValue = wx.StaticText(self, -1, str(self.sl_scaling.GetValue() * 0.01))
        self.sl_scaling.Disable()
        scalingBox.Add(self.scalingValue, 0, wx.RIGHT, 10)
        box.Add(scalingBox, 0, wx.ALL, 5)
        
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)
        
        box.Add(wx.StaticText(self, -1, "Playback parameters"), 0, wx.CENTER|wx.TOP, 5)
        
        box.Add(wx.StaticText(self, -1, "Timer speed"), 0, wx.LEFT|wx.TOP, 5)
        speedBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_speed = wx.Slider( self, 100, 25, 5, 250, size=(150, -1), style=wx.SL_HORIZONTAL)
        speedBox.Add(self.sl_speed, 0, wx.RIGHT, 10)
        self.speedValue = wx.StaticText(self, -1, str(self.sl_speed.GetValue()) + ' ms')
        speedBox.Add(self.speedValue, 0, wx.RIGHT, 10)
        box.Add(speedBox, 0, wx.ALL, 5)

        box.Add(wx.StaticText(self, -1, "Point step"), 0, wx.LEFT, 5)
        stepBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_step = wx.Slider( self, 101, 1, 1, 50, size=(150, -1), style=wx.SL_HORIZONTAL)
        stepBox.Add(self.sl_step, 0, wx.RIGHT, 10)
        self.stepValue = wx.StaticText(self, -1, str(self.sl_step.GetValue()))
        stepBox.Add(self.stepValue, 0, wx.RIGHT, 10)
        box.Add(stepBox, 0, wx.ALL, 5)

        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)

        self.b_openFx = wx.Button(self, -1, "Open FX window")
        box.Add(self.b_openFx, 0, wx.CENTER|wx.ALL, 10)

        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)

        soundBox = wx.BoxSizer(wx.HORIZONTAL)
        self.b_loadSnd = wx.Button(self, -1, "Load sound")
        soundBox.Add(self.b_loadSnd, 0, wx.ALL, 11)
        self.tog_audio = wx.ToggleButton(self, -1, "Start Audio", size=(80,20))
        soundBox.Add(self.tog_audio, 0, wx.TOP | wx.LEFT, 12)
        box.Add(soundBox, 0, wx.ALL, 5)

        box.Add(wx.StaticText(self, -1, "Record to disk"), 0, wx.CENTER, 5)
        recBox = wx.BoxSizer(wx.HORIZONTAL)
        recBox.Add(wx.StaticText(self, -1, "File: "), 0, wx.TOP, 4)
        self.tx_output = wx.TextCtrl( self, -1, "snd", size=(120, -1))
        recBox.Add(self.tx_output, 0, wx.RIGHT, 12)
        self.tog_record = wx.ToggleButton(self, -1, "Start", size=(50,20))
        self.tog_record.Disable()
        recBox.Add(self.tog_record, 0, wx.TOP, 2)
        box.Add(recBox, 0, wx.ALL, 5)


        self.Bind(wx.EVT_CHOICE, self.handleType, self.trajType)
        self.Bind(wx.EVT_CHOICE, self.handleMax, self.trajMax)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.handleClosed, self.closedToggle)
        self.Bind(wx.EVT_SLIDER, self.handlePeriod, self.sl_period)
        self.Bind(wx.EVT_SLIDER, self.handleScaling, self.sl_scaling)
        self.Bind(wx.EVT_SLIDER, self.handleTimer, self.sl_speed)
        self.Bind(wx.EVT_SLIDER, self.handleStep, self.sl_step)
        self.Bind(wx.EVT_SLIDER, self.handleCutoff, self.sl_cutoff)
        self.Bind(wx.EVT_SLIDER, self.handleQ, self.sl_q)
        self.Bind(wx.EVT_BUTTON, self.handleOpenFx, self.b_openFx)
        self.Bind(wx.EVT_BUTTON, self.handleLoad, self.b_loadSnd)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.handleAudio, self.tog_audio)
        self.tx_output.Bind(wx.EVT_CHAR, self.handleOutput)        
        self.Bind(wx.EVT_TOGGLEBUTTON, self.handleRecord, self.tog_record)

        self.SetSizer(box)

    def handleType(self, event):
        self.type = event.GetInt()
        self.surface.setMode(self.type)
        self.checkEnableWidgets()

    def checkEnableWidgets(self):
        if self.type == 0:
            self.closedToggle.Enable()
        else:
            self.closedToggle.Disable()
        if self.type == 2:
            self.sl_period.Enable()
            self.sl_scaling.Enable()
        else:
            self.sl_period.Disable()
            self.sl_scaling.Disable()

    def getType(self):
        return self.type

    def setType(self, type):
        self.trajType.SetSelection(type)
        self.type = type
        self.surface.setMode(type)
        self.checkEnableWidgets()
       
    def handleMax(self, event):
        self.numTraj = event.GetInt() + 1
        self.surface.numOfTrajectories(self.numTraj)
        
    def getMax(self):
        return self.numTraj

    def setMax(self, max):
        self.numTraj = max
        self.trajMax.SetSelection(max-1)
        self.surface.numOfTrajectories(max)

    def handleClosed(self, event):
        self.surface.setClosed(event.GetInt())

    def getClosed(self):
        return self.closedToggle.GetValue()

    def setClosed(self, closed):
        self.closedToggle.SetValue(closed)
        self.surface.setClosed(closed)

    def handleCutoff(self, event):
        for traj in self.surface.getAllTrajectories():
            traj.setFilterFreq(event.GetInt() * 100)
            self.cutoffValue.SetLabel(str(event.GetInt() * 100) + ' Hz')

    def getCutoff(self):
        return self.sl_cutoff.GetValue() * 100

    def setCutoff(self, cutoff):
        self.sl_cutoff.SetValue(int(cutoff * 0.01))
        for traj in self.surface.getAllTrajectories():
            traj.setFilterFreq(cutoff)
            self.cutoffValue.SetLabel(str(cutoff) + ' Hz')

    def handleQ(self, event):
        for traj in self.surface.getAllTrajectories():
            traj.setFilterQ(event.GetInt() + 0.5)
            self.qValue.SetLabel(str(event.GetInt() + 0.5))

    def getQ(self):
        return self.sl_q.GetValue() + 0.5

    def setQ(self, q):
        self.sl_q.SetValue(int(q - 0.5))  
        for traj in self.surface.getAllTrajectories():
            traj.setFilterQ(q)
            self.qValue.SetLabel(str(q))
      
    def handlePeriod(self, event):
        self.surface.setOscilPeriod(event.GetInt() * 0.05)
        self.periodValue.SetLabel(str(event.GetInt() * 0.05))

    def getPeriod(self):
        return self.surface.getOscilPeriod()

    def setPeriod(self, period):
        self.sl_period.SetValue(int(period * 20))
        self.periodValue.SetLabel(str(period))
        self.surface.setOscilPeriod(period)

    def handleScaling(self, event):
        self.surface.setOscilScaling(event.GetInt() * 0.01)
        self.scalingValue.SetLabel(str(event.GetInt() * 0.01))

    def getScaling(self):
        return self.surface.getOscilScaling()

    def setScaling(self, scaling):
        self.sl_scaling.SetValue(int(scaling * 100))
        self.scalingValue.SetLabel(str(scaling))
        self.surface.setOscilScaling(scaling)

    def handleTimer(self, event):
        self.surface.setTimerSpeed(event.GetInt())
        self.speedValue.SetLabel(str(event.GetInt()) + ' ms')

    def getTimer(self):
        return self.surface.getTimerSpeed()

    def setTimer(self, time):
        self.sl_speed.SetValue(time)
        self.surface.setTimerSpeed(time)
        self.speedValue.SetLabel(str(time) + ' ms')
        
    def handleStep(self, event):
        self.surface.setStep(event.GetInt())
        for traj in self.surface.getAllTrajectories():
            traj.setStep(event.GetInt())
            self.stepValue.SetLabel(str(event.GetInt()))

    def getStep(self):
        return self.sl_step.GetValue()

    def setStep(self, step):
        self.surface.setStep(step)
        self.sl_step.SetValue(step)
        for traj in self.surface.getAllTrajectories():
            traj.setStep(step)
            self.stepValue.SetLabel(str(step))

    def handleOpenFx(self, event):
        self.parent.openFxWindow()
            
    def handleLoad(self, event):
        dlg = wx.FileDialog(self, message="Choose a sound file",
                            defaultDir=os.path.expanduser('~'), 
                            defaultFile="",
                            wildcard="AIFF file |*.aif;*.aiff;*.aifc;*.AIF;*.AIFF;*.Aif;*.Aiff|" \
                                     "Wave file |*.wav;*.wave;*.WAV;*.WAVE;*.Wav;*.Wave",
                            style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            sndPath = dlg.GetPath()
        dlg.Destroy()
        self.loadSound(sndPath)

    def loadSound(self, sndPath):
        self.sndPath = sndPath
        if self.sndPath:
            if os.path.isfile(self.sndPath):
                chnls, samprate, dur = soundInfo(self.sndPath)
                self.sndDur = dur
                self.chnls = chnls
                self.sndInfoStr = 'Loaded sound: %s,    Sr: %s Hz,    Channels: %s,    Duration: %s sec' % (self.sndPath, samprate, chnls, dur)
                if self.parent.draw:
                    if not self.sndPath in self.surface.bitmapDict.keys():
                        self.parent.log("Drawing waveform...")
                        self.surface.analyse(self.sndPath, self.chnls)
                    else:
                        self.surface.list = self.surface.bitmapDict[self.sndPath]
                        self.surface.create_bitmap()
                self.logSndInfo()

    def drawWaveform(self):
        if self.surface.sndBitmap and self.parent.draw:
            self.surface.create_bitmap()

    def handleAudio(self, event):
        if event.GetInt() == 1:
            if not self.sndPath:
                self.parent.log('*** No sound loaded! ***')
                self.tog_audio.SetValue(0)
            else:    
                self.tog_audio.SetLabel('Stop audio')
                self.b_loadSnd.Disable()
                self.trajMax.Disable()
                self.tx_output.Disable()
                self.tog_record.Enable()
                for t in self.surface.getAllTrajectories():
                    t.initCounter()
                args = self.parent.moduleFrames[self.parent.currentModule].getFixedValues()
                startAudio(self.numTraj, self.sndPath, self.parent.audioDriver, self.tx_output.GetValue(), self.parent.currentModule, *args)
                if self.parent.currentModule in ['FFTReader','FFTAdsyn', 'FFTRingMod', 'FMCrossSynth']:
                    self.parent.log('FFT Buffering...')
                    wx.CallLater(self.sndDur * 1000, self.logSndInfo)
        else:    
            self.tog_audio.SetLabel('Start audio')
            self.b_loadSnd.Enable()
            self.trajMax.Enable()
            self.tx_output.Enable()
            self.tog_record.SetValue(0)
            self.tog_record.SetLabel('Start')
            self.tog_record.Disable()
            stopAudio()
        self.parent.moduleFrames[self.parent.currentModule].activateWidgets(event.GetInt())

    def handleOutput(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_TAB or key == wx.WXK_RETURN:
            self.surface.SetFocus()
        event.Skip()
                
    def handleRecord(self, event):
        if event.GetInt() == 1:
            self.tog_record.SetLabel('Stop')
        else:
            self.tog_record.SetLabel('Start')
        sendRecord()        

    def logSndInfo(self):
        self.parent.log(self.sndInfoStr)
                   
class MainFrame(wx.Frame):
    def __init__(self, parent, id, pos, size, file):
        wx.Frame.__init__(self, parent, id, "", pos, size)

        self.currentFile = None
        self.temps = []
        self.draw = True
        self.lowpass = True
        self.fillPoints = True
        self.editionLevels = [2, 4, 8, 12, 16, 24, 32, 50]
        self.editionLevel = 2
        self.audioDriver = None
        self.modules = ['Granulator', 'FFTReader', 'FFTAdsyn', 'FFTRingMod', 'FMCrossSynth', 'AutoModulation']
        self.moduleFrames = {}
        self.recall = self.undos = 0

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseEvent)

        self.Bind(wx.EVT_SIZE, self.OnResize)        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        if wx.Platform == '__WXMAC__':
            self.MacSetMetalAppearance(True)
        self.status = wx.StatusBar(self, -1)
        self.SetStatusBar(self.status)

        menuBar = wx.MenuBar()
        self.menu = wx.Menu()
        self.menu.Append(1, "Open...\tCtrl+O")
        self.Bind(wx.EVT_MENU, self.handleOpen, id=1)
        self.menu.Append(2, "Save\tCtrl+S")
        self.Bind(wx.EVT_MENU, self.handleSave, id=2)
        self.menu.Append(3, "Save as...\tShift+Ctrl+S")
        self.Bind(wx.EVT_MENU, self.handleSaveAs, id=3)
        menuBar.Append(self.menu, "&File")

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
        menuBar.Append(self.menu1, "&Drawing")

        self.menu2 = wx.Menu()
        menuBar.Append(self.menu2, "&Audio Drivers")

        self.menu3 = wx.Menu()
        for i, module in enumerate(self.modules):
            menuId = 300 + i
            self.menu3.Append(menuId, module + "\tCtrl+%d" % (i+1) , "", wx.ITEM_RADIO)
            self.Bind(wx.EVT_MENU, self.handleModules, id=menuId)
            if i == 0:
                self.menu3.Check(menuId, True)
                self.currentModule = self.modules[i]
        exList = os.listdir(os.path.join(RESOURCES_PATH, 'examples'))
        exList = [f for f in exList if f[-3:] == '.sg']
        self.subMenu3 = wx.Menu()
        for i, f in enumerate(exList):
            self.subMenu3.Append(3000+i, f)
            self.Bind(wx.EVT_MENU, self.handleExamples, id=3000+i)
        self.menu3.AppendMenu(menuId+1, "Examples", self.subMenu3)
        menuBar.Append(self.menu3, "&Modules")

        self.SetMenuBar(menuBar)
        
        mainBox = wx.BoxSizer(wx.HORIZONTAL)
        self.panel = DrawingSurface(self)
        self.controls = ControlPanel(self, self.panel)
        mainBox.Add(self.panel, 1, wx.EXPAND, 5)
        mainBox.Add(self.controls, 0, wx.EXPAND, 5)
        self.SetSizer(mainBox)

        self.SetTitle(self.currentModule)

        self.SetMinSize((-1,580))

        self.Show()

        wx.CallAfter(self.check)
        
        self.granulatorControls = GranulatorFrame(self, self.panel, sendControl)
        self.moduleFrames['Granulator'] = self.granulatorControls
        self.fftreaderControls = FFTReaderFrame(self, self.panel, sendControl)
        self.moduleFrames['FFTReader'] = self.fftreaderControls
        self.fftringmodControls = FFTRingModFrame(self, self.panel, sendControl)
        self.moduleFrames['FFTRingMod'] = self.fftringmodControls
        self.fftadsynControls = FFTAdsynFrame(self, self.panel, sendControl)
        self.moduleFrames['FFTAdsyn'] = self.fftadsynControls
        self.automodulationControls = AutoModulationFrame(self, self.panel, sendControl)
        self.moduleFrames['AutoModulation'] = self.automodulationControls
        self.fmcrosssynthControls = FMCrossSynthFrame(self, self.panel, sendControl)
        self.moduleFrames['FMCrossSynth'] = self.fmcrosssynthControls
        
        self.createInitTempFile()

        if file:
            self.loadFile(file)

    def OnEraseEvent(self, evt):
        pass
            
    def check(self):
        self.status.SetStatusText('Scanning audio drivers...')
        self.driversList, selected = checkForDrivers()
        
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
                    self.panel.analyse(self.controls.sndPath, self.controls.chnls)

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
            self.controls.sl_cutoff.Enable()
            self.controls.sl_q.Enable()
        else:
            self.controls.sl_cutoff.Disable()
            self.controls.sl_q.Disable()

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
        self.audioDriver = menuId - 200

    def handleModules(self, evt):
        menuId = evt.GetId()
        self.checkModules(menuId-300)

    def setModules(self, module):
        ind = self.modules.index(module)
        self.menu3.Check(ind+300, True)
        self.checkModules(ind)

    def checkModules(self, menuId):
        if self.moduleFrames[self.currentModule].IsShown():
            self.moduleFrames[self.currentModule].Show(False)
        self.currentModule = self.modules[menuId]
        self.SetTitle(self.currentModule)
        
    def openFxWindow(self):
        self.moduleFrames[self.currentModule].SetTitle(self.currentModule + ' controls')
        self.moduleFrames[self.currentModule].Show()

    def OnResize(self, evt):
        self.controls.drawWaveform()
        evt.Skip()

    def handleUndo(self, evt):
        self.recallTempFile(evt.GetId())

    def handleExamples(self, evt):
        self.loadFile(os.path.join(RESOURCES_PATH, 'examples', self.subMenu3.GetLabel(evt.GetId())))

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

    def handleSave(self, evt):
        if self.currentFile:
            self.saveFile(self.currentFile)
        else:
            self.handleSaveAs(None)

    def handleSaveAs(self, evt):
        dlg = wx.FileDialog(self, message="Save file as ...", 
                            defaultDir=os.path.expanduser('~'),
                            defaultFile=self.currentModule + ".sg", 
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
        saveDict = {}

        ### Main Frame ###
        saveDict['MainFrame'] = {}
        saveDict['MainFrame']['draw'] = self.draw
        saveDict['MainFrame']['lowpass'] = self.lowpass
        saveDict['MainFrame']['fillPoints'] = self.fillPoints
        saveDict['MainFrame']['editionLevel'] = self.editionLevel
        saveDict['MainFrame']['currentModule'] = self.currentModule
        saveDict['MainFrame']['size'] = (self.panel.GetSize()[0], self.panel.GetSize()[1])

        ### Controls Frame ###
        saveDict['ControlFrame'] = self.moduleFrames[self.currentModule].save()

        ### Control Panel ###
        saveDict['ControlPanel'] = {}
        saveDict['ControlPanel']['type'] = self.controls.getType()
        saveDict['ControlPanel']['max'] = self.controls.getMax()
        saveDict['ControlPanel']['closed'] = self.controls.getClosed()
        saveDict['ControlPanel']['cutoff'] = self.controls.getCutoff()
        saveDict['ControlPanel']['q'] = self.controls.getQ()
        saveDict['ControlPanel']['period'] = self.controls.getPeriod()
        saveDict['ControlPanel']['scaling'] = self.controls.getScaling()
        saveDict['ControlPanel']['timer'] = self.controls.getTimer()
        saveDict['ControlPanel']['step'] = self.controls.getStep()
        saveDict['ControlPanel']['sound'] = self.controls.sndPath

        ### Trajectories ###
        saveDict['Trajectories'] = {}
        for i, t in enumerate(self.panel.getAllTrajectories()):
            saveDict['Trajectories'][str(i)] = t.getAttributes()
        msg = xmlrpclib.dumps((saveDict, ), allow_none=True)
        f = open(path, 'w')
        f.write(msg)
        f.close()

        self.SetTitle(os.path.split(self.currentFile)[1] + ' - ' + self.currentModule)

    def loadFile(self, path):
        self.currentFile = path
        f = open(path, 'r')
        msg = f.read()
        f.close()
        result, method = xmlrpclib.loads(msg)
        dict = result[0]
        ### Main Frame ###
        self.setDraw(dict['MainFrame']['draw'])
        self.setLowpass(dict['MainFrame']['lowpass'])
        self.setFillPoints(dict['MainFrame']['fillPoints'])
        self.setEditionLevel(dict['MainFrame']['editionLevel'])
        self.setModules(dict['MainFrame']['currentModule'])

        ### Control Frame ###
        self.moduleFrames[self.currentModule].load(dict['ControlFrame'])

        ### Control panel ###
        self.controls.setType(dict['ControlPanel']['type'])
        self.controls.setMax(dict['ControlPanel']['max'])
        self.controls.setClosed(dict['ControlPanel']['closed'])
        self.controls.setCutoff(dict['ControlPanel']['cutoff'])
        self.controls.setQ(dict['ControlPanel']['q'])
        self.controls.setPeriod(dict['ControlPanel']['period'])
        self.controls.setScaling(dict['ControlPanel']['scaling'])
        self.controls.setTimer(dict['ControlPanel']['timer'])
        self.controls.setStep(dict['ControlPanel']['step'])
        self.controls.loadSound(dict['ControlPanel']['sound'])

        ### Trajectories ###
        for i, t in enumerate(self.panel.getAllTrajectories()):
            t.setAttributes(dict['Trajectories'][str(i)])

        self.panel.setCurrentSize(dict['MainFrame']['size'])
        self.panel.OnResize(None)

        self.SetTitle(os.path.split(self.currentFile)[1] + ' - ' + self.currentModule)

    def createInitTempFile(self):
        handle, path =  tempfile.mkstemp()
        temp = open(path, 'w')
        for t in self.panel.getAllTrajectories():
            temp.write(str(t.getAttributes()) + '\n')
        temp.close()
        self.temps.insert(0, path)

    def createTempFile(self):
        handle, path =  tempfile.mkstemp()
        temp = open(path, 'w')
        for t in self.panel.getAllTrajectories():
            temp.write(str(t.getAttributes()) + '\n')
        temp.close()
        self.temps.insert(0, path)
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
            f = open(self.temps[self.recall],'r')
            lines = f.readlines()
            f.close()
            for i, t in enumerate(self.panel.getAllTrajectories()):
                t.setAttributes(eval(lines[i]))
        if self.recall >= len(self.temps) - 1:
            self.menu1.Enable(110, False)
        else:
            self.menu1.Enable(110, True)
        if self.undos == 0:
            self.menu1.Enable(111, False)
        else:
            self.menu1.Enable(111, True) 
      
    def OnClose(self, evt):
        self.panel.stopTimer()
        stopCsound()
        for temp in self.temps:  
            print temp
            os.remove(temp)      
        self.Destroy()

    def log(self, text):
        self.status.SetStatusText(text)
              
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

    sys.setcheckinterval(0)
    app = wx.PySimpleApp()
    f = MainFrame(None, -1, pos=(20,20), size=(800,580), file=file)
    app.MainLoop()
