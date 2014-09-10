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

import __builtin__
__builtin__.SOUNDGRAIN_APP_OPENED = True

import os, wx
from types import ListType
from Resources.constants import *
from Resources.splash import SoundGrainSplashScreen
from Resources.MainFrame import MainFrame

class SoundGrainApp(wx.App):
    def __init__(self, *args, **kwargs):
        wx.App.__init__(self, *args, **kwargs)
    
    def OnInit(self):
        X = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        Y = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
        if X < 900: 
            sizex = X - 40
        else: 
            sizex = 900
        if PLATFORM in ['win32', 'linux2']: 
            defaultY = 670
        else: 
            defaultY = 650
        if Y < defaultY: 
            sizey = Y - 40
        else: 
            sizey = defaultY
        self.frame = MainFrame(None, -1, pos=(20,20), size=(sizex,sizey), 
                               screen_size=(X,Y))
        return True

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
    file = None
    if len(sys.argv) > 1:
        file = sys.argv[1]
    app = SoundGrainApp(redirect=False)
    splash = SoundGrainSplashScreen(None, os.path.join(RESOURCES_PATH, 
                                    "SoundGrainSplash.png"), app.frame)
    if file:
        wx.CallAfter(app.frame.loadFile, ensureNFD(file))
    app.MainLoop()
