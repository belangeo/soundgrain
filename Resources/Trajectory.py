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
import wx
from math import sin, pi, sqrt, floor
from Resources.Biquad_Filter import BiquadLP

def chooseColour(i, numlines=24):
    def clip(x):
        val = int(x*255)
        if val < 0: val = 0
        elif val > 255: val = 255
        else: val = val
        return val

    def colour(i, numlines, sat, bright):        
        hue = (i / float(numlines)) * 180 + 15
        if sat == 0:
            r = g = b = val
        else:
            segment = floor(hue / 60) % 6
            fraction = hue / 60 - segment
            t1 = bright * (1 - sat)
            t2 = bright * (1 - (sat * fraction))
            t3 = bright * (1 - (sat * (1 - fraction)))
            if segment == 0:
                r, g, b = bright, t3, t1
            elif segment == 1:
                r, g, b = t2, bright, t1
            elif segment == 2:
                r, g, b = t1, bright, t3
            elif segment == 3:
                r, g, b = t1, t2, bright
            elif segment == 4:
                r, g, b = t3, t1, bright
            elif segment == 5:
                r, g, b = bright, t1, t2
        return wx.Colour(clip(r),clip(g),clip(b))

    labelColour = colour(i, numlines, 1, 1)
    objectColour = colour(i, numlines, .95, .85)

    return objectColour, labelColour

class Trajectory:
    def __init__(self, parent, label):
        self.parent = parent
        self.label = label
        self.id = int(self.label)-1
        self.colour, self.bordercolour = chooseColour(int(self.label)-1)
        self.pen = wx.Pen(self.colour, width=1, style=wx.SOLID)
        self.brush = wx.Brush(self.colour, style=wx.SOLID)
        self.circlePen = wx.Pen(self.colour, width=8, style=wx.SOLID)
        self.activeLp = True
        self.editLevel = 2
        self.timeSpeed = 25
        self.amplitude = 1
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
        self.transpo = 1

    def clear(self):
        self.type = None
        self.center = None
        self.radius = None
        self.setActive(False)
        self.initPoints = []
        self.points = []
        self.circlePos = None
        self.setTranspo(1.)

    def getAttributes(self):
        return {'activeLp': self.activeLp, 
                'editLevel': self.editLevel, 
                'timeSpeed': self.timeSpeed,
                'amplitude': self.amplitude,
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
        self.setAmplitude(dict.get('amplitude', 1.0))
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

    def setTranspo(self, x):
        self.transpo = x
        if self.id >= 0:
            self.parent.parent.sg_audio.setTranspo(self.id, self.transpo)
        
    def getTranspo(self):
        return self.transpo

    def getFreeze(self):
        return self.freeze

    def setFreeze(self, freeze):
        self.freeze = freeze

    def getLabel(self):
        return self.label

    def getId(self):
        return self.id

    def getColour(self):
        return self.colour

    def getPen(self):
        return self.pen

    def getBrush(self):
        return self.brush

    def getCirclePen(self):
        return self.circlePen

    def getBorderColour(self):
        return self.bordercolour

    def setTimeSpeed(self, speed):
        self.timeSpeed = speed
        if self.id >= 0:
            self.parent.parent.sg_audio.setMetroTime(self.id, speed * 0.001)

    def getTimeSpeed(self):
        return self.timeSpeed

    def setAmplitude(self, val):
        self.amplitude = val
        
    def getAmplitude(self):
        return self.amplitude
    
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
            self.parent.parent.sg_audio.setActive(self.id, 1)
        else:
            self.parent.parent.sg_audio.setActive(self.id, 0)
            
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
            
            if self.activeLp:
                p = (int(round(filllpx.filter(self.points[first][0]))), int(round(filllpy.filter(self.points[first][1]))))
            else: 
                p = (self.points[first][0], self.points[first][1])
            if not templist:
                templist.append(p)
            else:
                gate = self.removeMatch(templist, p)
                if gate:
                    templist.append(p)
            if step > 3:       
                xpt = self.points[first][0] + xdir * xscale
                ypt = self.points[first][1] + ydir * yscale
                if self.activeLp:
                    p = (int(round(filllpx.filter(xpt))),int(round(filllpy.filter(ypt))))
                else:
                    p = (xpt, ypt)    
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
