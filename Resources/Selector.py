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

class Selector(wx.Panel):
    def __init__(self, parent, size=(160,20), outFunction=None):
        wx.Panel.__init__(self, parent, -1, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.backgroundColour = wx.SystemSettings.GetColour(0)
        self.SetBackgroundColour(self.backgroundColour)
        self.parent = parent
        self.SetSize((160,20))
        self.SetMaxSize(self.GetSize())
        self.rectList = []
        for i in range(8):
            self.rectList.append(wx.Rect(i*20, 0, 20, self.GetSize()[1]))
        self.overs = [False] * 8
        self.oversWait = [True] * 8
        self.selected = 0
        self.outFunction = outFunction

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.MouseDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)

    def setOverWait(self, which):
        self.oversWait[which] = False

    def checkForOverReady(self, pos):
        for i, rec in enumerate(self.rectList):
            if not rec.Contains(pos):
                self.oversWait[i] = True
                        
    def OnMotion(self, event):
        pos = event.GetPosition()
        self.overs = [False] * 8
        for i, rec in enumerate(self.rectList):
            if rec.Contains(pos) and self.oversWait[i]:
                self.overs[i] = True
        self.checkForOverReady(pos)
        self.Refresh()
        event.Skip()

    def OnLeave(self, event):
        self.overs = [False] * 8
        self.oversWait = [True] * 8
        self.Refresh()

    def OnPaint(self, event):
        w,h = self.GetSize()
        dc = wx.AutoBufferedPaintDC(self)

        dc.SetBrush(wx.Brush(self.backgroundColour, wx.SOLID))
        dc.Clear()

        # Draw background
        dc.SetPen(wx.Pen("#555555", width=1, style=wx.SOLID))
        dc.DrawRectangle(0, 0, w, h)

        for i in range(self.parent.getMax()):
            if i == self.selected:
                dc.SetBrush(wx.Brush("#CCCCCC", wx.SOLID))
                dc.DrawRoundedRectangleRect(self.rectList[i], 2)
            dc.SetTextForeground("#000000")
            dc.DrawLabel(str(i+1), self.rectList[i], wx.ALIGN_CENTER)
            dc.SetBrush(wx.Brush(self.backgroundColour, wx.SOLID))

    def MouseDown(self, event):
        pos = event.GetPosition()
        for i, rec in enumerate(self.rectList):
            if rec.Contains(pos) and i < self.parent.getMax():
                self.selected = i
                self.setOverWait(i)
                break
        if self.outFunction:
            self.outFunction(self.selected)
        self.Refresh()
        event.Skip()

    def setSelected(self, selected):
        self.selected = selected
        self.Refresh()