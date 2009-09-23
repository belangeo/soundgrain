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

import time, os, sys
from subprocess import Popen, PIPE
from ounk.ounklib import *
from constants import *
import Settings
    
def soundInfo(sndfile):
    chans, samprate, dur, frac, samps, bitrate = getSoundInfo(sndfile)
    return (chans, samprate, dur)
    
def checkForDrivers():
    setGlobalDuration(.01)
    sine(amplitude=0)
    startCsound(withevents=False)
    if sys.platform != 'win32':
        os.wait()
    else:
        time.sleep(3)
    f = open(os.path.join(OUNK_PATH, 'csoundlog.txt'), 'r')
    lines = f.readlines()
    if PLATFORM == 'win32':
        lines = [line for i, line in enumerate(lines) if (i % 2) == 0]
    f.close()
    
    total = len(lines)
    ind = lines.index('PortAudio: available output devices:\n')
    firstIndex = ind + 1
    for i in range(total - firstIndex):
        if lines[firstIndex + i].startswith('PortAudio:'):
            selectedDriver = lines[firstIndex + i].split("'")[1]
            lastIndex = firstIndex + i
            break
            
    driverList = [line.split(':')[1][:-1].lstrip() for line in lines[firstIndex:lastIndex]]
    return driverList, selectedDriver
    
def startAudio(_NUM, sndfile, audioDriver, outFile, module, *args):
    xlist = ['x%d' % i for i in range(_NUM)]
    oscxlist = ['/x%d' % i for i in range(_NUM)]
    ylist = ['y%d' % i for i in range(_NUM)]
    oscylist = ['/y%d' % i for i in range(_NUM)]
    amplist = ['amp%d' % i for i in range(_NUM)]
    oscamplist = ['/amp%d' % i for i in range(_NUM)]
    metrolist = ['metroVar%d' % i for i in range(_NUM)]
    oscmetrolist = ['/metroVar%d' % i for i in range(_NUM)]
    reclist = ['rec']
    oscreclist = ['/rec']
    paramslist = {  'Granulator': ['amplitude', 'grainsize', 'cutoff', 'globalAmp'],
                    'FFTReader': ['amplitude', 'cutoff', 'globalAmp'],
                    'FFTAdsyn': ['amplitude', 'cutoff', 'globalAmp']}[module]
    oscparamslist = {'Granulator': ['/amplitude', '/grainsize', '/cutoff', '/globalAmp'],
                    'FFTReader': ['/amplitude', '/cutoff', '/globalAmp'],
                    'FFTAdsyn': ['/amplitude', '/cutoff', '/globalAmp']}[module]
    totalbuslist = xlist + ylist + amplist + metrolist + reclist + paramslist
    totaloscbuslist = oscxlist + oscylist + oscamplist + oscmetrolist + oscreclist + oscparamslist
    portamentolist = [0.002] * len(totalbuslist)
    recindex = totalbuslist.index('rec')
    portamentolist[recindex] = 0
    
    if audioDriver != None:
        setAudioDevice(onumber = audioDriver)
        
    setGlobalDuration(-1)

    snd = sndfile
    chans, samprate, dur, frac, samps, bitrate = getSoundInfo(snd)
    
    setAudioAttributes(samplingrate=samprate, controlrate=samprate/10, sampleformat=bitrate, 
                       softbuffer=Settings.getSoftBuffer(), hardbuffer=Settings.getHardBuffer())
    
    setChannels(chans)
    tab = genSoundTable(snd)

    oscReceive( bus=totalbuslist, address=totaloscbuslist, port=8000, portamento=portamentolist)
    
    if module == 'Granulator':
        overlaps, trans, tr_check, tr_ymin, tr_ymax, cut_check, cut_ymin, cut_ymax, filt_type, ring_check, ring_ymin, ring_ymax, ring_wav, disto_check, disto_ymin, disto_ymax = \
            args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7], args[8], args[9], args[10], args[11], args[12], args[13], args[14], args[15]
            
        if len(trans) == 1 and trans[0] == 1:
            sizeVar = 'grainsize'
        else:    
            randomChoice(bus='sizeVar', choice=trans, rate=50)
            busMix(bus='size', in1='sizeVar', in2='grainsize', ftype='times')
            sizeVar = 'size'
        if tr_check == 0:
            pitVarlist = None
        else:
            pitVarlist = ['pitVar'+ele for ele in ylist]
            busMapper(pitVarlist, ylist, 0, 1, tr_ymin, tr_ymax)
        for i in range(len(amplist)):
            if tr_check == 0:
                pitVar = None
            else:
                pitVar = pitVarlist[i]
            granulator2(table=tab, overlaps=overlaps, pointerpos=frac, grainsize=0.001, amplitude=.5, 
                    grainsizeVar=sizeVar, pitch=1, pointerposVar=xlist[i], pitchVar=pitVar, amplitudeVar=amplist[i], out='outgrain%d' % i)
        if cut_check == 0:
            outbus = 'outgrain'
        else:
            cutVarlist = ['cutVar'+ele for ele in ylist]
            busMapper(cutVarlist, ylist, 0, 1, cut_ymin, cut_ymax)
            for i in range(len(amplist)):
                if filt_type == 0:
                    lowpass(input='outgrain%d' % i, cutoff=1, cutoffVar=cutVarlist[i], out='outlp%d' % i)
                elif filt_type == 1:
                    highpass(input='outgrain%d' % i, cutoff=1, cutoffVar=cutVarlist[i], out='outlp%d' % i)
                elif filt_type == 2:
                    bandpass(input='outgrain%d' % i, cutoff=1, bandwidth=.25, cutoffVar=cutVarlist[i], bandwidthVar=cutVarlist[i], out='outlp%d' % i)
                else:
                    bandreject(input='outgrain%d' % i, cutoff=1, bandwidth=.25, cutoffVar=cutVarlist[i], bandwidthVar=cutVarlist[i], out='outlp%d' % i)
            outbus = 'outlp'
        if ring_check == 1:
            ringVarlist = ['ringVar'+ele for ele in ylist]
            busMapper(ringVarlist, ylist, 0, 1, ring_ymin, ring_ymax)
            for i in range(len(amplist)):
                if ring_wav == 0:
                    sine(pitch=1, pitchVar=ringVarlist[i], out='wav%d' % i)
                if ring_wav == 1:
                    square(pitch=1, pitchVar=ringVarlist[i], out='wav%d' % i)
                if ring_wav == 2:
                    sawtooth(pitch=1, pitchVar=ringVarlist[i], out='wav%d' % i)
                ringMod(in1=outbus+str(i), in2='wav%d' % i, out='ring%d' % i)
            outbus = 'ring'
        if disto_check == 1:
            distoVarlist = ['distoVar'+ele for ele in ylist]
            busMapper(distoVarlist, ylist, 0, 1, disto_ymin, disto_ymax)
            for i in range(len(amplist)):
                distortion(input=outbus+str(i), drive=1, driveVar=distoVarlist[i], cutoff=10000, out='disto%d' % i)
            outbus = 'disto'
        for i in range(len(amplist)):
            lowpass(input=outbus+str(i), cutoff=1, cutoffVar='cutoff', out='lp')
        dcblock(input='lp', amplitudeVar='amplitude', out='sndout') 
               
    elif module == 'FFTReader':
        fftsize, overlaps, windowsize, tr_check, tr_ymin, tr_ymax, cut_check, cut_ymin, cut_ymax, filt_type, ring_check, ring_ymin, ring_ymax, ring_wav, disto_check, disto_ymin, disto_ymax = \
            args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7], args[8], args[9], args[10], args[11], args[12], args[13], args[14], args[15], args[16]   
        soundTableRead(table=tab, duration=dur, out='snd')
        if tr_check == 0:
            pitVarlist = None
        else:
            pitVarlist = ['pitVar'+ele for ele in ylist]
            busMapper(pitVarlist, ylist, 0, 1, tr_ymin, tr_ymax)
        for i in range(len(amplist)):
            if tr_check == 0:
                pitVar = None
            else:
                pitVar = pitVarlist[i]
            fftBufRead(input='snd', fftsize=fftsize, overlaps=overlaps, windowsize=windowsize, bufferlength=dur, 
                   transpo=1, pointerposVar=xlist[i], transpoVar=pitVar, amplitudeVar=amplist[i], out='fft%d' % i)
        if cut_check == 0:
            outbus = 'fft'
        else:
            cutVarlist = ['cutVar'+ele for ele in ylist]
            busMapper(cutVarlist, ylist, 0, 1, cut_ymin, cut_ymax)
            for i in range(len(amplist)):
                if filt_type == 0:
                    lowpass(input='fft%d' % i, cutoff=1, cutoffVar=cutVarlist[i], out='outlp%d' % i)
                elif filt_type == 1:
                    highpass(input='fft%d' % i, cutoff=1, cutoffVar=cutVarlist[i], out='outlp%d' % i)
                elif filt_type == 2:
                    bandpass(input='fft%d' % i, cutoff=1, bandwidth=.25, cutoffVar=cutVarlist[i], bandwidthVar=cutVarlist[i], out='outlp%d' % i)
                else:
                    bandreject(input='fft%d' % i, cutoff=1, bandwidth=.25, cutoffVar=cutVarlist[i], bandwidthVar=cutVarlist[i], out='outlp%d' % i)
            outbus = 'outlp'
        if ring_check == 1:
            ringVarlist = ['ringVar'+ele for ele in ylist]
            busMapper(ringVarlist, ylist, 0, 1, ring_ymin, ring_ymax)
            for i in range(len(amplist)):
                if ring_wav == 0:
                    sine(pitch=1, pitchVar=ringVarlist[i], out='wav%d' % i)
                if ring_wav == 1:
                    square(pitch=1, pitchVar=ringVarlist[i], out='wav%d' % i)
                if ring_wav == 2:
                    sawtooth(pitch=1, pitchVar=ringVarlist[i], out='wav%d' % i)
                ringMod(in1=outbus+str(i), in2='wav%d' % i, out='ring%d' % i)
            outbus = 'ring'
        if disto_check == 1:
            distoVarlist = ['distoVar'+ele for ele in ylist]
            busMapper(distoVarlist, ylist, 0, 1, disto_ymin, disto_ymax)
            for i in range(len(amplist)):
                distortion(input=outbus+str(i), drive=1, driveVar=distoVarlist[i], cutoff=10000, out='disto%d' % i)
            outbus = 'disto'
        for i in range(len(amplist)):
            lowpass(input=outbus+str(i), cutoff=1, cutoffVar='cutoff', out='lp')
        dcblock(input='lp', amplitudeVar='amplitude', out='sndout') 

    elif module == 'FFTAdsyn':
        fftsize, overlaps, windowsize, bins, first, incr, tr_check, tr_ymin, tr_ymax, cut_check, cut_ymin, cut_ymax, filt_type, ring_check, ring_ymin, ring_ymax, ring_wav, disto_check, disto_ymin, disto_ymax = \
            args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7], args[8], args[9], args[10], args[11], args[12], args[13], args[14], args[15], args[16], args[17], args[18], args[19]  
        soundTableRead(table=tab, duration=dur, out='snd')
        if tr_check == 0:
            pitVarlist = None
        else:
            pitVarlist = ['pitVar'+ele for ele in ylist]
            busMapper(pitVarlist, ylist, 0, 1, tr_ymin, tr_ymax)
        for i in range(len(amplist)):
            if tr_check == 0:
                pitVar = None
            else:
                pitVar = pitVarlist[i]
            fftBufAdsyn(input='snd', fftsize=fftsize, overlaps=overlaps, windowsize=windowsize, amplitudeVar=amplist[i],
                   numbins=bins, firstbin=first, binincr=incr, pointerposVar=xlist[i], transpoVar=pitVar, bufferlength=dur, out='fft%d' % i)          
        if cut_check == 0:
            outbus = 'fft'
        else:
            cutVarlist = ['cutVar'+ele for ele in ylist]
            busMapper(cutVarlist, ylist, 0, 1, cut_ymin, cut_ymax)
            for i in range(len(amplist)):
                if filt_type == 0:
                    lowpass(input='fft%d' % i, cutoff=1, cutoffVar=cutVarlist[i], out='outlp%d' % i)
                elif filt_type == 1:
                    highpass(input='fft%d' % i, cutoff=1, cutoffVar=cutVarlist[i], out='outlp%d' % i)
                elif filt_type == 2:
                    bandpass(input='fft%d' % i, cutoff=1, bandwidth=.25, cutoffVar=cutVarlist[i], bandwidthVar=cutVarlist[i], out='outlp%d' % i)
                else:
                    bandreject(input='fft%d' % i, cutoff=1, bandwidth=.25, cutoffVar=cutVarlist[i], bandwidthVar=cutVarlist[i], out='outlp%d' % i)
            outbus = 'outlp'
        if ring_check == 1:
            ringVarlist = ['ringVar'+ele for ele in ylist]
            busMapper(ringVarlist, ylist, 0, 1, ring_ymin, ring_ymax)
            for i in range(len(amplist)):
                if ring_wav == 0:
                    sine(pitch=1, pitchVar=ringVarlist[i], out='wav%d' % i)
                if ring_wav == 1:
                    square(pitch=1, pitchVar=ringVarlist[i], out='wav%d' % i)
                if ring_wav == 2:
                    sawtooth(pitch=1, pitchVar=ringVarlist[i], out='wav%d' % i)
                ringMod(in1=outbus+str(i), in2='wav%d' % i, out='ring%d' % i)
            outbus = 'ring'                   
        if disto_check == 1:
            distoVarlist = ['distoVar'+ele for ele in ylist]
            busMapper(distoVarlist, ylist, 0, 1, disto_ymin, disto_ymax)
            for i in range(len(amplist)):
                distortion(input=outbus+str(i), drive=1, driveVar=distoVarlist[i], cutoff=10000, out='disto%d' % i)
            outbus = 'disto'                   
        for i in range(len(amplist)):
            lowpass(input=outbus+str(i), cutoff=1, cutoffVar='cutoff', out='lp')
        dcblock(input='lp', amplitudeVar='amplitude', out='sndout') 

    toDac(input='sndout', amplitudeVar='globalAmp')

    beginTrigInst(trigbus = 'rec', trigval = 1, release = 0.05)
    recordPerf(name = os.path.join(os.path.expanduser('~'), outFile))
    endTrigInst()

    metro(bus='refresh', tempo=380)
    oscSend(input='refresh', address='/refresh', port=15000)

    for i in range(_NUM):
        metro(bus='metro%d' % i, tempo=1, tempoVar='metroVar%d' % i)
        oscSend(input='metro%d' % i, address='/metro%d' % i, port=15000)
    monitor()
    startCsound(withevents=False)

def stopAudio():
    stopCsound()
    processNumber(1)
      
def sendActiveTraj(val, which):
    sendOscControl(value=val, host=Settings.getHost(), port=Settings.getPort(), address='/amp%d' % which)
    
def sendXYControl(l, which):
    sendOscControl(value=l[0], host=Settings.getHost(), port=Settings.getPort(), address='/x%d' % which)
    sendOscControl(value=l[1], host=Settings.getHost(), port=Settings.getPort(), address='/y%d' % which)
                
def sendRecord():
    sendOscTrigger(value = 1, host=Settings.getHost(), port=Settings.getPort(), address = '/rec')
    
def sendControl(address, val):
    sendOscControl(value=float(val), host=Settings.getHost(), port=Settings.getPort(), address=address)
        
def splitSnd(file):
    cschnls = {'monaural': 1, 'stereo': 2, 'quad': 4, 'oct': 8}

    # retreive sound infos
    logPath = os.path.join(TEMP_PATH, 'log.txt')
    if PLATFORM == 'win32':
        cspipe1 = Popen('start /REALTIME /WAIT csound --logfile="%s" -U sndinfo "' % logPath + file + '"', shell=True, stdin=PIPE)
    elif PLATFORM == 'linux2':
        cspipe1 = Popen('csound --logfile="%s" -U sndinfo "' % logPath + file + '"', shell=True, stdin=PIPE)
    else:
        cspipe1 = Popen('/usr/local/bin/csound --logfile="%s" -U sndinfo "' % logPath + file + '"', shell=True, stdin=PIPE)
    cspipe1.wait()
    f = open(logPath, 'r')
    if systemPlatform == 'win32':
        lines = [line for i, line in enumerate(f.readlines()) if i%2 == 0]
        text = ''
        for line in lines:
            text += line
            text += '\n'
    else:        
        text = f.read()
    f.close()
    sp = text.split('srate')[-1]
    sp = sp.replace(',', '').replace('(', '').replace(')', '').replace('\n', ' ').replace('\t', '').strip()
    sp = sp.split(' ')

    samprate = eval(sp[0])
    chnls = cschnls[sp[1]]
    dur = eval(sp[sp.index('seconds')-1])
    nsamps = eval(sp[sp.index('sample')-1])
    bitrate = eval(sp[sp.index('bit')-1])
    typ = sp[sp.index('bit')+1]
    total_time = eval(sp[sp.index('seconds')-1])

    # create splitter.csd file
    splitterPath = os.path.join(TEMP_PATH, 'splitter.csd')
    splitter = open(splitterPath, "w")
    splitter.write('<CsoundSynthesizer>\n')
    splitter.write('<CsOptions>\n')
    splitter.write('-A -d -n -b256 -B1024\n')
    splitter.write('</CsOptions>\n')
    splitter.write('<CsInstruments>\n')
    
    splitter.write('sr = %s\n' % samprate)
    splitter.write('ksmps = 100\n')
    splitter.write('nchnls = 1\n')
    
    splitter.write('instr 1\n')

    outPath = TEMP_PATH
    sndName = os.path.split(file)[1].rsplit('.',1)[0]
    sndFileInput = file.replace('\\', '/')
    
    splitter.write('idur filelen "%s"\n' % sndFileInput)
    splitter.write('p3 = idur\n')
    
    outs = ', '.join(['a%d' % i for i in range(chnls)])
    splitter.write('%s diskin2 "%s", 1, 0, 0, 8, 0\n' % (outs, sndFileInput))
    
    for i in range(chnls):
        sndOutName = sndName + '-%d.aif' % i
        sndOutFile = os.path.join(outPath, sndOutName).replace('\\', '/')
        splitter.write('fout "%s", %d, a%d\n' % (sndOutFile, {16:2, 24:8}[bitrate], i))
    splitter.write('endin\n')
    
    splitter.write('</CsInstruments>\n')
    splitter.write('<CsScore>\n')
    splitter.write('i1 0 1\n')
    splitter.write('</CsScore>\n')
    splitter.write('</CsoundSynthesizer>\n')
    splitter.close()

    if PLATFORM == 'win32':
        cspipe2 = Popen('start /REALTIME /WAIT csound "%s"' % splitterPath, shell=True)
    elif PLATFORM == 'linux2':    
        cspipe2 = Popen('csound "%s"' % splitterPath, shell=True, stdin=PIPE)
    else:    
        cspipe2 = Popen('/usr/local/bin/csound "%s"' % splitterPath, shell=True, stdin=PIPE)
    cspipe2.wait()
    
def recordInput(audioDriver):
    setAudioAttributes(samplingrate=44100, controlrate=4410, softbuffer=Settings.getSoftBuffer(), hardbuffer=Settings.getHardBuffer())
    
    if audioDriver != None:
        setAudioDevice(onumber = audioDriver)
        
    setGlobalDuration(-1)
    setChannels(1)

    inputMic()
    recordPerf(os.path.join(TEMP_PATH, 'sndtemp'), nameinc=False)

    startCsound(nosound=True, withevents=False)
