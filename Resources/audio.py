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

import math, time, random, wx, os
from .constants import *

if SAMPLE_PRECISION == "64-bit":
    try:
        from pyo64 import *
    except:
        from pyo import *
else:
    from pyo import *

USE_MIDI = False

def soundInfo(sndfile):
    num_frames, dur, samprate, chans, fformat, stype = sndinfo(sndfile)
    return (chans, samprate, dur)

def checkForDrivers():
    driverList, driverIndexes = pa_get_output_devices()
    selectedDriver = pa_get_default_output()
    return driverList, driverIndexes, selectedDriver

def checkForMidiDrivers():
    driverList, driverIndexes = pm_get_input_devices()
    selectedDriver = pm_get_default_input()
    return driverList, driverIndexes, selectedDriver

class Fx:
    def __init__(self, input, fx=0, chnls=2):
        self.input = Denorm(DCBlock(input))
        self.fx = fx
        if fx == 0:
            self.process = WGVerb(self.input, feedback=.95, cutoff=5000, bal=1, mul=.7)
        elif fx == 1:
            self.process = Delay(self.input, delay=.1, feedback=.75)
        elif fx == 2:
            self.process = Disto(self.input, drive=.9, slope=.75, mul=.2)
        elif fx == 3:
            self.process = Waveguide(self.input, freq=100, dur=30, mul=.3)
        elif fx == 4:
            self.process = ComplexRes(self.input, freq=500, decay=1)
        elif fx == 5:
            self.process = Degrade(self.input, bitdepth=8, srscale=0.25)
        elif fx == 6:
            self.process = Harmonizer(self.input, transpo=-7, feedback=0.25)
        elif fx == 7:
            self.clip = Clip(self.input, min=-0.1, max=0.1, mul=3.3)
            self.process = ButLP(self.clip, freq=5000)
        elif fx == 8:
            self.lfo = Sine(freq=.2, mul=.0045, add=.005)
            self.flange = Delay(self.input, delay=self.lfo, feedback=.5)
            self.process = self.input + self.flange
        elif fx == 9:
            self.process = AllpassWG(self.input, freq=100, feed=0.999, detune=0.5, mul=.3)
        self.pan = SPan(self.process, outs=chnls, pan=0.5)

class Granulator_Stream:
    def __init__(self, order, env, dens_noise, trans_noise, dur_noise, pit_noise, dev_noise,
                 pan_noise, ff_noise, fq_noise, ftype, clock_func, chnls):
        self.order = order
        self.env = env
        self.dens_noise = dens_noise
        self.pit_noise = pit_noise
        self.trans_noise = trans_noise
        self.dur_noise = dur_noise
        self.dev_noise = dev_noise
        self.pan_noise = pan_noise
        self.ff_noise = ff_noise
        self.fq_noise = fq_noise
        self.ftype = ftype
        self.clock_func = clock_func
        self.chnls = chnls
        self.granulator = None

        self.metro = Metro(time=0.025)
        self.base_pitch = SigTo(value=1, time=0.01)
        self.transpo = SigTo(value=1, time=0.001)
        self.traj_amp = SigTo(value=1, time=0.01, init=1)
        self.y_dns = SigTo(value=1, time=0.01)
        self.y_pit = SigTo(value=1, time=0.01)
        self.y_len = SigTo(value=1, time=0.01)
        self.y_dev = SigTo(value=1, time=0.01)
        self.y_amp = SigTo(value=1, time=0.01)
        self.y_pan = SigTo(value=0.5, time=0.01, mul=2, add=-1)
        self.y_fif = SigTo(value=1, time=0.01)
        self.y_fiq = SigTo(value=1, time=0.01)
        # one global noise for every voices ?
        self.y_trs = Randh(min=-1, max=1, freq=231, mul=0, add=1).stop()
        self.y_dur = Randh(min=-1, max=1, freq=201, mul=0, add=1).stop()
        self.y_pos = Randh(min=-1, max=1, freq=202, mul=0).stop()
        self.y_ffr = Randh(min=-1, max=1, freq=677, mul=0, add=1).stop()
        self.y_fqr = Randh(min=-1, max=1, freq=547, mul=0, add=1).stop()
        self.fader = SigTo(value=0, mul=0.15)
        self.trigger = TrigFunc(self.metro, self.clock_func, self.order)

    def create_granulator(self, table, pos_rnd):
        self.table = table
        self.pos_rnd = pos_rnd
        self.position = SigTo(value=0, time=0.01, mul=self.table.getSize(False))
        self.y_pos_rnd = Sig(self.y_pos, mul=self.table.getSize(False))
        nchnls = len(self.table)
        if nchnls == 1:
            self.v_pan = 0.5
        else:
            self.v_pan = [i / float(nchnls - 1) for i in range(nchnls)]
        self.granulator = Particle2( table=self.table,
                                    env=self.env,
                                    dens=self.dens_noise*self.y_dns,
                                    pitch=self.base_pitch*self.transpo*self.pit_noise*self.trans_noise*self.y_pit*self.y_trs,
                                    pos=self.position+self.pos_rnd+self.y_pos_rnd,
                                    dur=self.dur_noise*self.y_len*self.y_dur,
                                    dev=self.dev_noise+self.y_dev,
                                    pan=Clip(self.y_pan+self.pan_noise+self.v_pan, 0, 1),
                                    filterfreq=self.ff_noise*self.y_fif*self.y_ffr,
                                    filterq=self.fq_noise*self.y_fiq*self.y_fqr,
                                    filtertype=self.ftype,
                                    chnls=self.chnls,
                                    mul=self.fader*self.y_amp*self.traj_amp,
                                    ).stop()

    def ajustLength(self):
        self.position.mul = self.table.getSize(False)
        self.y_pos_rnd.mul = self.table.getSize(False)

    def setGain(self, x):
        self.fader.mul = x

    def setBasePitch(self, x):
        self.base_pitch.value = x

    def setActive(self, val):
        if val == 1:
            self.metro.play()
            self.y_trs.play()
            self.y_dur.play()
            self.y_pos.play()
            self.y_ffr.play()
            self.y_fqr.play()
            self.granulator.play()
            self.fader.value = 1
        else:
            self.metro.stop()
            self.y_trs.stop()
            self.y_dur.stop()
            self.y_pos.stop()
            self.y_ffr.stop()
            self.y_fqr.stop()
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
        self.chnls = 2
        self.activeStreams = []
        self.fxs = {}
        self.samplingRate = 44100
        self.globalAmplitude = 1.0
        self.midiTriggerMethod = 0
        self.midiPitches = []
        self.server = Server(sr=self.samplingRate, buffersize=256, duplex=0)
        self.check_dict = {"y_dns_check": 0, "y_pit_check": 1, "y_len_check": 0,
                           "y_dev_check": 0, "y_amp_check": 0, "y_trs_check": 0,
                           "y_dur_check": 0, "y_pos_check": 0, "y_pan_check": 0,
                           "y_fif_check": 0, "y_fiq_check": 0, "y_ffr_check": 0,
                           "y_fqr_check": 0}
        # map_dict: [min, max, exp, mid(optional)]
        self.map_dict = {"y_dns_map": [0, 1, 2, None], "y_pit_map": [0, 1, 1, None], "y_len_map": [0, 1, 1, None],
                         "y_dev_map": [0, 1, 1, None], "y_amp_map": [0, 1, 1, None], "y_trs_map": [0, 1, 3, None],
                         "y_dur_map": [0, 1, 4, None], "y_pos_map": [0, 1, 4, None], "y_pan_map": [0, 1, 1, None],
                         "y_fif_map": [0, 1, 2, None], "y_fiq_map": [0, 1, 2, None], "y_ffr_map": [0, 1, 1, None],
                         "y_fqr_map": [0, 1, 1, None]}

    def boot(self, driver, chnls, samplingRate, midiInterface):
        global USE_MIDI
        self.server.setOutputDevice(driver)
        self.chnls = chnls
        self.server.setNchnls(chnls)
        self.samplingRate = samplingRate
        self.server.setSamplingRate(samplingRate)
        if midiInterface != None:
            self.server.setMidiInputDevice(midiInterface)
        self.server._server.setAmpCallable(self.controls.meter)
        self.server.boot()
        self.mixer = Mixer(outs=10, chnls=chnls)
        if midiInterface != None:
            USE_MIDI = True
            self.notein = Notein(poly=16)
            self.noteinpitch = Sig(self.notein["pitch"])
            self.noteinvelocity = Sig(self.notein["velocity"])
            self.noteonFunc = TrigFunc(self.notein["trigon"], self.noteon, list(range(16)))
            self.noteoffFunc = TrigFunc(self.notein["trigoff"], self.noteoff, list(range(16)))
        self.env = CosTable([(0,0),(2440,1),(5751,1),(8191,0)])
        self.envFrame.setEnv(self.env)
        self.refresh_met = Metro(0.066666666666666666)
        self.refresh_func = TrigFunc(self.refresh_met, self.refresh_screen)

        self.dens_noise = Randh(min=0, max=0, freq=25, mul=32, add=32)
        self.pit_noise = Randh(min=-1, max=1, freq=397, mul=0, add=1)
        self.pos_noise = Randh(min=-1, max=1, freq=199, mul=0)
        self.dur_noise = Randh(min=0, max=0, freq=198, mul=0.2, add=0.2)
        self.dev_noise = Sig(0)
        self.pan_noise = Randh(min=-1, max=1, freq=303, mul=0)
        self.trans_noise = Choice([1], freq=777)
        self.ffr_noise = Noise(mul=0, add=1)
        self.ffr_noise.setType(1)
        self.ff_noise = Choice(choice=[1.0], freq=999, mul=15000)
        self.fqr_noise = Noise(0.0, add=1.0)
        self.fqr_noise.setType(1)
        self.filterq = SigTo(0.7, time=0.05, init=0.7, mul=self.fqr_noise)
        self.filtert = SigTo(0.0, time=0.05, init=0.0)

        self.streams = {}
        for i in range(MAX_STREAMS):
            self.streams[i] = Granulator_Stream(i, self.env, self.dens_noise, self.trans_noise, self.dur_noise,
                                                self.pit_noise, self.dev_noise, self.pan_noise, self.ff_noise*self.ffr_noise,
                                                self.filterq, self.filtert, self.clock, chnls)

        self.stream_sum = Sig([0] * self.chnls)
        self.eqFreq = [100, 500, 2000]
        self.eqGain = [1, 1, 1, 1]

        self.fbEqAmps = SigTo(self.eqGain, time=.1, init=self.eqGain)
        self.fbEq = FourBand(self.stream_sum, freq1=self.eqFreq[0],
                            freq2=self.eqFreq[1], freq3=self.eqFreq[2], mul=self.fbEqAmps)
        self.outEq = Mix(self.fbEq, voices=self.chnls)

        self.compLevel = Compress(self.outEq, thresh=-3, ratio=2, risetime=.01,
                                    falltime=.1, lookahead=0, knee=0.5, outputAmp=True)
        self.compDelay = Delay(self.outEq, delay=0.005)
        self.outComp = self.compDelay * self.compLevel
        self.outComp.out()

    def shutdown(self):
        if hasattr(self, "table"):
            del self.table
        if hasattr(self, "pos_rnd"):
            del self.pos_rnd
        self.streams = {}
        self.fxs = {}
        del self.env
        del self.refresh_met
        del self.refresh_func
        del self.dens_noise
        del self.pit_noise
        del self.pos_noise
        del self.dur_noise
        del self.dev_noise
        del self.pan_noise
        del self.trans_noise
        del self.ffr_noise
        del self.ff_noise
        del self.filterq
        del self.filtert
        del self.mixer
        del self.fbEqAmps
        del self.fbEq
        del self.outEq
        del self.compLevel
        del self.compDelay
        del self.outComp
        if USE_MIDI:
            del self.notein
            del self.noteinpitch
            del self.noteinvelocity
            del self.noteonFunc
            del self.noteoffFunc
        self.server.shutdown()

    def recStart(self, filename, fileformat=0, sampletype=0):
        self.server.recordOptions(fileformat=fileformat, sampletype=sampletype)
        filename, ext = os.path.splitext(filename)
        if fileformat >= 0 and fileformat < 8:
            ext = RECORD_EXTENSIONS[fileformat]
        else:
            ext = ".wav"
        date = time.strftime('_%d_%b_%Y_%Hh%M')
        complete_filename = toSysEncoding(filename + date + ext)
        self.server.recstart(complete_filename)

    def recStop(self):
        self.server.recstop()

    def setEqFreq(self, which, freq):
        self.eqFreq[which] = freq
        if which == 0:
            self.fbEq.freq1 = freq
        elif which == 1:
            self.fbEq.freq2 = freq
        elif which == 2:
            self.fbEq.freq3 = freq

    def setEqGain(self, which, gain):
        self.eqGain[which] = gain
        self.fbEqAmps.value = self.eqGain

    def setCompParam(self, param, value):
        if param == "thresh":
            self.compLevel.thresh = value
        elif param == "ratio":
            self.compLevel.ratio = value
        elif param == "risetime":
            self.compLevel.risetime = value
        elif param == "falltime":
            self.compLevel.falltime = value

    def getTableDuration(self):
        return self.table.getDur(False)

    def loadSnd(self, sndPath):
        ch, sndsr, dur = soundInfo(sndPath)
        self.table = SndTable(sndPath)
        self.table.normalize()
        self.pos_rnd = Sig(self.pos_noise, self.table.getSize(False))
        for gr in self.streams.values():
            gr.create_granulator(self.table, self.pos_rnd)
            gr.ajustLength()
        self.stream_sum.value = Mix([st.granulator for st in self.streams.values()] + \
                                    [f.pan for f in self.fxs.values()], voices=self.chnls)
        if self.server.getIsStarted():
            for which in self.activeStreams:
                self.streams[which].setActive(1)

    def insertSnd(self, sndPath, start, end, point, cross):
        self.table.insert(sndPath, point, cross, start, end)
        self.pos_rnd.mul = self.table.getSize(False)
        for gr in self.streams.values():
            gr.ajustLength()
        if self.server.getIsStarted():
            for which in self.activeStreams:
                self.streams[which].setActive(1)

    def setGlobalAmp(self, val):
        self.globalAmplitude = val
        self.server.amp = self.globalAmplitude

    def getViewTable(self, size):
        return self.table.getViewTable(size)

    def setMidiMethod(self, value):
        self.midiTriggerMethod = value

    def getMidiMethod(self):
        return self.midiTriggerMethod

    def setDensity(self, x):
        self.dens_noise.add = x
        self.dens_noise.mul = x
        if x < 1:
            x = 1
        amp = 0.707/(math.log(x)+1)
        for gr in self.streams.values():
            gr.setGain(amp)

    def setRandDens(self, x):
        x = floatmap(x, exp=2)
        self.dens_noise.min = -x
        self.dens_noise.max = x

    def setBasePitch(self, x):
        for gr in self.streams.values():
            gr.setBasePitch(x)

    def setGrainDur(self, x):
        x *= 0.001
        self.dur_noise.add = x
        self.dur_noise.mul = x

    def setRandDur(self, x):
        x = floatmap(x, exp=2)
        self.dur_noise.min = -x
        self.dur_noise.max = x

    def setGrainDev(self, x):
        self.dev_noise.value = x

    def setFilterFreq(self, x):
        self.ff_noise.mul = x

    def setFilterQ(self, x):
        self.filterq.value = x

    def setFilterType(self, x):
        self.filtert.value = x

    def setRandPos(self, x):
        x = floatmap(x, min=0, max=0.5, exp=2)
        self.pos_noise.mul = x

    def setRandPit(self, x):
        x = floatmap(x, exp=3)
        self.pit_noise.mul = x * 0.99

    def setRandPan(self, x):
        self.pan_noise.mul = x

    def setRandFilterFreq(self, x):
        self.ffr_noise.mul = x

    def setRandFilterQ(self, x):
        self.fqr_noise.mul = x

    def setDiscreteTrans(self, lst):
        self.trans_noise.choice = lst

    def setDiscreteFilterTrans(self, lst):
        self.ff_noise.choice = lst

    def setMetroTime(self, which, x):
        self.streams[which].metro.time = x

    def setTranspo(self, which, x):
        self.streams[which].transpo.value = x

    def setTrajAmplitude(self, which, x):
        self.streams[which].traj_amp.value = x

    def setCheck(self, which, state):
        self.check_dict[which] = state

    def setMapMin(self, which, value):
        self.map_dict[which][0] = value

    def setMapMax(self, which, value):
        self.map_dict[which][1] = value

    def setMapMid(self, which, value):
        self.map_dict[which][3] = value

    def setXposition(self, which, x):
        self.streams[which].position.value = x

    def setYposition(self, which, x):
        params = [("y_dns", 1.0), ("y_pit", 1.0), ("y_len", 1.0), ("y_dev", 0.0),
                  ("y_pos", 0.0), ("y_trs", 0.0), ("y_dur", 0.0), ("y_amp", 1.0),
                  ("y_pan", 0.5), ("y_fif", 1.0), ("y_fiq", 1.0), ("y_ffr", 0.0),
                  ("y_fqr", 0.0)]
        for param, defval in params:
            if self.check_dict["%s_check" % param]:
                rng = self.map_dict["%s_map" % param]
                if rng[3] is None:
                    val = floatmap(x, rng[0], rng[1], rng[2])
                else:
                    if x < 0.5:
                        val = floatmap(x*2.0, rng[0], rng[3], rng[2])
                    else:
                        val = floatmap((x-0.5)*2.0, rng[3], rng[1], rng[2])
                getattr(self.streams[which], param).value = val
            else:
                getattr(self.streams[which], param).value = defval
        return

    def setActive(self, which, val):
        try:
            self.streams[which].setActive(val)
        except:
            pass
        if val == 1:
            if which not in self.activeStreams:
                self.activeStreams.append(which)
            if self.streams[which].granulator != None:
                if which in self.mixer.getKeys():
                    self.mixer.delInput(which)
                self.mixer.addInput(which, self.streams[which].granulator)
        else:
            if which in self.activeStreams:
                self.activeStreams.remove(which)
                self.mixer.delInput(which)

    def addFx(self, fx, key):
        self.fxs[key] = Fx(self.mixer[key], fx, self.chnls)
        self.stream_sum.value = Mix([st.granulator for st in self.streams.values()] + \
                                    [f.pan for f in self.fxs.values()], voices=self.chnls)

    def removeFx(self, key):
        del self.fxs[key]
        self.stream_sum.value = Mix([st.granulator for st in self.streams.values()] + \
                                    [f.pan for f in self.fxs.values()], voices=self.chnls)

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
            self.fxs[key].process.freq = val
        elif fx == 5:
            self.fxs[key].process.bitdepth = val
        elif fx == 6:
            self.fxs[key].process.transpo = val
        elif fx == 7:
            self.fxs[key].clip.min = -val
            self.fxs[key].clip.max = val
            self.fxs[key].clip.mul = 1.0 / val * 0.33
        elif fx == 8:
            self.fxs[key].lfo.freq = val
        elif fx == 9:
            self.fxs[key].process.freq = val

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
            self.fxs[key].process.decay = val
        elif fx == 5:
            self.fxs[key].process.srscale = val
        elif fx == 6:
            self.fxs[key].process.feedback = val
        elif fx == 7:
            self.fxs[key].process.freq = val
        elif fx == 8:
            self.fxs[key].flange.feedback = val
        elif fx == 9:
            self.fxs[key].process.detune = val

    def handleFxMul(self, key, val):
        self.fxs[key].pan.mul = val

    def handleFxPan(self, key, val):
        if self.chnls == 1:
            return
        self.fxs[key].pan.pan = val

    def start(self):
        for which in self.activeStreams:
            self.setActive(which, 1)
        self.refresh_met.play()
        self.server.start()
        self.server.amp = self.globalAmplitude

    def stop(self):
        self.refresh_met.stop()
        wx.CallAfter(self.server.stop)

    def refresh_screen(self):
        wx.CallAfter(self.refresh)

    def noteon(self, voice):
        if self.midiTriggerMethod == 0:
            pits = self.noteinpitch.get(True)
            vels = self.noteinvelocity.get(True)
            pit, vel = midiToTranspo(pits[voice]), vels[voice]
            self.createTraj(voice, pit, vel, pits[voice])
        elif self.midiTriggerMethod == 1:
            pits = self.noteinpitch.get(True)
            vels = self.noteinvelocity.get(True)
            pit, vel = pits[voice], vels[voice]
            if pit not in self.midiPitches:
                self.midiPitches.append(pit)
                self.createTraj(pit, midiToTranspo(pit), vel, pits[voice])
            else:
                self.midiPitches.remove(pit)
                self.deleteTraj(pit)

    def noteoff(self, voice):
        if self.midiTriggerMethod == 0:
            self.deleteTraj(voice)
