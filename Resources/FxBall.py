#!/usr/bin/env python
# encoding: utf-8

import wx, math
from constants import *
from pyolib._wxwidgets import ControlSlider

class FxBallControls(wx.Frame):
    def __init__(self, parent, fxball, sg_audio, size=(270, 200)):
        title = "%s Controls" % {0: "Reverb", 1: "Delay", 2: "Disto", 3: "Waveguide", 4: "Ring Mod", 5: "Degrade", 6: "Harmonizer"}[fxball.getFx()]
        wx.Frame.__init__(self, parent, -1, title, size=size)
        self.parent = parent
        self.fxball = fxball
        self.sg_audio = sg_audio
        menuBar = wx.MenuBar()
        self.menu = wx.Menu()
        self.menu.Append(200, 'Close\tCtrl+W', "")
        menuBar.Append(self.menu, "&File")
        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_CLOSE, self.handleClose)
        self.Bind(wx.EVT_MENU, self.handleClose, id=200)

        self.panel = wx.Panel(self, -1)
        self.panel.SetBackgroundColour(BACKGROUND_COLOUR)
        self.box = wx.BoxSizer(wx.VERTICAL)

        sl1values = {   0: ["Feedback", 0, 1, .75, False], 
                        1: ["Delay", 0.01, 1, 0.25, False], 
                        2: ["Drive", 0, 1, .75, False], 
                        3: ["Frequency", 20, 500, 100, True], 
                        4: ["Frequency", 1, 1000, 100, True],
                        5: ["Bit Depth", 2, 32, 8, True],
                        6: ["Transposition", -12, 12, -7, False]
                    }[fxball.getFx()]
        text = wx.StaticText(self.panel, -1, sl1values[0])
        font, psize = text.GetFont(), text.GetFont().GetPointSize()
        if sys.platform == "win32":
            font.SetPointSize(psize-1)
        else:
            font.SetPointSize(psize-2)
        text.SetFont(font)
        self.box.Add(text, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        self.box.AddSpacer(2)
        self.slider1 = ControlSlider(self.panel, sl1values[1], sl1values[2], sl1values[3], log=sl1values[4], size=(250,16), outFunction=self.handleSlider1)
        self.box.Add(self.slider1, 0, wx.LEFT|wx.RIGHT, 10)

        sl2values = {   0: ["Cutoff", 100, 15000, 5000, True], 
                        1: ["Feedback", 0, 1, 0.5, False], 
                        2: ["Slope", 0, .99, .75, False], 
                        3: ["Fall time", 1, 60, 30, False], 
                        4: ["Ring vs Amp mod", 0, .5, 0, False],
                        5: ["SR Scale", 0.01, 1, 0.25, True],
                        6: ["Feedback", 0, 1, 0.25, False], 
                    }[fxball.getFx()]
        text = wx.StaticText(self.panel, -1, sl2values[0])
        text.SetFont(font)
        self.box.Add(text, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        self.box.AddSpacer(2)
        self.slider2 = ControlSlider(self.panel, sl2values[1], sl2values[2], sl2values[3], log=sl2values[4], size=(250,16), outFunction=self.handleSlider2)
        self.box.Add(self.slider2, 0, wx.LEFT|wx.RIGHT, 10)

        text = wx.StaticText(self.panel, -1, "Amplitude")
        text.SetFont(font)
        self.box.Add(text, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        self.box.AddSpacer(2)
        self.slider3 = ControlSlider(self.panel, 0, 2, 1, size=(250,16), outFunction=self.handleMul)
        self.box.Add(self.slider3, 0, wx.LEFT|wx.RIGHT, 10)

        text = wx.StaticText(self.panel, -1, "Pan")
        text.SetFont(font)
        self.box.Add(text, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        self.box.AddSpacer(2)
        self.slider4 = ControlSlider(self.panel, 0, 1, 0.5, size=(250,16), outFunction=self.handlePan)
        self.box.Add(self.slider4, 0, wx.LEFT|wx.RIGHT, 10)

        self.panel.SetSizerAndFit(self.box)

        self.Fit()
        self.SetMinSize(self.GetSize())
        self.SetMaxSize(self.GetSize())
        
    def handleClose(self, event):
        self.Show(False)

    def handleSlider1(self, val):
        self.sg_audio.handleFxSlider1(self.fxball.getFx(), self.fxball.getId(), val)

    def handleSlider2(self, val):
        self.sg_audio.handleFxSlider2(self.fxball.getFx(), self.fxball.getId(), val)
            
    def handleMul(self, val):
        self.sg_audio.handleFxMul(self.fxball.getId(), val)

    def handlePan(self, val):
        self.sg_audio.handleFxPan(self.fxball.getId(), val)

    def save(self):
        return {"slider1": self.slider1.GetValue(),
                "slider2": self.slider2.GetValue(),
                "slider3": self.slider3.GetValue(),
                "slider4": self.slider4.GetValue()}

    def load(self, dict):
        self.slider1.SetValue(dict["slider1"])
        self.handleSlider1(self.slider1.GetValue())
        self.slider2.SetValue(dict["slider2"])
        self.handleSlider2(self.slider2.GetValue())
        self.slider3.SetValue(dict["slider3"])
        self.handleMul(self.slider3.GetValue())
        self.slider4.SetValue(dict["slider4"])
        self.handlePan(self.slider4.GetValue())

def getColors(col, gradient):
    if col == 0:
        firstColor = wx.Colour(255,30,255)
        secondColor = wx.Colour(gradient,30,gradient)
    elif col == 1:
        firstColor = wx.Colour(30,255,255)
        secondColor = wx.Colour(30,gradient,gradient)
    elif col == 2:
        firstColor = wx.Colour(255,255,30)
        secondColor = wx.Colour(gradient,gradient,30)
    elif col == 3:
        firstColor = wx.Colour(30,255,30)
        secondColor = wx.Colour(30,gradient,30)
    elif col == 4:
        firstColor = wx.Colour(30,30,255)
        secondColor = wx.Colour(30,30,gradient)
    elif col == 5:
        firstColor = wx.Colour(255,30,30)
        secondColor = wx.Colour(gradient,30,30)
    elif col == 6:
        firstColor = wx.Colour(255,255,255)
        secondColor = wx.Colour(gradient,gradient,gradient)
    return firstColor, secondColor    
    
def GetRoundMaskBitmap(w, h, radius):
    maskColor = wx.Color(30,30,30)
    shownColor = wx.Color(29,29,29)
    b = wx.EmptyBitmap(w,h)
    dc = wx.MemoryDC(b)
    dc.SetPen(wx.Pen(maskColor, 1))
    dc.SetBrush(wx.Brush(maskColor))
    dc.DrawRectangle(0,0,w,h)
    dc.SetPen(wx.Pen(shownColor, 1, style=wx.TRANSPARENT))
    dc.SetBrush(wx.Brush(shownColor, wx.CROSSDIAG_HATCH))
    dc.DrawRoundedRectangle(0,0,w,h,radius)
    dc.SelectObject(wx.NullBitmap)
    b.SetMaskColour(shownColor)
    return b

def GetRoundBitmap(w, h, mask, col, gradient):
    firstColor, secondColor = getColors(col, gradient)
    maskColor = wx.Color(30,30,30)
    b = wx.EmptyBitmap(w,h)
    dc = wx.MemoryDC(b)
    dc.SetPen(wx.Pen(maskColor, 1))
    dc.SetBrush(wx.Brush(maskColor))
    dc.Clear()
    rec = wx.Rect(0, 0, w, h)  
    dc.GradientFillConcentric(rec, firstColor, secondColor, (w/2,h/2))
    dc.DrawBitmap(mask, rec[0], rec[1], True)
    dc.SelectObject(wx.NullBitmap)
    b.SetMaskColour(maskColor)
    return b

class FxBall():
    def __init__(self, fx, id, sg_audio, pos, size=64, gradient=30, fader=1.):
        self.fx = fx
        self.id = id
        self.pos = pos
        self.size, self.halfSize = size, size/2
        self._gradient = self.gradient = gradient
        self.fader = fader
        self._center = self.center = (self.pos[0]+self.halfSize, self.pos[1]+self.halfSize)
        self.setBitmaps(self.size, self.halfSize)

        self.controls = FxBallControls(None, self, sg_audio)

    def save(self):
        return {"fx": self.fx,
                "id": self.id,
                "pos": self.pos,
                "size": self.size,
                "gradient": self.gradient,
                "fader": self.fader,
                "controls": self.controls.save()}
                
    def load(self, dict):
        self.controls.load(dict)

    def setBitmaps(self, size, halfSize):
        self.mask = GetRoundMaskBitmap(size, size, halfSize)
        self.bit = GetRoundBitmap(size, size, self.mask, self.fx, self.gradient)

    def getFx(self):
        return self.fx

    def getId(self):
        return self.id

    def restoreGradient(self):
        self.gradient = self._gradient

    def restoreCenter(self):
        self.center = self._center

    def getCenter(self):
        return self.center

    def setCenter(self, c):
        self.center = c
        self.pos = (self.center[0]-self.halfSize, self.center[1]-self.halfSize)
        self.setBitmaps(self.size, self.halfSize)

    def getSize(self):
        return self.size

    def setSize(self, size):
        if size < 4:
            size = 4
        self.size, self.halfSize = size, size/2
        self.setBitmaps(self.size, self.halfSize)

    def setGradient(self, x):
        self._gradient = self.gradient + x
        if self._gradient > 255: self._gradient = 255
        elif self._gradient < 30: self._gradient = 30
        self.fader = 1. - ((self._gradient - 30) / 225.)
        self.bit = GetRoundBitmap(self.size, self.size, self.mask, self.fx, self._gradient)

    def resize(self, x):
        self.size, self.halfSize = x, x/2
        self._center = (self.pos[0]+self.halfSize, self.pos[1]+self.halfSize)
        self.setBitmaps(self.size, self.halfSize)

    def move(self, newpos):
        self.pos = (newpos[0]-self.halfSize, newpos[1]-self.halfSize)
        self._center = self.center = newpos

    def getInside(self, pos, small=False):
        x, y = self.center[0] - pos[0], self.center[1] - pos[1]
        hyp = math.sqrt(x*x+y*y)
        if small:
            return hyp < (self.halfSize*2/3)
        else:    
            return hyp < self.halfSize

    def getAmpValue(self, pos):
        x, y = self.center[0] - pos[0], self.center[1] - pos[1]
        hyp = math.sqrt(x*x+y*y)
        if hyp < self.halfSize:
            return pow((self.halfSize - (hyp * self.fader)) / self.halfSize, 2)
        else:
            return 0.0

    def openControls(self, pos):
        self.controls.SetPosition(pos)
        self.controls.Show()
