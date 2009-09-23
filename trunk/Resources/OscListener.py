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

import math, time
import wx
import ounk.osc as osc

class Listener():
    def __init__(self, meter, csoundReady, clock, surface):
        self.meter = meter
        self.csoundReady = csoundReady
        self.clock = clock
        self.surface = surface
        
        osc.init()
        osc.listen("127.0.0.1", 15000)
        osc.bind(self.monitorReady, "/csound_ready")    
        osc.bind(self.monitor, "/monitor")
        osc.bind(self.metro1, "/metro0")
        osc.bind(self.metro2, "/metro1")
        osc.bind(self.metro3, "/metro2")
        osc.bind(self.metro4, "/metro3")
        osc.bind(self.metro5, "/metro4")
        osc.bind(self.metro6, "/metro5")
        osc.bind(self.metro7, "/metro6")
        osc.bind(self.metro8, "/metro7")
        osc.bind(self.refreshScreen, "/refresh")

    def monitor(self, *msg):
        amps = msg[0][2:]
        amps = [math.sqrt(amp) for amp in amps]
        wx.CallAfter(self.meter.setAmplitude, amps)

    def refreshScreen(self, *msg):
        wx.CallAfter(self.surface.Refresh)
        
    def metro1(self, *msg):
        wx.CallAfter(self.clock, 0) 
        
    def metro2(self, *msg):
        wx.CallAfter(self.clock, 1)
        
    def metro3(self, *msg):
        wx.CallAfter(self.clock, 2)
        
    def metro4(self, *msg):
        wx.CallAfter(self.clock, 3)
        
    def metro5(self, *msg):
        wx.CallAfter(self.clock, 4)
        
    def metro6(self, *msg):
        wx.CallAfter(self.clock, 5)
        
    def metro7(self, *msg):
        wx.CallAfter(self.clock, 6)
        
    def metro8(self, *msg):
        wx.CallAfter(self.clock, 7)
         
    def monitorReady(self, *msg):
        state = msg[0][2:][0]
        wx.CallAfter(self.csoundReady, state)

    def stop(self):
        osc.dontListen()

