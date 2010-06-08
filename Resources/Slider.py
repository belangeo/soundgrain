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

import wx, sys, math
from constants import BACKGROUND_COLOUR

def interpFloat(t, v1, v2):
    "interpolator for a single value; interprets t in [0-1] between v1 and v2"
    return (v2-v1)*t + v1

def tFromValue(value, v1, v2):
    "returns a t (in range 0-1) given a value in the range v1 to v2"
    return float(value-v1)/(v2-v1)

def clamp(v, minv, maxv):
    "clamps a value within a range"
    if v<minv: v=minv
    if v> maxv: v=maxv
    return v

def toLog(t, v1, v2):
    return math.log10(t/v1) / math.log10(v2/v1)

def toExp(t, v1, v2):
    return math.pow(10, t * (math.log10(v2) - math.log10(v1)) + math.log10(v1))

POWOFTWO = {2:1, 4:2, 8:3, 16:4, 32:5, 64:6, 128:7, 256:8, 512:9, 1024:10, 2048:11, 4096:12, 8192:13, 16384:14, 32768:15, 65536:16}
def powOfTwo(x):
    return 2**x

def powOfTwoToInt(x):
    return POWOFTWO[x]
        
def GetRoundBitmap( w, h, r ):
    maskColor = wx.Color(0,0,0)
    shownColor = wx.Color(5,5,5)
    b = wx.EmptyBitmap(w,h)
    dc = wx.MemoryDC(b)
    dc.SetBrush(wx.Brush(maskColor))
    dc.DrawRectangle(0,0,w,h)
    dc.SetBrush(wx.Brush(shownColor))
    dc.SetPen(wx.Pen(shownColor))
    dc.DrawRoundedRectangle(0,0,w,h,r)
    dc.SelectObject(wx.NullBitmap)
    b.SetMaskColour(maskColor)
    return b

def GetRoundShape( w, h, r ):
    return wx.RegionFromBitmap( GetRoundBitmap(w,h,r) )

class ControlSlider(wx.Panel):
    def __init__(self, parent, minvalue, maxvalue, init=None, pos=(0,0), size=(200,16), log=False, outFunction=None, integer=False, powoftwo=False, backColour=None):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, pos=pos, size=size, style=wx.NO_BORDER | wx.WANTS_CHARS)
        self.parent = parent
        self.backgroundColour = BACKGROUND_COLOUR
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)  
        self.SetBackgroundColour(self.backgroundColour)
        self.SetMinSize(self.GetSize())
        self.knobSize = 40
        self.knobHalfSize = 20
        self.sliderHeight = 11
        self.outFunction = outFunction
        self.integer = integer
        self.log = log
        self.powoftwo = powoftwo
        if self.powoftwo:
            self.integer = True
            self.log = False
        self.SetRange(minvalue, maxvalue)
        self.borderWidth = 1
        self.selected = False
        self._enable = True
        self.new = ''
        if backColour: self.backColour = backColour
        else: self.backColour = "#444444"
        if init != None: 
            self.SetValue(init)
            self.init = init
        else: 
            self.SetValue(minvalue)
            self.init = minvalue
        self.clampPos()
        self.Bind(wx.EVT_LEFT_DOWN, self.MouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.MouseUp)
        self.Bind(wx.EVT_LEFT_DCLICK, self.DoubleClick)
        self.Bind(wx.EVT_MOTION, self.MouseMotion)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_KEY_DOWN, self.keyDown)
        self.Bind(wx.EVT_KILL_FOCUS, self.LooseFocus)
        self.createSliderBitmap()
        self.createKnobBitmap()

    def getMinValue(self):
        return self.minvalue

    def getMaxValue(self):
        return self.maxvalue

    def Enable(self):
        self._enable = True
        self.Refresh()

    def Disable(self):
        self._enable = False
        self.Refresh()
        
    def setSliderHeight(self, height):
        self.sliderHeight = height
        self.createSliderBitmap()
        self.createKnobBitmap()
        self.Refresh()

    def createSliderBitmap(self):
        w, h = self.GetSize()
        b = wx.EmptyBitmap(w,h)
        dc = wx.MemoryDC(b)
        dc.SetPen(wx.Pen(self.backgroundColour, width=1))
        dc.SetBrush(wx.Brush(self.backgroundColour))
        dc.DrawRectangle(0,0,w,h)
        dc.SetBrush(wx.Brush("#999999"))
        dc.SetPen(wx.Pen(self.backgroundColour, width=1))
        h2 = self.sliderHeight / 4
        dc.DrawRoundedRectangle(0,h2,w,self.sliderHeight,2)
        dc.SelectObject(wx.NullBitmap)
        b.SetMaskColour("#999999")
        self.sliderMask = b

    def createKnobBitmap(self):
        w, h = self.knobSize, self.GetSize()[1]
        b = wx.EmptyBitmap(w,h)
        dc = wx.MemoryDC(b)
        rec = wx.Rect(0, 0, w, h)
        dc.SetPen(wx.Pen(self.backgroundColour, width=1))
        dc.SetBrush(wx.Brush(self.backgroundColour))
        dc.DrawRectangleRect(rec)
        h2 = self.sliderHeight / 4
        rec = wx.Rect(0, h2, w, self.sliderHeight)
        dc.GradientFillLinear(rec, "#414753", "#99A7CC", wx.BOTTOM)
        dc.SetBrush(wx.Brush("#999999"))
        dc.DrawRoundedRectangle(0,0,w,h,2)
        dc.SelectObject(wx.NullBitmap)
        b.SetMaskColour("#999999")
        self.knobMask = b

    def getInit(self):
        return self.init

    def SetRange(self, minvalue, maxvalue):   
        self.minvalue = minvalue
        self.maxvalue = maxvalue

    def getRange(self):
        return [self.minvalue, self.maxvalue]

    def scale(self):
        inter = tFromValue(self.pos, self.knobHalfSize, self.GetSize()[0]-self.knobHalfSize)
        if not self.integer:
            return interpFloat(inter, self.minvalue, self.maxvalue)
        elif self.powoftwo:
            return powOfTwo(int(interpFloat(inter, self.minvalue, self.maxvalue)))    
        else:
            return int(interpFloat(inter, self.minvalue, self.maxvalue))

    def SetValue(self, value):
        if self.HasCapture():
            self.ReleaseMouse()
        if self.powoftwo:
            value = powOfTwoToInt(value)  
        value = clamp(value, self.minvalue, self.maxvalue)
        if self.log:
            t = toLog(value, self.minvalue, self.maxvalue)
            self.value = interpFloat(t, self.minvalue, self.maxvalue)
        else:
            t = tFromValue(value, self.minvalue, self.maxvalue)
            self.value = interpFloat(t, self.minvalue, self.maxvalue)
        if self.integer:
            self.value = int(self.value)
        if self.powoftwo:
            self.value = powOfTwo(self.value)    
        self.clampPos()
        self.selected = False
        self.Refresh()

    def GetValue(self):
        if self.log:
            t = tFromValue(self.value, self.minvalue, self.maxvalue)
            val = toExp(t, self.minvalue, self.maxvalue)
        else:
            val = self.value
        if self.integer:
            val = int(val)
        return val

    def LooseFocus(self, event):
        self.selected = False
        self.Refresh()

    def keyDown(self, event):
        if self.selected:
            char = ''
            if event.GetKeyCode() in range(324, 334):
                char = str(event.GetKeyCode() - 324)
            elif event.GetKeyCode() == 390:
                char = '-'
            elif event.GetKeyCode() == 391:
                char = '.'
            elif event.GetKeyCode() == wx.WXK_BACK:
                if self.new != '':
                    self.new = self.new[0:-1]
            elif event.GetKeyCode() < 256:
                char = chr(event.GetKeyCode())
            if char in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '-']:
                self.new += char
            elif event.GetKeyCode() in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
                self.SetValue(eval(self.new))
                self.new = ''
                self.selected = False
            self.Refresh()
 
    def MouseDown(self, evt):
        if evt.ShiftDown():
            self.DoubleClick(evt)
            return
        if self._enable:
            size = self.GetSize()
            self.pos = clamp(evt.GetPosition()[0], self.knobHalfSize, size[0]-self.knobHalfSize)
            self.value = self.scale()
            self.CaptureMouse()
            self.selected = False
            self.Refresh()
        evt.Skip()

    def MouseUp(self, evt):
        if self.HasCapture():
            self.ReleaseMouse()

    def DoubleClick(self, event):
        if self._enable:
            w, h = self.GetSize()
            pos = event.GetPosition()
            if wx.Rect(self.pos-self.knobHalfSize, 0, self.knobSize, h).Contains(pos):
                self.selected = True
            self.Refresh()
        event.Skip()
            
    def MouseMotion(self, evt):
        if self._enable:
            size = self.GetSize()
            if evt.Dragging() and evt.LeftIsDown():
                self.pos = clamp(evt.GetPosition()[0], self.knobHalfSize, size[0]-self.knobHalfSize)
                self.value = self.scale()
                self.selected = False
                self.Refresh()

    def OnResize(self, evt):
        self.createSliderBitmap()
        self.clampPos()    
        self.Refresh()

    def clampPos(self):
        size = self.GetSize()
        if self.powoftwo:
            val = powOfTwoToInt(self.value)
        else:
            val = self.value    
        self.pos = tFromValue(val, self.minvalue, self.maxvalue) * (size[0] - self.knobHalfSize) + self.knobHalfSize
        self.pos = clamp(self.pos, self.knobHalfSize, size[0]-self.knobHalfSize)
        
    def setbackColour(self, colour):
        self.backColour = colour

    def OnPaint(self, evt):
        w,h = self.GetSize()
        dc = wx.AutoBufferedPaintDC(self)

        dc.SetBrush(wx.Brush(self.backgroundColour, wx.SOLID))
        dc.Clear()

        # Draw background
        dc.SetPen(wx.Pen(self.backgroundColour, width=self.borderWidth, style=wx.SOLID))
        dc.DrawRectangle(0, 0, w, h)

        # Draw inner part
        if self._enable: sliderColour =  "#99A7CC"
        else: sliderColour = "#BBBBBB"
        h2 = self.sliderHeight / 4
        rec = wx.Rect(0, h2, w, self.sliderHeight)
        dc.GradientFillLinear(rec, "#646986", sliderColour, wx.BOTTOM)
        dc.DrawBitmap(self.sliderMask, 0, 0, True)

        # Draw knob
        if self._enable: knobColour = '#888888'
        else: knobColour = "#DDDDDD"
        rec = wx.Rect(self.pos-self.knobHalfSize, 0, self.knobSize, h)  
        dc.GradientFillLinear(rec, "#424864", knobColour, wx.RIGHT)
        dc.DrawBitmap(self.knobMask, rec[0], rec[1], True)
        
        if self.selected:
            rec2 = wx.Rect(self.pos-self.knobHalfSize, 0, self.knobSize, h)  
            dc.SetBrush(wx.Brush('#333333', wx.SOLID))
            dc.SetPen(wx.Pen('#333333', width=self.borderWidth, style=wx.SOLID))  
            dc.DrawRoundedRectangleRect(rec2, 3)

        if sys.platform in ['win32', 'linux2']:
            dc.SetFont(wx.Font(7, wx.ROMAN, wx.NORMAL, wx.NORMAL))
        else:    
            dc.SetFont(wx.Font(10, wx.ROMAN, wx.NORMAL, wx.NORMAL))

        # Draw text
        if self.selected and self.new:
            val = self.new
        else:
            if self.integer:
                val = '%d' % self.GetValue()
            else:
                val = '%.3f' % self.GetValue()
        if sys.platform == 'linux2':
            width = len(val) * (dc.GetCharWidth() - 3)
        else:
            width = len(val) * dc.GetCharWidth()
        dc.SetTextForeground('#FFFFFF')
        dc.DrawLabel(val, rec, wx.ALIGN_CENTER)

        # Send value
        if self.outFunction:
            self.outFunction(self.GetValue())

        evt.Skip()
