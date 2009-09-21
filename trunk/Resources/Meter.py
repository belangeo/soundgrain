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
import wx, math, threading, time, osc, random, os, sys
from Biquad import BiquadLP
from constants import *

class Listener(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.terminated = False
        self.amps = [0]*8
        self.t = 0

        #osc.init()
        self.inSocket = osc.createListener("127.0.0.1", 15001)
        osc.bind(self.monitor, "/monitor")

    def run(self):
        while not self.terminated:
            osc.getOSC(self.inSocket)
            time.sleep(.06)

    def monitor(self, *msg):
        self.amps = msg[0][2:]

    def getAmps(self):
        return self.amps

    def stop(self):
        self.terminated = True
        del self.inSocket

class VuMeter(wx.Panel):
    def __init__(self, parent, size=(200,11)):
        wx.Panel.__init__(self, parent, -1, size=size)
        self.parent = parent
        self.SetMinSize((200,6))
        self.SetBackgroundColour("#000000")
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.old_nchnls = 2
        self.numSliders = 2
        self.timeSpeed = 60
        self.SetSize((200, 5*self.numSliders+1))
        self.bitmap = wx.Bitmap(os.path.join(IMAGES_PATH, 'vu-metre.png'))
        self.backBitmap = wx.Bitmap(os.path.join(IMAGES_PATH, 'vu-metre-dark.png'))
        self.amplitude = [0] * self.numSliders
        self.listener = Listener()
        self.listener.start()

        self.Bind(wx.EVT_CLOSE, self.OnClose)   
        self.Bind(wx.EVT_SIZE, self.OnResize)   
 
        self.startTimer()

    def OnResize(self, evt):
        self.setNumSliders(self.numSliders)

    def startTimer(self):
        self.timer = wx.PyTimer(self.clock)
        self.timer.Start(self.timeSpeed)
        
    def stopTimer(self):
        self.timer.Stop()
        del self.timer

    def clock(self):
        self.setAmplitude([math.sqrt(amp) for amp in self.listener.getAmps()])
        self.Refresh()

    def setNumSliders(self, numSliders):
        oldChnls = self.old_nchnls
        self.numSliders = numSliders
        self.amplitude = [0] * self.numSliders
        gap = (self.numSliders - oldChnls) * 5
        parentSize = self.parent.GetSize()
        if sys.platform == 'linux2':
            self.SetMinSize((200, 5*self.numSliders+1))
            self.parent.SetMinSize((parentSize[0], parentSize[1]+gap))
        else:
            self.SetSize((200, 5*self.numSliders+1))
            self.parent.SetSize((parentSize[0], parentSize[1]+gap))
        self.Refresh()

    def setAmplitude(self, amplitudeList=[]):
        if amplitudeList[0] < 0: 
            return
        if not amplitudeList:
            self.amplitude = [0 for i in range(self.numSliders)]                
        else:
            self.amplitude = amplitudeList
        
    def OnPaint(self, event):
        w,h = self.GetSize()
        dc = wx.PaintDC(self)
        dc.SetBrush(wx.Brush("#000000"))
        dc.Clear()
        dc.DrawRectangle(0,0,w,h)
        for i in range(self.numSliders):
            width = int(self.amplitude[i] * w * 1.2)
            dc.DrawBitmap(self.backBitmap, 0, i*5)
            dc.SetClippingRegion(0, i*5, width, 5)
            dc.DrawBitmap(self.bitmap, 0, i*5)
            dc.DestroyClippingRegion()

    def OnClose(self, evt):
        self.stopTimer()
        self.listener.stop()
        self.Destroy()


    

