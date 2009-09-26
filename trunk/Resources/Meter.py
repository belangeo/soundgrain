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
import wx, math, os, sys
from Biquad import BiquadLP
from constants import *

class VuMeter(wx.Panel):
    def __init__(self, parent, size=(200,11)):
        wx.Panel.__init__(self, parent, -1, size=size)
        self.parent = parent
        self.SetMinSize((200,6))
        self.SetBackgroundColour("#000000")
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.old_nchnls = 2
        self.numSliders = 2
        self.SetSize((200, 5*self.numSliders+1))
        self.bitmap = wx.Bitmap(os.path.join(IMAGES_PATH, 'vu-metre.png'))
        self.backBitmap = wx.Bitmap(os.path.join(IMAGES_PATH, 'vu-metre-dark.png'))
        self.amplitude = [0] * self.numSliders

        self.Bind(wx.EVT_CLOSE, self.OnClose)   
        self.Bind(wx.EVT_SIZE, self.OnResize)   
 
    def OnResize(self, evt):
        self.setNumSliders(self.numSliders)

    def setNumSliders(self, numSliders):
        oldChnls = self.old_nchnls
        self.numSliders = numSliders
        self.amplitude = [0] * self.numSliders
        gap = (self.numSliders - oldChnls) * 5
        parentSize = self.parent.GetSize()
        if sys.platform == 'linux2':
            self.SetSize((200, 5*self.numSliders+1))
            self.SetMinSize((200, 5*self.numSliders+1))
            self.parent.SetSize((parentSize[0], parentSize[1]+gap))
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
        self.Refresh()    
        
    def OnPaint(self, event):
        w,h = self.GetSize()
        dc = wx.AutoBufferedPaintDC(self)
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
        self.Destroy()


    

