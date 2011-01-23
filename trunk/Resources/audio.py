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

import math, time, random, wx
from constants import *
from pyo import *
from types import UnicodeType
import unicodedata

USE_MIDI = False

def ensureNFD(unistr):
    if PLATFORM == 'win32':
        if type(unistr) != UnicodeType:
            unistr = unistr.decode('cp1252')
        return unicodedata.normalize('NFC', unistr)
    else:    
        if type(unistr) != UnicodeType:
            unistr = unistr.decode('utf-8')
        return unicodedata.normalize('NFD', unistr)

def soundInfo(sndfile):
    sndfile = ensureNFD(sndfile)
    num_frames, dur, samprate, chans = sndinfo(sndfile)
    return (chans, samprate, dur)

def checkForDrivers():
    driverList, driverIndexes = pa_get_output_devices()
    selectedDriver = pa_get_default_output()
    return driverList, driverIndexes, selectedDriver

class Fx:
    def __init__(self, input, fx=0, chnls=2):
        self.input = input
        self.fx = fx
        if fx == 0:
            self.process = WGVerb(self.input, feedback=.95, cutoff=5000, mix=1, mul=.7)
        elif fx == 1:
            self.process = Delay(self.input, delay=.1, feedback=.75)
        elif fx == 2:
            self.process = Disto(self.input, drive=.9, slope=.75, mul=.2)
        elif fx == 3:
            self.process = Waveguide(self.input, freq=100, dur=30, mul=.5)
        elif fx == 4:
            self.rsine = Sine(freq=100)
            self.process = self.input * self.rsine
        elif fx == 5:
            self.process = Degrade(self.input, bitdepth=8, srscale=0.25)
        elif fx == 6:
            self.process = Harmonizer(self.input, transpo=-7, feedback=0.25)
        self.pan = SPan(self.process, outs=chnls, pan=0.5).out()

class Granulator_Stream:
    def __init__(self, order, env, trans_noise, dur_noise, num_grains, clock_func, srScale, chnls):
        self.order = order
        self.env = env
        self.trans_noise = trans_noise
        self.dur_noise = dur_noise
        self.num_grains = num_grains
        self.clock_func = clock_func
        self.srScale = srScale
        self.chnls = chnls
        self.granulator = None
        self.panner = None

        self.metro = Metro(time=0.025)
        self.duration = Randh(min=-1, max=1, freq=200, mul=0, add=.2)
        self.base_pitch = SigTo(value=1, time=0.01)
        self.transpo = SigTo(value=1, time=0.001)
        self.traj_amp = SigTo(value=1, time=0.01, init=1)
        self.y_pit = SigTo(value=1, time=0.01)
        self.y_amp = SigTo(value=1, time=0.01)
        self.y_pan = SigTo(value=0.5, time=0.01)
        self.y_dur = Randh(min=-1, max=1, freq=201, mul=0)
        self.y_pos = Randh(min=-1, max=1, freq=202, mul=0)
        self.fader = SigTo(value=0, mul=1./(math.log(self.num_grains)+1.))
        self.trigger = TrigFunc(self.metro, self.clock_func, self.order)

    def create_granulator(self, table, pos_rnd):
        self.table = table
        self.pos_rnd = pos_rnd
        self.position = SigTo(value=0, time=0.01, mul=self.table.getSize())
        self.y_pos_rnd = Sig(self.y_pos, mul=self.table.getSize())
        self.granulator = Granulator(table=self.table, env=self.env, pitch=self.base_pitch*self.y_pit*self.srScale*self.transpo,
                                    pos=self.position+self.pos_rnd+self.y_pos_rnd,
                                    dur=self.duration*self.trans_noise+self.dur_noise+self.y_dur,
                                    grains=self.num_grains, basedur=self.duration.add, 
                                    mul=self.fader*self.y_amp*self.traj_amp
                                    ).stop()
        self.panner = SPan(input=self.granulator, outs=self.chnls, pan=self.y_pan).stop()                       

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

    def togglePan(self, state):
        if self.granulator == None:
            return
        if state:
            self.granulator.play()
            self.panner.out()
        else:
            self.granulator.out(self.order)
            self.panner.stop()    

    def setActive(self, val):
        if val == 1:
            self.metro.play()
            self.granulator.out(self.order)
            self.fader.value = 1
        else:    
            self.metro.stop()
            self.granulator.stop()
            self.fader.value = 0

class SG_Audio:
    def __init__(self, clock, refresh, controls, createTraj, deleteTraj, envFrame):
        self.clock = clock
        self.refresh = refresh
        self.controls = controls
        self.createTraj = createTraj
        self.deleteTraj = deleteTraj
        self.envFrame = envFrame
        self.server_started = False
        self.num_grains = 8
        self.activeStreams = []
        self.fxs = {}
        self.samplingRate = 44100
        self.globalAmplitude = 1.0
        self.midiTriggerMethod = 0
        self.midiPitches = []
        if PLATFORM == "darwin":
            self.server = Server(sr=self.samplingRate, buffersize=1024, duplex=0, audio="coreaudio")
        elif PLATFORM == "linux2":
            self.server = Server(sr=self.samplingRate, buffersize=1024, duplex=0, audio="jack")
        else:
            self.server = Server(sr=self.samplingRate, buffersize=1024, duplex=0)
        self.pitch_check = 1
        self.pitch_map = Map(0, 1, "lin")
        self.amp_check = 0
        self.amp_map = Map(0, 1, "lin")
        self.dur_check = 0
        self.dur_map = Map(0.001, 1, "log")
        self.pos_check = 0
        self.pos_map = Map(0.001, 1, "log")
        self.pan_check = 0
        self.pan_map = Map(0, 1, "lin")

    def boot(self, driver, chnls, samplingRate, midiInterface):
        global USE_MIDI
        self.server.setOutputDevice(driver)
        self.server.setNchnls(chnls)
        self.samplingRate = samplingRate
        self.server.setSamplingRate(samplingRate)
        print midiInterface
        if midiInterface != None:
            self.server.setMidiInputDevice(midiInterface)
        self.server._server.setAmpCallable(self.controls.meter)
        self.server.boot()
        self.mixer = Mixer(outs=8, chnls=chnls)
        if midiInterface != None:
            USE_MIDI = True
            self.notein = Notein(poly=10)
            self.noteinpitch = Sig(self.notein["pitch"])
            self.noteinvelocity = Sig(self.notein["velocity"])
            self.noteonThresh = Thresh(self.notein["velocity"])
            self.noteonFunc = TrigFunc(self.noteonThresh, self.noteon, range(10))
            self.noteoffThresh = Thresh(self.notein["velocity"], threshold=.001, dir=1)
            self.noteoffFunc = TrigFunc(self.noteoffThresh, self.noteoff, range(10))
        self.env = CosTable([(0,0),(2440,1),(5751,1),(8191,0)])
        self.envFrame.setEnv(self.env)
        self.refresh_met = Metro(0.066666666666666666)
        self.refresh_func = TrigFunc(self.refresh_met, self.refresh_screen)
        self.pos_noise = Randh(min=-1, max=1, freq=199, mul=0)
        self.dur_noise = Randh(min=-1, max=1, freq=198, mul=0)
        self.srScale = Sig(1)
        self.trans_noise = Choice([1], freq=500)
        self.streams = {}
        for i in range(MAX_STREAMS):
            self.streams[i] = Granulator_Stream(i, self.env, self.trans_noise, self.dur_noise, 
                                                self.num_grains, self.clock, self.srScale, chnls)   
        
    def shutdown(self):
        self.server.shutdown()
        self.streams = {}
        del self.env
        del self.refresh_met
        del self.refresh_func
        del self.pos_noise
        del self.dur_noise
        del self.srScale
        del self.trans_noise
        if USE_MIDI:
            del self.notein
            del self.noteinpitch
            del self.noteinvelocity
            del self.noteonThresh
            del self.noteonFunc
            del self.noteoffThresh
            del self.noteoffFunc

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

    def setGlobalAmp(self, val):
        self.globalAmplitude = val
        self.server.amp = self.globalAmplitude

    def getViewTable(self):
        self.env_extract = []
        for j in range(len(self.table)):
            self.env_extract.append([math.fabs(x) for i, x in enumerate(self.table[j].getTable()) if i % 64 == 0])
        return self.env_extract

    def setMidiMethod(self, value):
        self.midiTriggerMethod = value

    def getMidiMethod(self):
        return self.midiTriggerMethod

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

    def setTranspo(self, which, x):
        self.streams[which].transpo.value = x

    def setTrajAmplitude(self, which, x):
        self.streams[which].traj_amp.value = x

    def setXposition(self, which, x):
        self.streams[which].position.value = x

    def setYposition(self, which, x):
        if self.pitch_check:
            pit = self.pitch_map.get(x)
            self.streams[which].y_pit.value = pit
        else:
            self.streams[which].y_pit.value = 1
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
            self.streams[which].y_amp.value = amp
        else:
            self.streams[which].y_amp.value = 1
        if self.pan_check:
            pan = self.pan_map.get(x)
            self.streams[which].y_pan.value = pan
        else:
            pass

    def setPanCheck(self, state):
        self.pan_check = state
        for which in self.activeStreams:
            self.streams[which].togglePan(state)

    def setActive(self, which, val):
        try: 
            self.streams[which].setActive(val)
            self.streams[which].togglePan(self.pan_check)
        except: 
            pass 
        if val == 1:
            if which not in self.activeStreams:
                self.activeStreams.append(which)
            if self.pan_check:
                if self.streams[which].granulator != None:
                    self.mixer.addInput(which, self.streams[which].panner)
            else:
                if self.streams[which].granulator != None:
                    self.mixer.addInput(which, self.streams[which].granulator)
        else:
            if which in self.activeStreams:
                self.activeStreams.remove(which)
                self.mixer.delInput(which)
    
    def addFx(self, fx, key):
        self.fxs[key] = Fx(self.mixer[key], fx)

    def removeFx(self, key):
        del self.fxs[key]

    def setMixerChannelAmp(self, vin, vout, val):
        self.mixer.setAmp(vin, vout, val)

    def setMixerChannelAmps(self, trajs, fxballs):
        [self.mixer.setAmp(t.getId(), fx.getId(), fx.getAmpValue(t.circlePos)) for t in trajs for fx in fxballs]

    def handleFxSlider1(self, fx, key, val):
        if fx == 0:
            self.fxs[key].process.feedback = val
        elif fx == 1:
            self.fxs[key].process.delay = val
        elif fx == 2:
            self.fxs[key].process.drive = val
        elif fx == 3:
            self.fxs[key].process.freq = val
        elif fx == 4:
            self.fxs[key].rsine.freq = val
        elif fx == 5:
            self.fxs[key].process.bitdepth = val
        elif fx == 6:
            self.fxs[key].process.transpo = val

    def handleFxSlider2(self, fx, key, val):
        if fx == 0:
            self.fxs[key].process.cutoff = val
        elif fx == 1:
            self.fxs[key].process.feedback = val
        elif fx == 2:
            self.fxs[key].process.slope = val
        elif fx == 3:
            self.fxs[key].process.dur = val
        elif fx == 4:
            self.fxs[key].rsine.mul = 1. - val
            self.fxs[key].rsine.add = val
        elif fx == 5:
            self.fxs[key].process.srscale = val
        elif fx == 6:
            self.fxs[key].process.feedback = val

    def handleFxMul(self, key, val):
        self.fxs[key].pan.mul = val

    def handleFxPan(self, key, val):
        self.fxs[key].pan.pan = val

    def start(self):
        for which in self.activeStreams:
            self.setActive(which, 1)
        self.refresh_met.play()
        self.server.start() 
        self.server.amp = self.globalAmplitude
        self.server_started = True
            
    def stop(self):
        self.refresh_met.stop()
        self.server.stop()       
        self.server_started = False    

    def refresh_screen(self): 
        wx.CallAfter(self.refresh)        

    def noteon(self, voice):
        if self.midiTriggerMethod == 0:
            pits = self.noteinpitch.get(True)
            vels = self.noteinvelocity.get(True)
            pit, vel = midiToTranspo(pits[voice]), vels[voice]
            self.createTraj(voice, pit, vel)
        elif self.midiTriggerMethod == 1:
            pits = self.noteinpitch.get(True)
            vels = self.noteinvelocity.get(True)
            pit, vel = pits[voice], vels[voice]
            if pit not in self.midiPitches:
                self.midiPitches.append(pit)
                self.createTraj(pit, midiToTranspo(pit), vel)
            else:
                self.midiPitches.remove(pit)
                self.deleteTraj(pit)

    def noteoff(self, voice):
        if self.midiTriggerMethod == 0:
            self.deleteTraj(voice)
