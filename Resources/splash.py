# encoding: utf-8
"""
Copyright 2009-2017 Olivier Belanger

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
import wx, sys, os
from .constants import *

def GetRoundBitmap(w, h, r=10):
    maskColour = wx.Colour(0,0,0)
    shownColour = wx.Colour(5,5,5)
    b = wx.Bitmap(w,h)
    dc = wx.MemoryDC(b)
    dc.SetBrush(wx.Brush(maskColour))
    dc.DrawRectangle(0,0,w,h)
    dc.SetBrush(wx.Brush(shownColour))
    dc.SetPen(wx.Pen(shownColour))
    dc.DrawCircle(w//2,h//2,w//2)
    dc.SelectObject(wx.NullBitmap)
    b.SetMaskColour(maskColour)
    return b

def GetRoundShape(w, h, r=10):
    if sys.version_info[0] < 3:
        return wx.RegionFromBitmap(GetRoundBitmap(w,h,r))
    else:
        return wx.Region(GetRoundBitmap(w,h,r))

class SoundGrainSplashScreen(wx.Frame):
    def __init__(self, parent, img, mainframe=None):
        display = wx.Display(0)
        size = display.GetGeometry()[2:]
        style = wx.FRAME_SHAPED|wx.BORDER_NONE|wx.FRAME_NO_TASKBAR|wx.STAY_ON_TOP
        wx.Frame.__init__(self, parent, -1, "", pos=(-1, size[1]//6), style=style)

        self.Bind(wx.EVT_PAINT, self.OnPaint)

        self.mainframe = mainframe
        image = wx.Image(os.path.join(img), wx.BITMAP_TYPE_PNG)
        if image.HasAlpha():
            # The PNG edge was matted against white before alpha was added.
            # Remove that matte to avoid a pale fringe around the black rim.
            pixels = bytearray(image.GetData())
            for index, alpha in enumerate(image.GetAlpha()):
                if alpha == 0:
                    pixels[index * 3:index * 3 + 3] = b'\x00\x00\x00'
                elif alpha < 255:
                    offset = index * 3
                    for channel in range(offset, offset + 3):
                        pixels[channel] = max(0, min(255,
                            (pixels[channel] - (255 - alpha)) * 255 // alpha))
            image.SetData(bytes(pixels))
        self.bmp = wx.Bitmap(image)
        self.w, self.h = self.bmp.GetWidth(), self.bmp.GetHeight()
        self.SetClientSize((self.w, self.h))

        if wx.Platform == "__WXGTK__":
            self.Bind(wx.EVT_WINDOW_CREATE, self.SetWindowShape)
        else:
            self.SetWindowShape()

        self.fc = wx.CallLater(3500, self.OnClose)

        geometry = display.GetGeometry()
        x = geometry.x + (geometry.width - self.w) // 2
        y = geometry.y + (geometry.height - self.h) // 2 if sys.platform == 'win32' else geometry.y + geometry.height // 6
        self.SetPosition((x, y))

        wx.CallAfter(self.Show)

    def SetWindowShape(self, *evt):
        # Some window managers draw an unwanted outline for path shapes.
        # Keep the window boundary separate from the bitmap's alpha smoothing.
        self.hasShape = self.SetShape(GetRoundShape(self.w, self.h))

    def OnPaint(self, evt):
        w,h = self.GetSize()
        dc = wx.PaintDC(self)
        dc.SetPen(wx.Pen("#000000"))
        dc.SetBrush(wx.Brush("#000000"))
        dc.DrawRectangle(0,0,w,h)
        dc.DrawBitmap(self.bmp, 0, 0, True)
        dc.SetTextForeground("#FFFFFF")
        font = dc.GetFont()
        psize = font.GetPointSize()
        if PLATFORM == "win32":
            font.SetPointSize(psize+1)
        else:
            font.SetPointSize(psize)
        font.SetFaceName("Monospace")
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        dc.SetFont(font)
        dc.DrawLabel("%s %s" % (NAME, SG_VERSION),
                     wx.Rect(0, 298, 400, 15), wx.ALIGN_CENTER)
        dc.DrawLabel("Olivier Belanger", 
                     wx.Rect(0, 314, 400, 15), wx.ALIGN_CENTER)

    def OnClose(self):
        if self.mainframe:
            self.mainframe.Show()
        self.Destroy()
