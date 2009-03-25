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

systemPlatform = sys.platform

def soundInfo(sndfile):
    setGlobalDuration(.1)
    snd = sndfile
    chans, samprate, dur, frac, samps = getSoundInfo(snd)
    startCsound()
    return (chans, samprate, dur)
    
def checkForDrivers():
    setGlobalDuration(.01)
    sine(amplitude=0)
    startCsound()
    if sys.platform != 'win32':
        os.wait()
    else:
        time.sleep(3)
    f = open(os.path.join(os.path.expanduser('~'), '.ounk', 'csoundlog.txt'), 'r')
    lines = f.readlines()
    if systemPlatform == 'win32':
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
    
    if audioDriver != None:
        setAudioDevice(onumber = audioDriver)
        
    setGlobalDuration(-1)

    snd = sndfile
    chans, samprate, dur, frac, samps = getSoundInfo(snd)
    
    setAudioAttributes(samplingrate=samprate, controlrate=samprate/10, softbuffer=512, hardbuffer=2048)
    
    setChannels(chans)
    tab = genSoundTable(snd)

    oscReceive( bus=xlist + ylist + amplist, adress=oscxlist + oscylist + oscamplist, port=8000, portamento=0.002)
    oscReceive(bus = 'rec', adress = '/rec', port = 8001)
    
    if module == 'Granulator':
        overlaps, trans = args[0], args[1]
        oscReceive(bus = ['amplitude', 'grainsize'], adress = ['/amplitude', '/grainsize'], port = 8002, portamento = 0.005)
        randomChoice(bus='sizeVar', choice=trans, rate=50)
        busMix(bus='size', in1='sizeVar', in2='grainsize', ftype='times')
        granulator2(table=tab, overlaps=overlaps, pointerpos=frac, grainsize=0.001, amplitude=.5, 
                    grainsizeVar='size', pitch=1, pointerposVar=xlist, pitchVar=ylist, amplitudeVar=amplist, out='outgrain')
        dcblock(input='outgrain', amplitudeVar='amplitude')                
    elif module == 'FFTReader':
        fftsize, overlaps, windowsize, keepformant = args[0], args[1], args[2], args[3]
        oscReceive(bus = 'amplitude', adress = '/amplitude', port = 8002, portamento = 0.005)
        soundTableRead(table=tab, duration=dur, out='snd')
        fftBufRead(input='snd', fftsize=fftsize, overlaps=overlaps, windowsize=windowsize, bufferlength=dur, 
                   transpo=1, keepformant=keepformant, pointerposVar=xlist, transpoVar=ylist, amplitudeVar=amplist, out='fft')
        dcblock(input='fft', amplitudeVar='amplitude')                
    elif module == 'FFTRingMod':
        oscReceive(bus = ['amplitude', 'transpo'], adress = ['/amplitude', '/transpo'], port = 8002, portamento = 0.005)
        for i in range(len(xlist)):
            soundTableRead(table=tab, duration=dur, out='snd')
            fftBufRead(input='snd', fftsize=1024, overlaps=4, windowsize=1024, bufferlength=dur, 
                   transpo=1, transpoVar='transpo', keepformant=0, pointerposVar=xlist[i], amplitudeVar=amplist[i], out='fft%d' % i)
            sine(pitch = 100, pitchVar=ylist[i], out='sin%d' % i)
            ringMod(in1='fft%d' % i, in2='sin%d' % i, amplitudeVar='amplitude')
    elif module == 'FFTAdsyn':
        fftsize, overlaps, windowsize, bins, first, incr = args[0], args[1], args[2], args[3], args[4], args[5]
        oscReceive(bus = 'amplitude', adress = '/amplitude', port = 8002, portamento = 0.005)
        soundTableRead(table=tab, duration=dur, out='snd')
        fftBufAdsyn(input='snd', fftsize=fftsize, overlaps=overlaps, windowsize=windowsize, amplitudeVar=amplist,
                   numbins=bins, firstbin=first, binincr=incr, pointerposVar=xlist, transpoVar=ylist, bufferlength=dur, out='fft')
        dcblock(input='fft', amplitudeVar='amplitude')                
    elif module == 'FMCrossSynth':
        fftsize, overlaps, windowsize, pitch = args[0], args[1], args[2], args[3]
        oscReceive(bus = ['amplitude', 'transpo', 'carrier', 'modulator', 'index'], 
                   adress = ['/amplitude','/transpo', '/carrier', '/modulator', '/index'], port = 8002, portamento = 0.005)
        soundTableRead(table=tab, duration=dur, out='snd')
        for i in range(len(xlist)):
            fftBufRead(input='snd', fftsize=fftsize, overlaps=overlaps, windowsize=windowsize, bufferlength=dur, 
                   transpo=1, transpoVar='transpo', keepformant=0, pointerposVar=xlist[i], amplitudeVar=amplist[i], out='reader%d' % i)
            freqMod(pitch=pitch, modulator=1, index=1, carrierVar='carrier', modulatorVar='modulator', indexVar='index', 
                    pitchVar=ylist[i], out='fm%d' % i)
            #train(pitch=pitch, pitchVar=ylist[i], damp=.5, out='fm%d' % i)
            crossSynth(in1='fm%d' % i, in2='reader%d' % i, out='fft')
        dcblock(input='fft', amplitudeVar='amplitude')                
    elif module == 'AutoModulation':
        oscReceive(bus = 'amplitude', adress = '/amplitude', port = 8002, portamento = 0.005)
        tablesMod(table1=tab, table2=tab, amplitudeVar=amplist, index1Var=xlist, index2Var=ylist, out='mod')
        dcblock(input='mod', amplitudeVar='amplitude')  

    beginTrigInst(trigbus = 'rec', trigval = 1, release = 0.05)
    recordPerf(name = outFile)
    endTrigInst()
            
    startCsound()

def stopAudio():
    stopCsound()
    processNumber(1)
       
def sendXYControls(list):
    if list:
        for i, l in enumerate(list):
            if l:
                sendOscControl(value=1, adress='/amp%d' % i)
                sendOscControl(value=l[0], adress='/x%d' % i)
                sendOscControl(value=l[1], adress='/y%d' % i)
            else:
                sendOscControl(value=0, adress='/amp%d' % i)

def sendRecord():
    sendOscTrigger(value = 1, adress = '/rec', port = 8001)
    
def sendControl(adress, val):
    sendOscControl(value=float(val), adress=adress, port=8002)
        
def splitSnd(file):
    cschnls = {'monaural': 1, 'stereo': 2, 'quad': 4, 'oct': 8}

    # retreive sound infos
    if systemPlatform == 'darwin':
        cspipe1 = Popen('/usr/local/bin/csound --logfile=log.txt -U sndinfo "' + file + '"', shell=True, stdin=PIPE)
    elif systemPlatform == 'win32':
        cspipe1 = Popen('start /REALTIME /WAIT csound --logfile=log.txt -U sndinfo "' + file + '"', shell=True, stdin=PIPE)
    cspipe1.wait()
    f = open('log.txt', 'r')
    text = f.read()
    f.close()
    os.remove('log.txt')
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
    splitter = open("splitter.csd", "w")
    splitter.write('<CsoundSynthesizer>\n')
    splitter.write('<CsOptions>\n')
    splitter.write('-A -d -n -b256 -B1024\n')
    splitter.write('</CsOptions>\n')
    splitter.write('<CsInstruments>\n')
    
    splitter.write('sr = %s\n' % samprate)
    splitter.write('ksmps = 100\n')
    splitter.write('nchnls = 1\n')
    
    splitter.write('instr 1\n')
    
    path = os.path.split(file)[0]
    outPath = os.path.expanduser('~')
    if systemPlatform == 'darwin':    
        splitter.write('Spath strcpy "%s/"\n' % path)
        splitter.write('SoutPath strcpy "%s/"\n' % outPath)
    elif systemPlatform == 'win32':    
        splitter.write('Spath strcpy "%s/"\n' % path)
        splitter.write('SoutPath strcpy "%s/"\n' % outPath)
    splitter.write('Sname strcpy "%s"\n' % os.path.split(file)[1].rsplit('.',1)[0])                                
    splitter.write('SinFileName strcat Sname, ".%s"\n' % os.path.split(file)[1].rsplit('.',1)[1])
    splitter.write('SfileInput strcat Spath, SinFileName\n')
    
    for i in range(chnls):
        splitter.write('SoutName%d strcat Sname, "-%d.aif"\n' % (i, i)) 
        splitter.write('SfileOutput%d strcat SoutPath, SoutName%d\n' % (i, i))
    
    splitter.write('idur filelen SfileInput\n')
    splitter.write('p3 = idur\n')
    
    outs = ', '.join(['a%d' % i for i in range(chnls)])
    splitter.write('%s diskin2 SfileInput, 1, 0, 0, 8, 0\n' % outs)
    
    for i in range(chnls):
        splitter.write('fout SfileOutput%d, %d, a%d\n' % (i, {16:2, 24:8}[bitrate], i))
    splitter.write('endin\n')
    
    splitter.write('</CsInstruments>\n')
    splitter.write('<CsScore>\n')
    splitter.write('i1 0 1\n')
    splitter.write('</CsScore>\n')
    splitter.write('</CsoundSynthesizer>\n')
    splitter.close()

    if systemPlatform == 'darwin':    
        cspipe2 = Popen('/usr/local/bin/csound splitter.csd', shell=True, stdin=PIPE)
    elif systemPlatform == 'win32':
        cspipe2 = Popen('start /REALTIME /WAIT csound splitter.csd', shell=True, stdin=PIPE)
    cspipe2.wait()
    #os.remove('splitter.csd')
    