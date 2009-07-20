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
import wx, math, threading, time, osc, random
from Biquad import BiquadLP

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
            time.sleep(.05)

    def monitor(self, *msg):
        self.amps = msg[0][2:]

    def getAmps(self):
        return self.amps

    def stop(self):
        self.terminated = True
        del self.inSocket

class Peaks(wx.Panel):
    def __init__(self, parent, pos=(0,0), size=(-1,15)):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, pos=pos, size=size, style = wx.EXPAND)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.parent = parent
        self.numSliders = 2
        self.offset = 1
        self.peaks = [0]*self.numSliders
        self.SetColors(outline=(255,255,255), bg=(20,20,20), red=(255,0,0))
        self.currentSize = self.GetSizeTuple()

        self.Bind(wx.EVT_LEFT_DOWN, self.MouseDown)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnResize)

    def OnResize(self, evt):
        w,h = self.GetSizeTuple()
        cX, cY = self.currentSize[0], self.currentSize[1]
        self.currentSize = (w,h)
                                  
    def SetColors(self, outline, bg, red):
        self.outlinecolor = wx.Color(*outline)
        self.backgroundcolor = wx.Color(*bg)
        self.red = wx.Color(*red)

    def setPeak(self, num):
        self.peaks[num] = 1
        self.Refresh()

    def MouseDown(self, evt):
        pos = evt.GetPosition()  
        x,y = (0,0)
        off = self.offset
        w,h = self.GetSizeTuple()
        for i in range(self.numSliders):
            l = x + (w * (float(i) / self.numSliders)) + off
            r = (w * (1. / self.numSliders)) - (off * 2) # width
            if wx.Rect(l, 0, r, h).Contains(pos):
                self.peaks[i] = 0
                break
        self.Refresh()
        evt.Skip()

    def OnPaint(self, evt):
        x,y = (0,0)
        off = self.offset
        w,h = self.GetSizeTuple()
        dc = wx.AutoBufferedPaintDC(self)

        dc.SetBrush(wx.Brush(self.backgroundcolor, wx.SOLID))
        dc.Clear()
        
        dc.SetPen(wx.Pen(self.outlinecolor, width=1, style=wx.SOLID))
        dc.DrawRectangle(x, y, w, h)

        dc.SetBrush(wx.Brush(self.red, wx.SOLID))
        dc.SetPen(wx.Pen(self.red, width=1, style=wx.SOLID))

        for i in range(self.numSliders):
            if self.peaks[i]:
                l = x + (w * (float(i) / self.numSliders)) + off
                r = (w * (1. / self.numSliders)) - (off * 2) # width
                dc.DrawRoundedRectangle(l, 0, r, h, 1)
        evt.Skip()

class Meter(wx.Panel):
    def __init__(self, parent, pos=(0,0), size=wx.DefaultSize, func=None):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, pos=pos, size=size, style = wx.EXPAND)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.parent = parent
        self.function = func
        self.numSliders = 2
        self.biquad = [BiquadLP(freq=2000)]*self.numSliders
        self.offset = 1
        self.timeSpeed = 50
        self.count = 0
        self.amp = [0]*self.numSliders
        self.SetColors(outline=(255,255,255), bg=(20,20,20), red=(255,0,0), green=(0,255,0), yellow=(200,200,0))
        self.currentSize = self.GetSizeTuple()

        self.listener = Listener()
        self.listener.start()

        self.Bind(wx.EVT_CLOSE, self.OnClose)    
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.startTimer()

    def OnResize(self, evt):
        w,h = self.GetSizeTuple()
        cX, cY = self.currentSize[0], self.currentSize[1]
        self.currentSize = (w,h)
        
    def startTimer(self):
        self.timer = wx.PyTimer(self.clock)
        self.timer.Start(self.timeSpeed)
        
    def stopTimer(self):
        self.timer.Stop()
        del self.timer

    def clock(self):
        self.amp = [math.sqrt(amp) for amp in self.listener.getAmps()]
        for i in range(len(self.amp)):
            if self.amp[i] > 1:
                self.function(i)
        self.count += 1
        self.Refresh()
                                  
    def SetColors(self, outline, bg, red, green, yellow):
        self.outlinecolor = wx.Color(*outline)
        self.backgroundcolor = wx.Color(*bg)
        self.red = wx.Color(*red)
        self.green = wx.Color(*green)
        self.yellow = wx.Color(*yellow)
      
    def OnPaint(self, evt):
        x,y = (0,0)
        off = self.offset
        w,h = self.GetSizeTuple()
        dc = wx.AutoBufferedPaintDC(self)

        dc.SetBrush(wx.Brush(self.backgroundcolor, wx.SOLID))
        dc.Clear()
        
        dc.SetPen(wx.Pen(self.outlinecolor, width=1, style=wx.SOLID))
        dc.DrawRectangle(x, y, w, h)

        dc.SetBrush(wx.Brush(self.red, wx.SOLID))
        dc.SetPen(wx.Pen(self.red, width=1, style=wx.SOLID))

        for i in range(self.numSliders):
            l = x + (w * (float(i) / self.numSliders)) + off
            r = (w * (1. / self.numSliders)) - (off * 2) # width
            if self.amp[i] < .5:
                rect = wx.Rect(l, h-(h*self.amp[i]), r, h*self.amp[i])
                dc.GradientFillLinear(rect, self.green, self.green, wx.NORTH)
            elif self.amp[i] < .85:
                rect1 = wx.Rect(l, h-(h*.5), r, h*.5)
                rect2 = wx.Rect(l, h-(h*self.amp[i]), r, h*(self.amp[i]-.49))
                dc.GradientFillLinear(rect1, self.green, self.green, wx.NORTH)
                dc.GradientFillLinear(rect2, self.green, self.yellow, wx.NORTH)
            else:    
                rect1 = wx.Rect(l, h-(h*.5), r, h*.5)
                rect2 = wx.Rect(l, h-(h*.85), r, h*(.85-.49))
                rect3 = wx.Rect(l, h-(h*self.amp[i]), r, h*(self.amp[i]-.84))
                dc.GradientFillLinear(rect1, self.green, self.green, wx.NORTH)
                dc.GradientFillLinear(rect2, self.green, self.yellow, wx.NORTH)
                dc.GradientFillLinear(rect3, self.yellow, self.red, wx.NORTH)
        evt.Skip()

    def OnClose(self, evt):
        self.stopTimer()
        self.listener.stop()
        self.Destroy()

class VuMeter(wx.Panel):
    def __init__(self, parent, id=-1, size=(40,250)):
        wx.Panel.__init__(self, parent, id, size=size)
        mainBox = wx.BoxSizer(wx.VERTICAL)
        self.peaker = Peaks(self)
        mainBox.Add(self.peaker, 0, wx.EXPAND, 5)
        self.panel = Meter(self, func=self.peaker.setPeak)  
        mainBox.Add(self.panel, 1, wx.EXPAND, 5)
        self.SetSizer(mainBox)

    def setNumSliders(self, num):
        self.peaker.numSliders = num  
        self.peaker.peaks = [0]*num  
        self.panel.numSliders = num    

    def OnClose(self, evt):
        self.panel.OnClose(None)
        self.Destroy()

class MainFrame(wx.Frame):
    def __init__(self, parent, id, pos, size):
        wx.Frame.__init__(self, parent, id, "", pos, size)
        self.Bind(wx.EVT_CLOSE, self.OnClose)    
        self.pane = VuMeter(self, -1, size=(40,250))

    def OnClose(self, evt):
        self.pane.OnClose(None)
        self.Destroy()

if __name__ == '__main__':
    app = wx.PySimpleApp()
    f = MainFrame(None, id=-1, pos=(20,20), size=(40,250))
    f.Show()
    app.MainLoop()
    

