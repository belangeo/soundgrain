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
import threading, time, osc

class WaitCsound(threading.Thread):
    def __init__(self, function):
        threading.Thread.__init__(self)
        self.function = function
        self.terminated = False

        #osc.init()
        self.inSocket = osc.createListener("127.0.0.1", 15000)
        osc.bind(self.call, "/csound_ready")

    def run(self):
        while not self.terminated:
            osc.getOSC(self.inSocket)
            time.sleep(.25)

    def call(self, *msg):
        self.terminated = True
        self.function("".join(msg[0][2:]))
        del self.inSocket
