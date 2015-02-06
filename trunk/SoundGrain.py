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
import sys
if sys.platform == "linux2":
    import wxversion
    if wxversion.checkInstalled("3.0"):
        wxversion.select("3.0")
    elif wxversion.checkInstalled("2.8"):
        wxversion.select("2.8")

import wx
from types import ListType
from Resources.constants import *
from Resources.splash import SoundGrainSplashScreen
from Resources.MainFrame import MainFrame

class SoundGrainApp(wx.App):
    def __init__(self, *args, **kwargs):
        wx.App.__init__(self, *args, **kwargs)
        sysx = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        sysy = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
        if sysx < 900:
            sizex = sysx - 40
        else:
            sizex = 900
        if sysy < 670:
            sizey = sysy - 40
        else:
            sizey = 670
        self.frame = MainFrame(None, -1, pos=(20, 20), size=(sizex, sizey),
                               screen_size=(sysx, sysy))

    def MacOpenFiles(self, filenames):
        if type(filenames) != ListType:
            filenames = [filenames]
        self.frame.loadFile(ensureNFD(filenames[0]))

    def MacReopenApp(self):
        try:
            self.frame.Raise()
        except:
            pass

if __name__ == '__main__':
    sgfile = None
    if len(sys.argv) > 1:
        sgfile = sys.argv[1]
    app = SoundGrainApp(redirect=False)
    splash = SoundGrainSplashScreen(None, SPLASH_FILE, app.frame)
    if sgfile:
        wx.CallAfter(app.frame.loadFile, ensureNFD(sgfile))
    app.MainLoop()
