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
import os, math, random, wx
import  wx.lib.scrolledpanel as scrolled
from Resources.constants import *
from Resources.audio import soundInfo
from Resources.widgets import ControlKnob
from pyolib._wxwidgets import ControlSlider, VuMeter, BACKGROUND_COLOUR

class ControlPanel(scrolled.ScrolledPanel):
    def __init__(self, parent, surface):
        scrolled.ScrolledPanel.__init__(self, parent, -1)
        self.SetBackgroundColour(BACKGROUND_COLOUR)
        self.parent = parent
        self.surface = surface
        self.type = 0
        self.selected = 0
        self.selectedOkToChange = True
        self.sndPath = ""
        self.sndDur = 0.0
        self.amplitude = 1
        self.nchnls = 2
        self.samplingRate = 44100
        self.fileformat = 0
        self.sampletype = 0
        self.tempState = None

        box = wx.BoxSizer(wx.VERTICAL)

        box.Add(wx.StaticText(self, -1, "Trajectories"), 0, wx.CENTER|wx.TOP, 3)

        typeBox = wx.BoxSizer(wx.HORIZONTAL)
        popupBox = wx.BoxSizer(wx.VERTICAL)
        self.trajType = wx.Choice(self, -1, choices = ['Free', 'Circle', 'Oscil', 'Line'])
        self.trajType.SetSelection(0)
        popupBox.Add(self.trajType)
        typeBox.Add(popupBox, 0, wx.CENTER|wx.RIGHT, 5)

        # TODO: Check the size of this button on Windows and OSX
        self.closedToggle = wx.ToggleButton(self, -1, 'Closed', size=self.trajType.GetSize())
        font = self.closedToggle.GetFont()
        if PLATFORM.startswith('linux') or PLATFORM == 'win32':
            font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.closedToggle.SetFont(font)
        typeBox.Add(self.closedToggle, wx.CENTER|wx.RIGHT, 5 )
        box.Add(typeBox, 0, wx.CENTER|wx.ALL, 5)

        self.notebook = wx.Notebook(self, -1, style=wx.BK_DEFAULT | wx.EXPAND)
        self.notebook.SetBackgroundColour(BACKGROUND_COLOUR)
        self.drawing = DrawingParameters(self.notebook)
        self.playback = PlaybackParameters(self.notebook)
        self.notebook.AddPage(self.drawing, "Drawing")
        self.notebook.AddPage(self.playback, "Playback")
        box.Add(self.notebook, 0, wx.ALL, 5)

        # EQ
        eqTitle = wx.StaticText(self, id=-1, label="4 Bands Equalizer")
        box.Add(eqTitle, 0, wx.CENTER)

        eqFreqBox = wx.BoxSizer(wx.HORIZONTAL)
        self.knobEqF1 = ControlKnob(self, 40, 250, 100, label='Freq 1', outFunction=self.changeEqF1)
        eqFreqBox.Add(self.knobEqF1, 0, wx.LEFT | wx.RIGHT, 20)
        self.knobEqF1.setFloatPrecision(2)
        self.knobEqF2 = ControlKnob(self, 300, 1000, 500, label='Freq 2', outFunction=self.changeEqF2)
        eqFreqBox.Add(self.knobEqF2, 0, wx.LEFT | wx.RIGHT, 4)
        self.knobEqF2.setFloatPrecision(2)
        self.knobEqF3 = ControlKnob(self, 1200, 5000, 2000, label='Freq 3', outFunction=self.changeEqF3)
        eqFreqBox.Add(self.knobEqF3, 0, wx.LEFT | wx.RIGHT, 20)
        self.knobEqF3.setFloatPrecision(2)

        box.Add(eqFreqBox)

        eqGainBox = wx.BoxSizer(wx.HORIZONTAL)
        self.knobEqA1 = ControlKnob(self, -40, 18, 0, label='B1 gain', outFunction=self.changeEqA1)
        eqGainBox.Add(self.knobEqA1, 0, wx.LEFT | wx.RIGHT, 5)
        self.knobEqA2 = ControlKnob(self, -40, 18, 0, label='B2 gain', outFunction=self.changeEqA2)
        eqGainBox.Add(self.knobEqA2, 0, wx.LEFT | wx.RIGHT, 5)
        self.knobEqA3 = ControlKnob(self, -40, 18, 0, label='B3 gain', outFunction=self.changeEqA3)
        eqGainBox.Add(self.knobEqA3, 0, wx.LEFT | wx.RIGHT, 5)
        self.knobEqA4 = ControlKnob(self, -40, 18, 0, label='B4 gain', outFunction=self.changeEqA4)
        eqGainBox.Add(self.knobEqA4, 0, wx.LEFT | wx.RIGHT, 5)

        box.Add(eqGainBox)

        box.Add(wx.StaticLine(self, size=(210, 1)), 0, wx.ALL, 5)

        #Compress
        compTitle = wx.StaticText(self, id=-1, label="Dynamic Compressor")
        box.Add(compTitle, 0, wx.CENTER)

        cpKnobBox = wx.BoxSizer(wx.HORIZONTAL)
        self.knobComp1 = ControlKnob(self, -60, 0, -3, label='Thresh', outFunction=self.changeComp1)
        cpKnobBox.Add(self.knobComp1, 0, wx.LEFT | wx.RIGHT, 5)
        self.knobComp2 = ControlKnob(self, 1, 10, 2, label='Ratio', outFunction=self.changeComp2)
        cpKnobBox.Add(self.knobComp2, 0, wx.LEFT | wx.RIGHT, 5)
        self.knobComp3 = ControlKnob(self, 0.001, 0.5, 0.05, label='Rise', outFunction=self.changeComp3)
        cpKnobBox.Add(self.knobComp3, 0, wx.LEFT | wx.RIGHT, 5)
        self.knobComp4 = ControlKnob(self, 0.01, 1, .2, label='Fall', outFunction=self.changeComp4)
        cpKnobBox.Add(self.knobComp4, 0, wx.LEFT | wx.RIGHT, 5)

        box.Add(cpKnobBox)

        box.Add(wx.StaticLine(self, size=(210, 1)), 0, wx.ALL, 5)

        box.Add(wx.StaticText(self, -1, "Global amplitude (dB)"), 0, wx.LEFT | wx.TOP, 10)
        ampBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_amp = ControlSlider(self, -60, 18, 0, size=(200, 16), outFunction=self.handleAmp)
        ampBox.Add(self.sl_amp, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(ampBox, 0, wx.LEFT | wx.RIGHT, 5)
        box.AddSpacer(10)
        self.meter = VuMeter(self, size=(200,11))
        self.meter.setNumSliders(self.nchnls)
        box.Add(self.meter, 0, wx.LEFT, 10)
        box.AddSpacer(5)

        box.Add(wx.StaticLine(self, size=(210, 1)), 0, wx.ALL, 5)

        box.Add(wx.StaticText(self, -1, "Project Settings"), 0, wx.CENTER | wx.ALL, 5)

        projSettingsBox = wx.BoxSizer(wx.HORIZONTAL)
        srBox = wx.BoxSizer(wx.VERTICAL)
        srText = wx.StaticText(self, -1, "Rate")
        srBox.Add(srText, 0, wx.CENTER | wx.LEFT | wx.RIGHT, 5)
        self.pop_sr = wx.Choice(self, -1, choices = ['44100', '48000', '96000'], size=(80,-1))
        self.pop_sr.SetSelection(0)
        self.pop_sr.Bind(wx.EVT_CHOICE, self.handleSamplingRate)
        srBox.Add(self.pop_sr, 0, wx.LEFT | wx.RIGHT, 5)
        chnlsBox = wx.BoxSizer(wx.VERTICAL)
        chnlsText = wx.StaticText(self, -1, "Chnls")
        chnlsBox.Add(chnlsText, 0, wx.CENTER  | wx.LEFT | wx.RIGHT, 5)
        self.tx_chnls = wx.TextCtrl(self, -1, "2", size=(60, -1), style=wx.TE_PROCESS_ENTER)
        self.tx_chnls.Bind(wx.EVT_TEXT_ENTER, self.handleNchnls)
        chnlsBox.Add(self.tx_chnls, 0, wx.LEFT | wx.RIGHT, 5)
        projSettingsBox.Add(srBox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        projSettingsBox.Add(chnlsBox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        box.Add(projSettingsBox, 0, wx.ALIGN_CENTER, 5)

        box.Add(wx.StaticLine(self, size=(210, 1)), 0, wx.ALL, 5)

        soundBox = wx.BoxSizer(wx.HORIZONTAL)
        self.tog_audio = wx.ToggleButton(self, -1, "Start", size=(80,-1))
        self.tog_audio.SetFont(font)
        self.tog_audio.Disable()
        soundBox.Add(self.tog_audio, 0, wx.CENTER |  wx.LEFT | wx.RIGHT, 5)
        box.Add(soundBox, 0, wx.CENTER | wx.ALL, 5)

        box.Add(wx.StaticLine(self, size=(210, 1)), 0, wx.ALL, 5)

        box.Add(wx.StaticText(self, -1, "Record Settings"), 0, wx.CENTER | wx.ALL, 5)

        recSettingsBox = wx.BoxSizer(wx.HORIZONTAL)
        fileformatBox = wx.BoxSizer(wx.VERTICAL)
        fileformatText = wx.StaticText(self, -1, "Format")
        fileformatBox.Add(fileformatText, 0, wx.CENTER | wx.LEFT | wx.RIGHT, 5)
        self.pop_fileformat = wx.Choice(self, -1, choices=EXPORT_FORMATS, size=(80,-1))
        self.pop_fileformat.SetSelection(0)
        self.pop_fileformat.Bind(wx.EVT_CHOICE, self.handleFileFormat)
        fileformatBox.Add(self.pop_fileformat, 0, wx.LEFT | wx.RIGHT, 5)
        sampletypeBox = wx.BoxSizer(wx.VERTICAL)
        sampletypeText = wx.StaticText(self, -1, "Type")
        sampletypeBox.Add(sampletypeText, 0, wx.CENTER  | wx.LEFT | wx.RIGHT, 5)
        self.pop_sampletype = wx.Choice(self, -1, choices=EXPORT_TYPES)
        self.pop_sampletype.SetSelection(0)
        self.pop_sampletype.Bind(wx.EVT_CHOICE, self.handleSampleType)
        sampletypeBox.Add(self.pop_sampletype, 0, wx.LEFT | wx.RIGHT, 5)
        recSettingsBox.Add(fileformatBox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        recSettingsBox.Add(sampletypeBox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        box.Add(recSettingsBox, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)

        rec1Box = wx.BoxSizer(wx.HORIZONTAL)

        self.tx_rec_folder = wx.TextCtrl( self, -1, "~/Desktop", size=(120, -1))
        rec1Box.Add(self.tx_rec_folder, 0, wx.LEFT | wx.RIGHT, 10)
        self.but_folder = wx.ToggleButton(self, -1, "Choose", size=(65,-1))
        self.but_folder.SetFont(font)
        rec1Box.Add(self.but_folder, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND | wx.RIGHT, 10)

        rec2Box = wx.BoxSizer(wx.HORIZONTAL)

        self.tx_output = wx.TextCtrl( self, -1, "snd", size=(120, -1))
        rec2Box.Add(self.tx_output, 0, wx.LEFT | wx.RIGHT, 10)
        self.tog_record = wx.ToggleButton(self, -1, "Start Rec", size=(65,-1))
        self.tog_record.SetFont(font)
        rec2Box.Add(self.tog_record, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND | wx.RIGHT, 10)

        box.Add(wx.StaticText(self, -1, "Destination"), 0, wx.LEFT | wx.RIGHT, 17)
        box.Add(rec1Box, 0, wx.EXPAND | wx.BOTTOM  | wx.LEFT | wx.RIGHT, 5)
        box.Add(wx.StaticText(self, -1, "Filename"), 0, wx.LEFT | wx.RIGHT, 17)
        box.Add(rec2Box, 0, wx.EXPAND | wx.BOTTOM  | wx.LEFT | wx.RIGHT, 5)


        self.Bind(wx.EVT_CHOICE, self.handleType, self.trajType)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.handleClosed, self.closedToggle)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.handleAudio, self.tog_audio)
        self.tx_output.Bind(wx.EVT_CHAR, self.handleOutput)
        self.tx_rec_folder.Bind(wx.EVT_CHAR, self.handleOutput)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.handleRecord, self.tog_record)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.chooseRecFolder, self.but_folder)

        self.SetAutoLayout(True)
        self.SetSizerAndFit(box)
        self.SetupScrolling(scroll_x = False)

    def changeEqF1(self, x):
        self.parent.sg_audio.setEqFreq(0, x)

    def changeEqF2(self, x):
        self.parent.sg_audio.setEqFreq(1, x)

    def changeEqF3(self, x):
        self.parent.sg_audio.setEqFreq(2, x)

    def getEqFreqs(self):
        return [self.knobEqF1.GetValue(), self.knobEqF2.GetValue(), self.knobEqF3.GetValue()]

    def setEqFreqs(self, freqs):
        self.knobEqF1.SetValue(freqs[0])
        self.knobEqF2.SetValue(freqs[1])
        self.knobEqF3.SetValue(freqs[2])

    def changeEqA1(self, x):
        self.parent.sg_audio.setEqGain(0, math.pow(10.0, x * 0.05))

    def changeEqA2(self, x):
        self.parent.sg_audio.setEqGain(1, math.pow(10.0, x * 0.05))

    def changeEqA3(self, x):
        self.parent.sg_audio.setEqGain(2, math.pow(10.0, x * 0.05))

    def changeEqA4(self, x):
        self.parent.sg_audio.setEqGain(3, math.pow(10.0, x * 0.05))

    def getEqAmps(self):
        return [self.knobEqA1.GetValue(), self.knobEqA2.GetValue(),
                self.knobEqA3.GetValue(), self.knobEqA4.GetValue()]

    def setEqAmps(self, amps):
        self.knobEqA1.SetValue(amps[0])
        self.knobEqA2.SetValue(amps[1])
        self.knobEqA3.SetValue(amps[2])
        self.knobEqA4.SetValue(amps[3])

    def changeComp1(self, x):
        self.parent.sg_audio.setCompParam("thresh", x)

    def changeComp2(self, x):
        self.parent.sg_audio.setCompParam("ratio", x)

    def changeComp3(self, x):
        self.parent.sg_audio.setCompParam("risetime", x)

    def changeComp4(self, x):
        self.parent.sg_audio.setCompParam("falltime", x)

    def getCompValues(self):
        return [self.knobComp1.GetValue(), self.knobComp2.GetValue(),
                self.knobComp3.GetValue(), self.knobComp4.GetValue()]

    def setCompValues(self, vals):
        self.knobComp1.SetValue(vals[0])
        self.knobComp2.SetValue(vals[1])
        self.knobComp3.SetValue(vals[2])
        self.knobComp4.SetValue(vals[3])

    def checkEnableWidgets(self):
        if self.type == 0:
            self.closedToggle.Enable()
        else:
            self.closedToggle.Disable()
        if self.type == 2:
            self.drawing.sl_period.Enable()
            self.drawing.sl_scaling.Enable()
        else:
            self.drawing.sl_period.Disable()
            self.drawing.sl_scaling.Disable()

    # TODO: replace all these handle, get, set, with single event
    def handleType(self, event):
        self.processType(event.GetInt())

    def getType(self):
        return self.type

    def setType(self, type):
        self.trajType.SetSelection(type)
        self.processType(type)

    def processType(self, type):
        self.type = type
        self.surface.setMode(type)
        self.checkEnableWidgets()

    def handleClosed(self, event):
        self.surface.setClosed(event.GetInt())

    def getClosed(self):
        return self.closedToggle.GetValue()

    def setClosed(self, closed):
        self.closedToggle.SetValue(closed)
        self.surface.setClosed(closed)

    def handleCutoff(self, val):
        for traj in self.surface.getAllTrajectories():
            traj.setFilterFreq(val)

    def getCutoff(self):
        return self.drawing.sl_cutoff.GetValue()

    def setCutoff(self, cutoff):
        self.drawing.sl_cutoff.SetValue(cutoff)
        for traj in self.surface.getAllTrajectories():
            traj.setFilterFreq(cutoff)

    def handleQ(self, val):
        for traj in self.surface.getAllTrajectories():
            traj.setFilterQ(val)

    def getQ(self):
        return self.drawing.sl_q.GetValue()

    def setQ(self, q):
        self.drawing.sl_q.SetValue(q)
        for traj in self.surface.getAllTrajectories():
            traj.setFilterQ(q)

    def handlePeriod(self, val):
        self.surface.setOscilPeriod(val)

    def getPeriod(self):
        return self.surface.getOscilPeriod()

    def setPeriod(self, period):
        self.drawing.sl_period.SetValue(period)
        self.surface.setOscilPeriod(period)

    def handleScaling(self, val):
        self.surface.setOscilScaling(val)

    def getScaling(self):
        return self.surface.getOscilScaling()

    def setScaling(self, scaling):
        self.drawing.sl_scaling.SetValue(scaling)
        self.surface.setOscilScaling(scaling)

    def resetPlaybackSliders(self):
        selToMax = False
        if self.selected == MAX_STREAMS:
            self.selected = 0
            selToMax = True
        timeSpeed = self.surface.getTrajectory(self.selected).getTimeSpeed()
        self.setTimerSpeed(timeSpeed)
        step = self.surface.getTrajectory(self.selected).getStep()
        self.setStep(step)
        amp = self.surface.getTrajectory(self.selected).getAmplitude()
        self.setTrajAmp(amp)
        if selToMax:
            self.selected = MAX_STREAMS
        self.surface.needBitmap = True

    def handleSelected(self, event):
        if event.GetInt() != self.selected:
            self.selected = event.GetInt()
            self.selectedOkToChange = False
            if self.selected == MAX_STREAMS:
                self.selectedOkToChange = False
            self.resetPlaybackSliders()

    def setSelected(self, selected):
        self.playback.tog_traj.SetSelection(selected)
        self.selected = selected
        self.surface.setSelectedById(selected)
        self.resetPlaybackSliders()

    def getSelected(self):
        return self.selected

    def handlePopupFocus(self, evt):
        self.selectedOkToChange = False
        evt.Skip()

    def handleTimerSpeed(self, val):
        if self.selectedOkToChange:
            if self.selected == MAX_STREAMS:
                for t in self.surface.getActiveTrajectories():
                    t.setTimeSpeed(val)
            else:
                self.surface.getTrajectory(self.selected).setTimeSpeed(val)
        else:
            self.selectedOkToChange = True

    def setTimerSpeed(self, timeSpeed):
        self.playback.sl_timespeed.SetValue(timeSpeed, self.selectedOkToChange)

    def sendTrajSpeed(self, which, speed):
        self.parent.sg_audio.setMetroTime(which, speed * 0.001)

    def handleStep(self, val):
        if self.selectedOkToChange:
            if self.selected == MAX_STREAMS:
                for t in self.surface.getActiveTrajectories():
                    t.setStep(val)
            else:
                self.surface.getTrajectory(self.selected).setStep(val)
        else:
            self.selectedOkToChange = True

    def setStep(self, step):
        self.playback.sl_step.SetValue(step, self.selectedOkToChange)

    def handleTrajAmp(self, val):
        val = pow(10.0, float(val) * 0.05)
        if self.selectedOkToChange:
            if self.selected == MAX_STREAMS:
                for t in self.surface.getActiveTrajectories():
                    t.setAmplitude(val)
                    self.parent.sg_audio.setTrajAmplitude(t.label-1, val)
            else:
                self.surface.getTrajectory(self.selected).setAmplitude(val)
                self.parent.sg_audio.setTrajAmplitude(self.selected, val)
        else:
            self.selectedOkToChange = True

    def setTrajAmp(self, val):
        if val <= 0.0:
            val = 0.0001
        self.playback.sl_amp.SetValue(20.0 * math.log10(val), self.selectedOkToChange)

    def handleAmp(self, val):
        self.amplitude = pow(10.0, float(val) * 0.05)
        self.sendAmp()

    def getAmp(self):
        return self.amplitude

    def setAmp(self, amp):
        if amp <= 0.0:
            amp = 0.0001
        self.sl_amp.SetValue(20.0 * math.log10(amp))
        self.amplitude = amp

    def sendAmp(self):
        self.parent.sg_audio.setGlobalAmp(self.amplitude)

    def handleLoad(self):
        dlg = wx.FileDialog(self, message="Choose a sound file",
                            defaultDir=self.parent.lastAudioPath,
                            wildcard=AUDIO_WILDCARD, style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            sndPath = dlg.GetPath()
            self.loadSound(ensureNFD(sndPath))
            self.parent.lastAudioPath = os.path.split(sndPath)[0]
        dlg.Destroy()

    def handleInsert(self):
        ok = False
        dlg = wx.FileDialog(self, message="Choose a sound file to insert",
                            defaultDir=self.parent.lastAudioPath,
                            wildcard=AUDIO_WILDCARD, style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            ok = True
            sndPath = dlg.GetPath()
            self.parent.lastAudioPath = os.path.split(sndPath)[0]
        dlg.Destroy()
        if ok:
            self.insertSound(ensureNFD(sndPath), True)

    def loadSound(self, sndPath, force=False):
        if sndPath:
            if os.path.isfile(sndPath):
                self.sndPath = sndPath
                self.parent.sg_audio.loadSnd(toSysEncoding(self.sndPath))
                chnls, samprate, dur = soundInfo(toSysEncoding(self.sndPath))
                self.sndDur = dur
                self.chnls = chnls
                self.sndInfoStr = u'Loaded sound: %s,  Sr: %i Hz,  Channels: %s,  Duration: %.3f sec' % (self.sndPath, int(samprate), chnls, dur)
                if self.parent.draw:
                    if not self.sndPath in self.surface.bitmapDict.keys() or force:
                        self.parent.log("Drawing waveform...")
                        self.surface.analyse(self.sndPath)
                    else:
                        self.surface.list = self.surface.bitmapDict[self.sndPath]
                        self.surface.create_bitmap()
                self.logSndInfo()
            elif os.path.isfile(os.path.join(self.parent.currentPath, os.path.split(sndPath)[1])):
                self.loadSound(os.path.join(self.parent.currentPath, os.path.split(sndPath)[1]), force)
            elif ":\\" in sndPath:
                # Handle windows path...
                self.loadSound(os.path.join(self.parent.currentPath, sndPath.split("\\")[-1]), force)
            else:
                self.parent.log('Sound file "%s" does not exist!' % sndPath)
        else:
            self.parent.log("")

    def insertSound(self, sndPath, force=False):
        if not self.sndPath:
            self.loadSound(sndPath)
            return
        if sndPath:
            if os.path.isfile(sndPath):
                self.sndPath = "Mixed sound " + str(random.randint(0, 10000))
                chnls, samprate, dur = soundInfo(toSysEncoding(sndPath))
                dlg = InsertDialog(self, -1, 'Insert sound settings', actual_dur=self.sndDur, snd_dur=dur)
                refpos = self.surface.GetPosition()
                refsize = self.surface.GetSize()
                dlgsize = dlg.GetSize()
                X = refpos[0] + (refsize[0] / 2 - dlgsize[0] / 2)
                Y = refpos[1] + (refsize[1] / 2 - dlgsize[1] / 2)
                dlg.SetPosition((X,Y))
                if dlg.ShowModal() == wx.ID_OK:
                    start, end, point, cross = dlg.getValues()
                    ok = True
                else:
                    ok = False
                dlg.Destroy()
                if not ok:
                    return
                self.parent.sg_audio.insertSnd(toSysEncoding(sndPath), start, end, point, cross)
                self.sndDur = self.parent.sg_audio.getTableDuration()
                self.sndInfoStr = u'Loaded sound: %s,    Sr: %s Hz,    Channels: %s,    Duration: %s sec' % (self.sndPath, samprate, self.chnls, self.sndDur)
                if self.parent.draw:
                    if not self.sndPath in self.surface.bitmapDict.keys() or force:
                        self.parent.log("Drawing waveform...")
                        self.surface.analyse(self.sndPath)
                    else:
                        self.surface.list = self.surface.bitmapDict[self.sndPath]
                        self.surface.create_bitmap()
                self.logSndInfo()
            elif os.path.isfile(os.path.join(self.parent.currentPath, os.path.split(sndPath)[1])):
                self.insertSound(os.path.join(self.parent.currentPath, os.path.split(sndPath)[1]), force)
            elif ":\\" in sndPath:
                # Handle windows path...
                self.insertSound(os.path.join(self.parent.currentPath, sndPath.split("\\")[-1]), force)
            else:
                self.parent.log('Sound file "%s" does not exist!' % sndPath)

    def drawWaveform(self):
        if self.surface.sndBitmap and self.parent.draw:
            self.surface.analyse(self.sndPath)

    def getNchnls(self):
        return self.nchnls

    def setNchnls(self, x):
        if x != self.nchnls:
            self.nchnls = x
            self.tx_chnls.SetValue(str(x))
            self.meter.setNumSliders(self.nchnls)
            self.shutdownServer()
            self.bootServer()

    def handleNchnls(self, event):
        x = int(self.tx_chnls.GetValue())
        if x != self.nchnls:
            status, path = self.parent.checkForMixedSound()
            if not status:
                self.tx_chnls.SetValue(str(self.nchnls))
                return
            if "Mixed sound" in self.sndPath:
                self.sndPath = path
            self.nchnls = x
            self.meter.setNumSliders(self.nchnls)
            self.shutdownServer()
            self.bootServer()

    def getSamplingRate(self):
        return self.samplingRate

    def setSamplingRate(self, x):
        SR = {44100: 0, 48000: 1, 96000: 2}
        if x != self.samplingRate:
            self.samplingRate = x
            self.pop_sr.SetSelection(SR[self.samplingRate])
            self.shutdownServer()
            self.bootServer()

    def handleSamplingRate(self, event):
        SR = {0: 44100, 1: 48000, 2: 96000}
        x = SR[event.GetInt()]
        if x != self.samplingRate:
            status, path = self.parent.checkForMixedSound()
            if not status:
                SR = {44100: 0, 48000: 1, 96000: 2}
                self.pop_sr.SetSelection(SR[self.samplingRate])
                return
            if "Mixed sound" in self.sndPath:
                self.sndPath = path
            self.samplingRate = x
            self.shutdownServer()
            self.bootServer()

    def getFileFormat(self):
        return self.fileformat

    def setFileFormat(self, x):
        self.fileformat = x
        self.pop_fileformat.SetSelection(self.fileformat)

    def handleFileFormat(self, event):
        self.fileformat = event.GetInt()

    def getSampleType(self):
        return self.sampletype

    def setSampleType(self, x):
        self.sampletype = x
        self.pop_sampletype.SetSelection(self.sampletype)

    def handleSampleType(self, event):
        self.sampletype = event.GetInt()

    def bootServer(self):
        self.parent.sg_audio.boot(self.parent.audioDriver, self.nchnls, self.samplingRate)
        self.tog_audio.Enable()
        if self.sndPath != "" and self.tempState == None:
            self.loadSound(self.sndPath)
        if self.tempState != None:
            self.parent.setState(self.tempState)
            self.tempState = None

    def shutdownServer(self):
        self.tempState = self.parent.getState()
        self.parent.sg_audio.shutdown()
        self.tog_audio.Disable()
        self.surface.Refresh()

    def handleAudio(self, event):
        if event.GetInt() == 1:
            if self.sndPath == "":
                self.parent.log('*** No sound loaded! ***')
                self.tog_audio.SetValue(0)
                self.parent.menu.Check(7, False)
            else:
                self.tx_chnls.Disable()
                self.tx_chnls.SetBackgroundColour("#EEEEEE")
                self.pop_sr.Disable()
                self.parent.enableDrivers(False)
                self.tog_audio.SetLabel('Stop')
                self.tog_audio.SetValue(1)
                self.parent.menu.Check(7, True)

                for t in self.surface.getAllTrajectories():
                    t.initCounter()
                self.parent.sg_audio.start()
        else:
            self.tx_chnls.Enable()
            self.tx_chnls.SetBackgroundColour("#FFFFFF")
            self.pop_sr.Enable()
            self.parent.enableDrivers(True)
            self.tog_audio.SetLabel('Start')
            self.tog_audio.SetValue(0)
            self.parent.menu.Check(7, False)
            self.tog_record.SetValue(0)
            self.tog_record.SetLabel('Start Rec')
            self.parent.sg_audio.stop()

    def handleOutput(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_TAB or key == wx.WXK_RETURN:
            self.surface.SetFocus()
        event.Skip()

    def setRecordFolder(self, str):
        self.tx_rec_folder.SetValue(str)

    def setRecordFilename(self, str):
        self.tx_output.SetValue(str)

    def handleRecord(self, event):
        if event.GetInt() == 1:
            folder = self.tx_rec_folder.GetValue()
            if folder.startswith("~"):
                folder = folder.replace("~", os.path.expanduser("~"), 1)
            if os.path.isdir(folder):
                filename = os.path.join(folder, self.tx_output.GetValue())
            else:
                filename = os.path.join(os.path.expanduser('~'), "Desktop", self.tx_output.GetValue())
            self.parent.sg_audio.recStart(filename, self.fileformat, self.sampletype)
            self.tog_record.SetLabel('Stop Rec')
        else:
            self.tog_record.SetLabel('Start Rec')
            self.parent.sg_audio.recStop()

    def chooseRecFolder(self, evt):
        dlg = wx.DirDialog(self, message="Choose a folder to save Soundgrain's output sounds...",
                            defaultPath=os.path.expanduser("~"))
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.tx_rec_folder.SetValue(ensureNFD(path))
        dlg.Destroy()
        self.but_folder.SetValue(0)

    def logSndInfo(self):
        self.parent.log(self.sndInfoStr)

class DrawingParameters(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.SetBackgroundColour(BACKGROUND_COLOUR)
        self.parent = parent
        box = wx.BoxSizer(wx.VERTICAL)

        lpcutText = wx.StaticText(self, -1, "Lowpass cutoff", size=(195,15))
        font, psize = lpcutText.GetFont(), lpcutText.GetFont().GetPointSize()
        if sys.platform == "win32":
            font.SetPointSize(psize-1)
        else:
            font.SetPointSize(psize-2)
        box.Add(lpcutText, 0, wx.LEFT|wx.TOP, 5)
        cutoffBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_cutoff = ControlSlider(self, 100, 15000, 5000, size=(195, 16), integer=True, log=True, outFunction=self.parent.GetParent().handleCutoff)
        cutoffBox.Add(self.sl_cutoff)
        box.Add(cutoffBox, 0, wx.LEFT | wx.RIGHT, 5)
        box.AddSpacer(5)

        lpqText = wx.StaticText(self, -1, "Lowpass Q", size=(195,15))
        box.Add(lpqText, 0, wx.LEFT, 5)
        qBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_q = ControlSlider(self, 0.5, 1000, 0.5, size=(195, 16), outFunction=self.parent.GetParent().handleQ)
        qBox.Add(self.sl_q)
        box.Add(qBox, 0, wx.LEFT | wx.RIGHT, 5)
        box.AddSpacer(5)

        oscpText = wx.StaticText(self, -1, "Oscil period", size=(195,15))
        box.Add(oscpText, 0, wx.LEFT, 5)
        periodBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_period = ControlSlider(self, 0, 5, 2, size=(195, 16), outFunction=self.parent.GetParent().handlePeriod)
        periodBox.Add(self.sl_period)
        self.sl_period.Disable()
        box.Add(periodBox, 0, wx.LEFT | wx.RIGHT, 5)
        box.AddSpacer(5)

        oscsclText = wx.StaticText(self, -1, "Oscil scaling", size=(195,15))
        box.Add(oscsclText, 0, wx.LEFT, 5)
        scalingBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_scaling = ControlSlider(self, 0, 4, 1, size=(195, 16), outFunction=self.parent.GetParent().handleScaling)
        scalingBox.Add(self.sl_scaling)
        self.sl_scaling.Disable()
        box.Add(scalingBox, 0, wx.LEFT | wx.RIGHT, 5)
        box.AddSpacer(5)

        for obj in [lpcutText, lpqText, oscpText, oscsclText]:
            obj.SetFont(font)

        self.SetAutoLayout(True)
        self.SetSizer(box)

class PlaybackParameters(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.SetBackgroundColour(BACKGROUND_COLOUR)
        self.parent = parent
        box = wx.BoxSizer(wx.VERTICAL)

        trajBox = wx.BoxSizer(wx.HORIZONTAL)
        seltrajText = wx.StaticText(self, -1, "Selected Traj:")
        font, psize = seltrajText.GetFont(), seltrajText.GetFont().GetPointSize()
        if sys.platform == "win32":
            font.SetPointSize(psize-1)
        else:
            font.SetPointSize(psize-2)
        trajBox.Add(seltrajText, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        trajChoices = [str(i+1) for i in range(MAX_STREAMS)]
        trajChoices.append("all")
        self.tog_traj = wx.Choice(self, -1, choices=trajChoices)
        self.tog_traj.SetSelection(0)
        self.tog_traj.Bind(wx.EVT_CHOICE, self.parent.GetParent().handleSelected)
        self.tog_traj.Bind(wx.EVT_LEFT_DOWN, self.parent.GetParent().handlePopupFocus)
        trajBox.Add(self.tog_traj, 0, wx.LEFT, 5)
        box.Add(trajBox, 0, wx.TOP, 2)
        box.AddSpacer(5)

        spdText = wx.StaticText(self, -1, "Timer speed", size=(195,15))
        box.Add(spdText, 0, wx.LEFT, 5)
        timespeedBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_timespeed = ControlSlider(self, 5, 1000, 25, size=(195, 16), log=True, outFunction=self.parent.GetParent().handleTimerSpeed)
        timespeedBox.Add(self.sl_timespeed)
        box.Add(timespeedBox, 0, wx.LEFT | wx.RIGHT, 5)
        box.AddSpacer(5)

        ptstepText = wx.StaticText(self, -1, "Point step", size=(195,15))
        box.Add(ptstepText, 0, wx.LEFT, 5)
        stepBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_step = ControlSlider(self, 1, 100, 1, size=(195, 16), integer=True, outFunction=self.parent.GetParent().handleStep)
        stepBox.Add(self.sl_step)
        box.Add(stepBox, 0, wx.LEFT | wx.RIGHT, 5)
        box.AddSpacer(5)

        ampText = wx.StaticText(self, -1, "Amplitude (dB)", size=(195,15))
        box.Add(ampText, 0, wx.LEFT, 5)
        ampBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_amp = ControlSlider(self, -60, 18, 0, size=(195, 16), integer=False, outFunction=self.parent.GetParent().handleTrajAmp)
        ampBox.Add(self.sl_amp)
        box.Add(ampBox, 0, wx.LEFT | wx.RIGHT, 5)

        for obj in [seltrajText, self.tog_traj, spdText, ptstepText, ampText]:
            obj.SetFont(font)

        self.SetAutoLayout(True)
        self.SetSizer(box)

class InsertDialog(wx.Dialog):
    def __init__(self, parent, id, title, actual_dur, snd_dur):
        wx.Dialog.__init__(self, parent, id, title)
        self.SetBackgroundColour(BACKGROUND_COLOUR)
        vbox = wx.BoxSizer(wx.VERTICAL)

        stline = wx.StaticText(self, -1, 'Starting point in seconds:')
        vbox.Add(stline, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP, 10)
        self.startSlider = ControlSlider(self, 0, snd_dur, 0, outFunction=self.handleStart)
        vbox.Add(self.startSlider, 0, wx.ALL, 5)

        stline = wx.StaticText(self, -1, 'Ending point in seconds:')
        vbox.Add(stline, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP, 10)
        self.endSlider = ControlSlider(self, 0, snd_dur, snd_dur, outFunction=self.handleEnd)
        vbox.Add(self.endSlider, 0, wx.ALL, 5)

        stline = wx.StaticText(self, -1, 'Insertion point in seconds:')
        vbox.Add(stline, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP, 10)
        self.insertSlider = ControlSlider(self, 0, actual_dur, 0)
        vbox.Add(self.insertSlider, 0, wx.ALL, 5)

        stline = wx.StaticText(self, -1, 'Crossfade time in seconds:')
        vbox.Add(stline, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP, 10)
        self.crossfadeSlider = ControlSlider(self, 0.001, snd_dur*0.5, 0, outFunction=self.handleCross)
        vbox.Add(self.crossfadeSlider, 0, wx.ALL, 5)

        sizer =  self.CreateButtonSizer(wx.CANCEL|wx.OK)
        vbox.Add(sizer, 0, wx.ALL, 10)
        self.SetSizerAndFit(vbox)

    def handleStart(self, val):
        start = self.startSlider.GetValue()
        end = self.endSlider.GetValue()
        cross = self.crossfadeSlider.GetValue()
        if start >= (end - .1):
            self.endSlider.SetValue(start + .1, False)
        rng = (end - start) * 0.5
        if cross > rng:
            self.crossfadeSlider.SetValue(rng, False)

    def handleEnd(self, val):
        start = self.startSlider.GetValue()
        end = self.endSlider.GetValue()
        cross = self.crossfadeSlider.GetValue()
        if end <= (start + .1):
            self.startSlider.SetValue(end - .1, False)
        rng = (end - start) * 0.5
        if cross > rng:
            self.crossfadeSlider.SetValue(rng, False)

    def handleCross(self, val):
        start = self.startSlider.GetValue()
        end = self.endSlider.GetValue()
        cross = self.crossfadeSlider.GetValue()
        rng = (end - start) * 0.5
        if cross > rng:
            self.crossfadeSlider.SetValue(rng, False)

    def getValues(self):
        return (self.startSlider.GetValue(), self.endSlider.GetValue(),
                self.insertSlider.GetValue(), self.crossfadeSlider.GetValue())
