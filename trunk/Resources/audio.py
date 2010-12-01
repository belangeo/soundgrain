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

import math, time, wx
from constants import *
from pyo import *

def soundInfo(sndfile):
    num_frames, dur, samprate, chans = sndinfo(sndfile)
    return (chans, samprate, dur)

def checkForDrivers():
    driverList, driverIndexes = pa_get_output_devices()
    selectedDriver = pa_get_default_output()
    return driverList, driverIndexes, selectedDriver

class Granulator_Stream:
    def __init__(self, order, env, trans_noise, dur_noise, num_grains, amplitude, clock_func, srScale):
        self.order = order
        self.env = env
        self.trans_noise = trans_noise
        self.dur_noise = dur_noise
        self.num_grains = num_grains
        self.amplitude = amplitude
        self.clock_func = clock_func
        self.srScale = srScale
        
        self.metro = Metro(time=0.025)
        self.duration = Noise(mul=0, add=.2)
        self.base_pitch = SigTo(value=1, time=0.01)
        self.pitch = SigTo(value=1, time=0.01)
        self.traj_amp = SigTo(value=1, time=0.01, init=1)
        self.amp = SigTo(value=1, time=0.01)
        self.y_dur = Noise(mul=0)
        self.y_pos = Noise(mul=0)
        self.fader = SigTo(value=0, mul=1./(math.log(self.num_grains)+1.))

        self.trigger = TrigFunc(self.metro, self.click)

    def create_granulator(self, table, pos_rnd):
        self.table = table
        self.pos_rnd = pos_rnd
        self.position = SigTo(value=0, time=0.01, mul=self.table.getSize())
        self.y_pos_rnd = Sig(self.y_pos, mul=self.table.getSize())
        self.granulator = Granulator(table=self.table, env=self.env, pitch=self.base_pitch*self.pitch*self.srScale,
                                    pos=self.position+self.pos_rnd+self.y_pos_rnd,
                                    dur=self.duration*self.trans_noise+self.dur_noise+self.y_dur,
                                    grains=self.num_grains, basedur=self.duration.add, 
                                    mul=self.fader*self.amplitude*self.amp*self.traj_amp
                                    ).stop()

    def ajustLength(self):
        self.position.mul = self.table.getSize()
        self.y_pos_rnd.mul = self.table.getSize()
        
    def setNumGrains(self, x):
        self.num_grains = x
        try:
            self.granulator.grains = x
        except: 
            pass    
        self.fader.mul = 1./(math.log(self.num_grains)+1.) 

    def setBasePitch(self, x):
        self.base_pitch.value = x
        
    def setGrainSize(self, x):
        self.duration.add = x
        try:
            self.granulator.basedur = x
        except:
            pass
    
    def setActive(self, val):
        if val == 1:
            self.metro.play()
            self.granulator.out(self.order)
            self.fader.value = 1
        else:    
            self.metro.stop()
            self.granulator.stop()
            self.fader.value = 0

    def click(self):
        self.clock_func(self.order)

class SG_Audio:
    def __init__(self, clock, refresh, controls):
        self.clock = clock
        self.refresh = refresh
        self.controls = controls
        self.server_started = False
        self.num_grains = 8
        self.activeStreams = []
        self.samplingRate = 44100
        if PLATFORM == "darwin":
            self.server = Server(sr=self.samplingRate, buffersize=512, duplex=0, audio="coreaudio")
        else:
            self.server = Server(sr=self.samplingRate, buffersize=512, duplex=0)
        self.pitch_check = 1
        self.pitch_map = Map(0, 1, "lin")
        self.amp_check = 0
        self.amp_map = Map(0, 1, "lin")
        self.dur_check = 0
        self.dur_map = Map(0, 1, "lin")
        self.pos_check = 0
        self.pos_map = Map(0, 1, "lin")

    def boot(self, driver, chnls, samplingRate):
        self.server.setOutputDevice(driver)
        self.server.setNchnls(chnls)
        self.samplingRate = samplingRate
        self.server.setSamplingRate(samplingRate)
        self.server._server.setAmpCallable(self.controls.meter)
        self.server.boot()
        self.env = HannTable()
        self.refresh_met = Metro(.05)
        self.refresh_func = TrigFunc(self.refresh_met, self.refresh_screen)
        self.pos_noise = Noise(0)
        self.dur_noise = Noise(0)
        self.srScale = Sig(1)
        self.trans_noise = Choice([1], freq=1000)
        self.amplitude = SigTo(0.7)
        self.rec_inc = 0
        self.streams = {}
        for i in range(24):
            self.streams[i] = Granulator_Stream(i, self.env, self.trans_noise, self.dur_noise, 
                                                self.num_grains, self.amplitude, self.clock, self.srScale)
        
    def shutdown(self):
        self.server.shutdown()
        self.streams = {}
        del self.env
        del self.refresh_met
        del self.refresh_func
        del self.pos_noise
        del self.dur_noise
        del self.trans_noise
        del self.amplitude

    def recStart(self, filename, fileformat=0, sampletype=0):
        self.server.recordOptions(fileformat=fileformat, sampletype=sampletype)
        if len(filename.split('.')) > 1:
            if filename.split('.')[1].lower() in ['aif', 'aiff', 'wav', 'wave']:
                filename = filename.split('.')[0]
        if fileformat == 0: ext = ".wav"
        else: ext = ".aif"
        date = time.strftime('_%d_%b_%Y_%Hh%M')
        self.server.recstart(os.path.join(os.path.expanduser('~'), "Desktop", filename+date+ext))        

    def recStop(self):
        self.server.recstop()

    def loadSnd(self, sndPath):
        ch, sndsr, dur = soundInfo(sndPath)
        self.srScale.value = float(sndsr) / self.samplingRate
        self.table = SndTable(sndPath)
        self.pos_rnd = Sig(self.pos_noise, self.table.getSize())
        for gr in self.streams.values():
            gr.create_granulator(self.table, self.pos_rnd)
            gr.ajustLength()
        if self.server_started:
            for which in self.activeStreams:
                self.streams[which].setActive(1)

    def getViewTable(self):
        self.env_extract = []
        for i in range(len(self.table)):
            self.env_extract.append([math.fabs(x) for i, x in enumerate(self.table[i].getTable()) if i % 64 == 0])
        return self.env_extract

    def setNumGrains(self, x):
        self.num_grains = x
        for gr in self.streams.values():
            gr.setNumGrains(self.num_grains)

    def setBasePitch(self, x):
        for gr in self.streams.values():
            gr.setBasePitch(x)

    def setGrainSize(self, x):
        for gr in self.streams.values():
            gr.setGrainSize(x)

    def setMetroTime(self, which, x):
        self.streams[which].metro.time = x

    def setTrajAmplitude(self, which, x):
        self.streams[which].traj_amp.value = x

    def setXposition(self, which, x):
        self.streams[which].position.value = x

    def setYposition(self, which, x):
        if self.pitch_check:
            pit = self.pitch_map.get(x)
            self.streams[which].pitch.value = pit
        else:
            self.streams[which].pitch.value = 1
        if self.dur_check:
            dur = self.dur_map.get(x)
            self.streams[which].y_dur.mul = dur
        else:
            self.streams[which].y_dur.mul = 0
        if self.pos_check:
            pos = self.pos_map.get(x)
            self.streams[which].y_pos.mul = pos
        else:
            self.streams[which].y_pos.mul = 0
        if self.amp_check:
            amp = self.amp_map.get(x)
            self.streams[which].amp.value = amp
        else:
            self.streams[which].amp.value = 1

    def setActive(self, which, val):
        try: self.streams[which].setActive(val)
        except: pass 
        if val == 1:
            self.activeStreams.append(which)
        else:
            if which in self.activeStreams:
                self.activeStreams.remove(which)
        
    def start(self):
        for which in self.activeStreams:
            self.streams[which].setActive(1)
        self.refresh_met.play()
        self.server.start() 
        self.server_started = True    
            
    def stop(self):
        self.refresh_met.stop()
        self.server.stop()       
        self.server_started = False    

    def refresh_screen(self): 
        wx.CallAfter(self.refresh)        
