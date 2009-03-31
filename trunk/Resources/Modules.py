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

import wx

class Module(wx.Frame):
    def __init__(self, parent, surface, continuousControl):
        wx.Frame.__init__(self, parent, -1, "Controls")

        if wx.Platform == '__WXMAC__':
            self.MacSetMetalAppearance(True)

        menuBar = wx.MenuBar()
        self.menu1 = wx.Menu()
        self.menu1.Append(1, 'Close\tCtrl+W', "")
        menuBar.Append(self.menu1, "&File")

        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_CLOSE, self.handleClose)
        self.Bind(wx.EVT_MENU, self.handleClose, id=1)

        self.parent = parent
        self.surface = surface
        self.continuousControl = continuousControl

    def handleClose(self, event):
        self.Show(False)

    def activateWidgets(self, audioState):
        if audioState:
            for widget in self.widgets:
                widget.Disable()
            #wx.CallLater(1000, self.initControlValues)
        else:
            for widget in self.widgets:
                widget.Enable()

    def initControlValues(self):
        for key, func in self.controls.iteritems():
            self.continuousControl(key, func())

    def handleGrainOverlaps(self, event):
        self.grainoverlaps = event.GetInt()
        self.overlapsValue.SetLabel(str(self.grainoverlaps))

    def getGrainOverlaps(self):
        return self.grainoverlaps

    def setGrainOverlaps(self, overlaps):
        self.grainoverlaps = overlaps
        self.sl_overlaps.SetValue(overlaps)
        self.overlapsValue.SetLabel(str(overlaps))

    def handleGrainSize(self, event):
        self.grainsize = event.GetInt()
        self.sizeValue.SetLabel(str(self.grainsize) + ' ms')   
        self.continuousControl('/grainsize', self.grainsize)   

    def getGrainSize(self):
        return self.grainsize

    def setGrainSize(self, size):
        self.grainsize = size
        self.sl_size.SetValue(self.grainsize)
        self.sizeValue.SetLabel(str(self.grainsize) + ' ms')   

    def handleAmp(self, event):
        self.amplitude = event.GetInt() * 0.01
        self.ampValue.SetLabel(str(self.amplitude))
        self.continuousControl('/amplitude', self.amplitude)   

    def getAmp(self):
        return self.amplitude

    def setAmp(self, amp):
        self.amplitude = amp
        self.sl_amp.SetValue(int(self.amplitude*100))
        self.ampValue.SetLabel(str(self.amplitude))

    def handleTrans(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_TAB or key == wx.WXK_RETURN:
            self.trans = [float(value) for value in self.tx_trans.GetValue().split(',') if value not in [" ", ""]]
            self.surface.SetFocus()
        event.Skip()

    def getTrans(self):
        return self.trans

    def setTrans(self, trans):
        self.trans = trans
        self.tx_trans.SetValue(", ".join(str(t) for t in self.trans))
                        
    def handleYMin(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_TAB or key == wx.WXK_RETURN:
            self.surface.setYMin(float(self.tx_ymin.GetValue()))
            self.surface.SetFocus()
        event.Skip()

    def getYMin(self):
        return float(self.tx_ymin.GetValue())

    def setYMin(self, ymin):
        self.tx_ymin.SetValue(str(ymin))
        self.surface.setYMin(ymin)
    
    def handleYMax(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_TAB or key == wx.WXK_RETURN:
            self.surface.setYMax(float(self.tx_ymax.GetValue()))
            self.surface.SetFocus()
        event.Skip()

    def getYMax(self):
        return float(self.tx_ymax.GetValue())

    def setYMax(self, ymax):
        self.tx_ymax.SetValue(str(ymax))
        self.surface.setYMax(ymax)
                        
    def handleLinLog(self, event):
        self.linLogSqrt = (self.linLogSqrt + 1) % 3
        self.b_linlog.SetLabel(['Lin', 'Log', 'Sqrt'][self.linLogSqrt])
        self.surface.setYMethod(self.linLogSqrt)

    def getLinLog(self):
        return self.linLogSqrt

    def setLinLog(self, val):
        self.linLogSqrt = val
        self.b_linlog.SetLabel(['Lin', 'Log', 'Sqrt'][self.linLogSqrt])
        self.surface.setYMethod(self.linLogSqrt)

    def handleFFTSize(self, event):
        self.fftsize = 2 ** event.GetInt()
        self.fftsizeValue.SetLabel(str(self.fftsize))

    def getFFTSize(self):
        return self.fftsize

    def setFFTSize(self, fftsize):
        self.fftsize = fftsize
        self.sl_fftsize.SetValue(self.ffts[self.fftsize])
        self.fftsizeValue.SetLabel(str(self.fftsize))

    def handleOverlaps(self, event):
        self.overlaps = event.GetInt()
        self.overlapsValue.SetLabel(str(self.overlaps))   

    def getOverlaps(self):
        return self.overlaps

    def setOverlaps(self, overlaps):
        self.overlaps = overlaps
        self.sl_overlaps.SetValue(self.overlaps)
        self.overlapsValue.SetLabel(str(self.overlaps))   

    def handleWindowSize(self, event):
        self.winsize = 2 ** event.GetInt()
        self.winsizeValue.SetLabel(str(self.winsize))

    def getWindowSize(self):
        return self.winsize

    def setWindowSize(self, winsize):
        self.winsize = winsize
        self.sl_winsize.SetValue(self.ffts[self.winsize])
        self.winsizeValue.SetLabel(str(self.winsize))

    def handleKeepFormant(self, event):
        if event.GetInt():
            self.tog_formant.SetLabel("Yes")
            self.formant = 1
        else:
            self.tog_formant.SetLabel("No")
            self.formant = 0

    def getKeepFormant(self):
        return self.formant

    def setKeepFormant(self, formant):
        self.formant = formant
        if self.formant:
            self.tog_formant.SetLabel("Yes")
        else:
            self.tog_formant.SetLabel("No")

    def handleNumBins(self, event):
        self.numbins = event.GetInt()
        self.numbinsValue.SetLabel(str(self.numbins))

    def getNumBins(self):
        return self.numbins

    def setNumBins(self, num):
        self.numbins = num
        self.sl_numbins.SetValue(self.numbins)
        self.numbinsValue.SetLabel(str(self.numbins))

    def handleFirst(self, event):
        self.first = event.GetInt()
        self.firstValue.SetLabel(str(self.first))

    def getFirst(self):
        return self.first

    def setFirst(self, first):
        self.first = first
        self.sl_first.SetValue(self.first)
        self.firstValue.SetLabel(str(self.first))
        
    def handleIncr(self, event):
        self.incr = event.GetInt()
        self.incrValue.SetLabel(str(self.incr))        

    def getIncr(self):
        return self.incr

    def setIncr(self, incr):
        self.incr = incr    
        self.sl_incr.SetValue(self.incr)    
        self.incrValue.SetLabel(str(self.incr))        

    def handleTranspo(self, event):
        self.transpo = event.GetInt() * 0.01
        self.transpoValue.SetLabel(str(self.transpo))
        self.continuousControl('/transpo', self.transpo)   

    def getTranspo(self):
        return self.transpo

    def setTranspo(self, transpo):
        self.transpo = transpo
        self.sl_transpo.SetValue(int(self.transpo*100))
        self.transpoValue.SetLabel(str(self.transpo))

    def handlePitch(self, event):
        self.pitch = event.GetInt()
        self.pitchValue.SetLabel(str(self.pitch) + ' Hz')

    def getPitch(self):
        return self.pitch

    def setPitch(self, pitch):
        self.pitch = pitch
        self.sl_pitch.SetValue(int(self.pitch))
        self.pitchValue.SetLabel(str(self.pitch) + ' Hz')

    def handleCarrier(self, event):
        self.carrier = event.GetInt() * 0.001
        self.carrierValue.SetLabel(str(self.carrier))
        self.continuousControl('/carrier', self.carrier)   

    def getCarrier(self):
        return self.carrier

    def setCarrier(self, carrier):
        self.carrier = carrier
        self.sl_carrier.SetValue(int(self.carrier*1000))
        self.carrierValue.SetLabel(str(self.carrier))

    def handleModulator(self, event):
        self.modulator = event.GetInt() * 0.001
        self.modulatorValue.SetLabel(str(self.modulator))
        self.continuousControl('/modulator', self.modulator)   

    def getModulator(self):
        return self.modulator

    def setModulator(self, modulator):
        self.modulator = modulator
        self.sl_modulator.SetValue(int(self.modulator*1000))
        self.modulatorValue.SetLabel(str(self.modulator))

    def handleIndex(self, event):
        self.index = event.GetInt() * 0.01
        self.indexValue.SetLabel(str(self.index))
        self.continuousControl('/index', self.index)   

    def getIndex(self):
        return self.index

    def setIndex(self, index):
        self.index = index
        self.sl_index.SetValue(int(self.index*100))
        self.indexValue.SetLabel(str(self.index))

    def handleCutoff(self, event):
        self.cutoff = event.GetInt() * 100
        self.cutoffValue.SetLabel(str(self.cutoff) + ' Hz')
        self.continuousControl('/cutoff', self.cutoff)   

    def getCutoff(self):
        return self.cutoff

    def setCutoff(self, cutoff):
        self.cutoff = cutoff
        self.sl_cutoff.SetValue(int(self.cutoff*0.01))
        self.cutoffValue.SetLabel(str(self.cutoff) + ' Hz')

    def makeGrainOverlapsBox(self, box):
        box.Add(wx.StaticText(self, -1, "Number of grains"), 0, wx.LEFT|wx.TOP, 5)
        overlapsBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_overlaps = wx.Slider( self, -1, self.grainoverlaps, 1, 48, size=(200, -1), style=wx.SL_HORIZONTAL)
        overlapsBox.Add(self.sl_overlaps, 0, wx.RIGHT, 10)
        self.overlapsValue = wx.StaticText(self, -1, str(self.sl_overlaps.GetValue()))
        overlapsBox.Add(self.overlapsValue, 0, wx.RIGHT, 10)
        box.Add(overlapsBox, 0, wx.ALL, 5)

    def makeGrainSizeBox(self, box):
        box.Add(wx.StaticText(self, -1, "Grain size"), 0, wx.LEFT|wx.TOP, 5)
        sizeBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_size = wx.Slider( self, -1, self.grainsize, 50, 500, size=(200, -1), style=wx.SL_HORIZONTAL)
        sizeBox.Add(self.sl_size, 0, wx.RIGHT, 10)
        self.sizeValue = wx.StaticText(self, -1, str(self.sl_size.GetValue()) + ' ms')
        sizeBox.Add(self.sizeValue, 0, wx.RIGHT, 10)
        box.Add(sizeBox, 0, wx.ALL, 5)

    def makeAmplitudeBox(self, box):
        box.Add(wx.StaticText(self, -1, "Amplitude"), 0, wx.LEFT|wx.TOP, 5)
        ampBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_amp = wx.Slider( self, -1, int(self.amplitude*100), 0, 200, size=(200, -1), style=wx.SL_HORIZONTAL)
        ampBox.Add(self.sl_amp, 0, wx.RIGHT, 10)
        self.ampValue = wx.StaticText(self, -1, str(self.sl_amp.GetValue() * 0.01))
        ampBox.Add(self.ampValue, 0, wx.RIGHT, 10)
        box.Add(ampBox, 0, wx.ALL, 5)

    def makeTransBox(self, box):
        box.Add(wx.StaticText(self, -1, "Random transposition per grain"), 0, wx.CENTER|wx.TOP, 5)
        box.Add(wx.StaticText(self, -1, "List of transposition ratios"), 0, wx.CENTER|wx.TOP, 5)
        transBox = wx.BoxSizer(wx.HORIZONTAL)
        self.tx_trans = wx.TextCtrl( self, -1, "1, ", size=(250, -1))
        transBox.Add(self.tx_trans, 0, wx.CENTER | wx.ALL, 5)
        box.Add(transBox, 0, wx.ALL, 5)                        

    def makeYaxisTranspoBox(self, box, label=None):
        if label == None: lab = "Y axis (transposition)"
        else: lab = label
        box.Add(wx.StaticText(self, -1, lab), 0, wx.CENTER|wx.TOP, 5)
        textBox = wx.BoxSizer(wx.HORIZONTAL)
        textBox.Add(wx.StaticText(self, -1, "Min: "), 0, wx.TOP, 4)
        self.tx_ymin = wx.TextCtrl( self, -1, "0.", size=(40, -1))
        textBox.Add(self.tx_ymin, 0, wx.RIGHT, 20)
        textBox.Add(wx.StaticText(self, -1, "Max: "), 0, wx.TOP, 4)
        self.tx_ymax = wx.TextCtrl( self, -1, "1.", size=(40, -1))
        textBox.Add(self.tx_ymax, 0, wx.RIGHT, 20)
        self.b_linlog = wx.Button(self, -1, 'Lin', size=(50,20))
        textBox.Add(self.b_linlog, 0, wx.TOP, 1 )
        box.Add(textBox, 0, wx.ALL, 10)

    def makeFFTSizeBox(self, box):
        box.Add(wx.StaticText(self, -1, "FFT size (power of 2)"), 0, wx.LEFT|wx.TOP, 5)
        fftsizeBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_fftsize = wx.Slider( self, -1, self.ffts[self.fftsize], 5, 14, size=(200, -1), style=wx.SL_HORIZONTAL)
        fftsizeBox.Add(self.sl_fftsize, 0, wx.RIGHT, 10)
        self.fftsizeValue = wx.StaticText(self, -1, str(2 ** self.sl_fftsize.GetValue()))
        fftsizeBox.Add(self.fftsizeValue, 0, wx.RIGHT, 10)
        box.Add(fftsizeBox, 0, wx.ALL, 5)

    def makeFFTOverlapsBox(self, box):
        box.Add(wx.StaticText(self, -1, "FFT Overlaps"), 0, wx.LEFT|wx.TOP, 5)
        overlapsBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_overlaps = wx.Slider( self, -1, self.overlaps, 2, 16, size=(200, -1), style=wx.SL_HORIZONTAL)
        overlapsBox.Add(self.sl_overlaps, 0, wx.RIGHT, 10)
        self.overlapsValue = wx.StaticText(self, -1, str(self.sl_overlaps.GetValue()))
        overlapsBox.Add(self.overlapsValue, 0, wx.RIGHT, 10)
        box.Add(overlapsBox, 0, wx.ALL, 5)

    def makeFFTWinSizeBox(self, box):
        box.Add(wx.StaticText(self, -1, "FFT window size ( >= FFT size)"), 0, wx.LEFT|wx.TOP, 5)
        winsizeBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_winsize = wx.Slider( self, -1, self.ffts[self.winsize], 5, 14, size=(200, -1), style=wx.SL_HORIZONTAL)
        winsizeBox.Add(self.sl_winsize, 0, wx.RIGHT, 10)
        self.winsizeValue = wx.StaticText(self, -1, str(2 ** self.sl_winsize.GetValue()))
        winsizeBox.Add(self.winsizeValue, 0, wx.RIGHT, 10)
        box.Add(winsizeBox, 0, wx.ALL, 5)

    def makeKeepFormantBox(self, box):
        box.Add(wx.StaticText(self, -1, "Try to keep spectral envelope"), 0, wx.CENTER|wx.TOP, 5)
        self.tog_formant = wx.ToggleButton( self, -1, "No")
        box.Add(self.tog_formant, 0, wx.CENTER|wx.ALL, 10)

    def makeNumBinsBox(self, box):
        box.Add(wx.StaticText(self, -1, "Number of bins to synthesize"), 0, wx.LEFT|wx.TOP, 5)
        numbinsBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_numbins = wx.Slider( self, -1, self.numbins, 1, 200, size=(200, -1), style=wx.SL_HORIZONTAL)
        numbinsBox.Add(self.sl_numbins, 0, wx.RIGHT, 10)
        self.numbinsValue = wx.StaticText(self, -1, str(self.sl_numbins.GetValue()))
        numbinsBox.Add(self.numbinsValue, 0, wx.RIGHT, 10)
        box.Add(numbinsBox, 0, wx.ALL, 5)

    def makeFirstBinBox(self, box):
        box.Add(wx.StaticText(self, -1, "First bin"), 0, wx.LEFT|wx.TOP, 5)
        firstBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_first = wx.Slider( self, -1, self.first, 0, 50, size=(200, -1), style=wx.SL_HORIZONTAL)
        firstBox.Add(self.sl_first, 0, wx.RIGHT, 10)
        self.firstValue = wx.StaticText(self, -1, str(self.sl_first.GetValue()))
        firstBox.Add(self.firstValue, 0, wx.RIGHT, 10)
        box.Add(firstBox, 0, wx.ALL, 5)

    def makeIncrementBox(self, box):
        box.Add(wx.StaticText(self, -1, "Bin increment"), 0, wx.LEFT|wx.TOP, 5)
        incrBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_incr = wx.Slider( self, -1, self.incr, 1, 50, size=(200, -1), style=wx.SL_HORIZONTAL)
        incrBox.Add(self.sl_incr, 0, wx.RIGHT, 10)
        self.incrValue = wx.StaticText(self, -1, str(self.sl_incr.GetValue()))
        incrBox.Add(self.incrValue, 0, wx.RIGHT, 10)
        box.Add(incrBox, 0, wx.ALL, 5)
   
    def makeTranspoBox(self, box):
        box.Add(wx.StaticText(self, -1, "Sound transposition"), 0, wx.LEFT|wx.TOP, 5)
        transpoBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_transpo = wx.Slider( self, -1, int(self.transpo*100), 0, 200, size=(200, -1), style=wx.SL_HORIZONTAL)
        transpoBox.Add(self.sl_transpo, 0, wx.RIGHT, 10)
        self.transpoValue = wx.StaticText(self, -1, str(self.sl_transpo.GetValue() * 0.01))
        transpoBox.Add(self.transpoValue, 0, wx.RIGHT, 10)
        box.Add(transpoBox, 0, wx.ALL, 5)
   
    def makePitchBox(self, box):
        box.Add(wx.StaticText(self, -1, "Base pitch"), 0, wx.LEFT|wx.TOP, 5)
        pitchBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_pitch = wx.Slider( self, -1, self.pitch, 40, 500, size=(200, -1), style=wx.SL_HORIZONTAL)
        pitchBox.Add(self.sl_pitch, 0, wx.RIGHT, 10)
        self.pitchValue = wx.StaticText(self, -1, str(self.sl_pitch.GetValue()) + ' Hz')
        pitchBox.Add(self.pitchValue, 0, wx.RIGHT, 10)
        box.Add(pitchBox, 0, wx.ALL, 5)
  
    def makeCarrierBox(self, box):
        box.Add(wx.StaticText(self, -1, "Carrier ratio"), 0, wx.LEFT|wx.TOP, 5)
        carrierBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_carrier = wx.Slider( self, -1, int(self.carrier * 1000), 250, 2000, size=(200, -1), style=wx.SL_HORIZONTAL)
        carrierBox.Add(self.sl_carrier, 0, wx.RIGHT, 10)
        self.carrierValue = wx.StaticText(self, -1, str(self.sl_carrier.GetValue() * 0.001))
        carrierBox.Add(self.carrierValue, 0, wx.RIGHT, 10)
        box.Add(carrierBox, 0, wx.ALL, 5)

    def makeModulatorBox(self, box):
        box.Add(wx.StaticText(self, -1, "Modulator ratio"), 0, wx.LEFT|wx.TOP, 5)
        modulatorBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_modulator = wx.Slider( self, -1, int(self.modulator * 1000), 250, 2000, size=(200, -1), style=wx.SL_HORIZONTAL)
        modulatorBox.Add(self.sl_modulator, 0, wx.RIGHT, 10)
        self.modulatorValue = wx.StaticText(self, -1, str(self.sl_modulator.GetValue() * 0.001))
        modulatorBox.Add(self.modulatorValue, 0, wx.RIGHT, 10)
        box.Add(modulatorBox, 0, wx.ALL, 5)

    def makeIndexBox(self, box):
        box.Add(wx.StaticText(self, -1, "Modulation index"), 0, wx.LEFT|wx.TOP, 5)
        indexBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_index = wx.Slider( self, -1, int(self.index * 100), 0, 2000, size=(200, -1), style=wx.SL_HORIZONTAL)
        indexBox.Add(self.sl_index, 0, wx.RIGHT, 10)
        self.indexValue = wx.StaticText(self, -1, str(self.sl_index.GetValue() * 0.01))
        indexBox.Add(self.indexValue, 0, wx.RIGHT, 10)
        box.Add(indexBox, 0, wx.ALL, 5)

    def makeCutoffBox(self, box):
        box.Add(wx.StaticText(self, -1, "Lowpass cutoff"), 0, wx.LEFT|wx.TOP, 5)
        cutoffBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_cutoff = wx.Slider( self, -1, int(self.cutoff * 0.01), 1, 160, size=(200, -1), style=wx.SL_HORIZONTAL)
        cutoffBox.Add(self.sl_cutoff, 0, wx.RIGHT, 10)
        self.cutoffValue = wx.StaticText(self, -1, str(self.sl_cutoff.GetValue() * 100) + ' Hz')
        cutoffBox.Add(self.cutoffValue, 0, wx.RIGHT, 10)
        box.Add(cutoffBox, 0, wx.ALL, 5)

class GranulatorFrame(Module): 
    def __init__(self, parent, surface, continuousControl):
        Module.__init__(self, parent, surface, continuousControl)

        self.grainoverlaps = 8
        self.grainsize = 200
        self.amplitude = 0.7
        self.trans = [1.]
        self.linLogSqrt = 0

        box = wx.BoxSizer(wx.VERTICAL)
        self.makeGrainOverlapsBox(box)
        self.makeGrainSizeBox(box)
        self.makeAmplitudeBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)
        self.makeTransBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)
        self.makeYaxisTranspoBox(box)
        self.SetSizer(box)
        
        self.Bind(wx.EVT_SLIDER, self.handleGrainOverlaps, self.sl_overlaps)        
        self.Bind(wx.EVT_SLIDER, self.handleGrainSize, self.sl_size)        
        self.Bind(wx.EVT_SLIDER, self.handleAmp, self.sl_amp)        
        self.tx_trans.Bind(wx.EVT_CHAR, self.handleTrans)        
        self.tx_ymin.Bind(wx.EVT_CHAR, self.handleYMin)        
        self.tx_ymax.Bind(wx.EVT_CHAR, self.handleYMax)        
        self.Bind(wx.EVT_BUTTON, self.handleLinLog, self.b_linlog)
        
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.SetMaxSize(self.GetSize())
        self.SetPosition((self.parent.GetPosition()[0] + self.parent.GetSize()[0], self.parent.GetPosition()[1]))

        self.widgets = [self.sl_overlaps, self.tx_trans]
        self.controls = {'/amplitude': self.getAmp, '/grainsize': self.getGrainSize}

        self.Show(False)

    def getFixedValues(self):
        return [self.grainoverlaps, self.trans]

    def save(self):
        return {'grainoverlaps': self.getGrainOverlaps(),
                'grainsize': self.getGrainSize(),
                'amp': self.getAmp(),
                'trans': self.getTrans(),
                'ymin': self.getYMin(),
                'ymax': self.getYMax(),
                'linlog': self.getLinLog()}

    def load(self, dict):
        self.setGrainOverlaps(dict['grainoverlaps'])
        self.setGrainSize(dict['grainsize'])
        self.setAmp(dict['amp'])
        self.setTrans(dict['trans'])
        self.setYMin(dict['ymin'])
        self.setYMax(dict['ymax'])
        self.setLinLog(dict['linlog'])

class FFTReaderFrame(Module): 
    def __init__(self, parent, surface, continuousControl):
        Module.__init__(self, parent, surface, continuousControl)

        self.ffts = {32: 5, 64: 6, 128: 7, 256: 8, 512: 9, 1024: 10, 2048: 11, 4096: 12, 8192: 13, 16384: 14}
        self.fftsize = 1024        
        self.overlaps = 8
        self.winsize = 2048 
        self.formant = 0
        self.cutoff = 10000
        self.amplitude = 0.7
        self.linLogSqrt = 0

        box = wx.BoxSizer(wx.VERTICAL)
        self.makeFFTSizeBox(box)
        self.makeFFTOverlapsBox(box)
        self.makeFFTWinSizeBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)
        self.makeKeepFormantBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)
        self.makeCutoffBox(box)
        self.makeAmplitudeBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)
        self.makeYaxisTranspoBox(box)
        self.SetSizer(box)
        
        self.Bind(wx.EVT_SLIDER, self.handleFFTSize, self.sl_fftsize)        
        self.Bind(wx.EVT_SLIDER, self.handleOverlaps, self.sl_overlaps)        
        self.Bind(wx.EVT_SLIDER, self.handleWindowSize, self.sl_winsize)        
        self.Bind(wx.EVT_TOGGLEBUTTON, self.handleKeepFormant, self.tog_formant)        
        self.Bind(wx.EVT_SLIDER, self.handleCutoff, self.sl_cutoff)        
        self.Bind(wx.EVT_SLIDER, self.handleAmp, self.sl_amp)        
        self.tx_ymin.Bind(wx.EVT_CHAR, self.handleYMin)        
        self.tx_ymax.Bind(wx.EVT_CHAR, self.handleYMax)        
        self.Bind(wx.EVT_BUTTON, self.handleLinLog, self.b_linlog)
        
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.SetMaxSize(self.GetSize())
        self.SetPosition((self.parent.GetPosition()[0] + self.parent.GetSize()[0], self.parent.GetPosition()[1]))

        self.widgets = [self.sl_fftsize, self.sl_overlaps, self.sl_winsize, self.tog_formant]
        self.controls = {'/amplitude': self.getAmp, '/cutoff': self.getCutoff}

        self.Show(False)

    def getFixedValues(self):
        return [self.fftsize, self.overlaps, self.winsize, self.formant]

    def save(self):
        return {'fftsize': self.getFFTSize(),
                'overlaps': self.getOverlaps(),
                'winsize': self.getWindowSize(),
                'formant': self.getKeepFormant(),
                'cutoff': self.getCutoff(),
                'amp': self.getAmp(),
                'ymin': self.getYMin(),
                'ymax': self.getYMax(),
                'linlog': self.getLinLog()}

    def load(self, dict):
        self.setFFTSize(dict['fftsize'])
        self.setOverlaps(dict['overlaps'])
        self.setWindowSize(dict['winsize'])
        self.setKeepFormant(dict['formant'])
        self.setCutoff(dict['cutoff'])
        self.setAmp(dict['amp'])
        self.setYMin(dict['ymin'])
        self.setYMax(dict['ymax'])
        self.setLinLog(dict['linlog'])

class FFTAdsynFrame(Module): 
    def __init__(self, parent, surface, continuousControl):
        Module.__init__(self, parent, surface, continuousControl)


        self.ffts = {32: 5, 64: 6, 128: 7, 256: 8, 512: 9, 1024: 10, 2048: 11, 4096: 12, 8192: 13, 16384: 14}
        self.fftsize = 1024        
        self.overlaps = 8
        self.winsize = 2048 
        self.numbins = 50
        self.first = 0
        self.incr = 3        
        self.cutoff = 10000
        self.amplitude = 0.7
        self.linLogSqrt = 0

        box = wx.BoxSizer(wx.VERTICAL)
        self.makeFFTSizeBox(box)
        self.makeFFTOverlapsBox(box)
        self.makeFFTWinSizeBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)
        self.makeNumBinsBox(box)
        self.makeFirstBinBox(box)
        self.makeIncrementBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)
        self.makeCutoffBox(box)
        self.makeAmplitudeBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)
        self.makeYaxisTranspoBox(box)
        self.SetSizer(box)

        self.Bind(wx.EVT_SLIDER, self.handleFFTSize, self.sl_fftsize)        
        self.Bind(wx.EVT_SLIDER, self.handleOverlaps, self.sl_overlaps)        
        self.Bind(wx.EVT_SLIDER, self.handleWindowSize, self.sl_winsize)                
        self.Bind(wx.EVT_SLIDER, self.handleNumBins, self.sl_numbins)                
        self.Bind(wx.EVT_SLIDER, self.handleFirst, self.sl_first)                
        self.Bind(wx.EVT_SLIDER, self.handleIncr, self.sl_incr)                
        self.Bind(wx.EVT_SLIDER, self.handleCutoff, self.sl_cutoff)        
        self.Bind(wx.EVT_SLIDER, self.handleAmp, self.sl_amp)        
        self.tx_ymin.Bind(wx.EVT_CHAR, self.handleYMin)        
        self.tx_ymax.Bind(wx.EVT_CHAR, self.handleYMax)        
        self.Bind(wx.EVT_BUTTON, self.handleLinLog, self.b_linlog)
        
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.SetMaxSize(self.GetSize())
        self.SetPosition((self.parent.GetPosition()[0] + self.parent.GetSize()[0], self.parent.GetPosition()[1]))

        self.widgets = [self.sl_fftsize, self.sl_overlaps, self.sl_winsize, self.sl_numbins, self.sl_first, self.sl_incr]
        self.controls = {'/amplitude': self.getAmp, '/cutoff': self.getCutoff}

        self.Show(False)

    def getFixedValues(self):
        return [self.fftsize, self.overlaps, self.winsize, self.numbins, self.first, self.incr]

    def save(self):
        return {'fftsize': self.getFFTSize(),
                'overlaps': self.getOverlaps(),
                'winsize': self.getWindowSize(),
                'numbins': self.getNumBins(),
                'first': self.getFirst(),
                'incr': self.getIncr(),
                'cutoff': self.getCutoff(),
                'amp': self.getAmp(),
                'ymin': self.getYMin(),
                'ymax': self.getYMax(),
                'linlog': self.getLinLog()}

    def load(self, dict):
        self.setFFTSize(dict['fftsize'])
        self.setOverlaps(dict['overlaps'])
        self.setWindowSize(dict['winsize'])
        self.setNumBins(dict['numbins'])
        self.setFirst(dict['first'])
        self.setIncr(dict['incr'])
        self.setCutoff(dict['cutoff'])
        self.setAmp(dict['amp'])
        self.setYMin(dict['ymin'])
        self.setYMax(dict['ymax'])
        self.setLinLog(dict['linlog'])

class FFTRingModFrame(Module): 
    def __init__(self, parent, surface, continuousControl):
        Module.__init__(self, parent, surface, continuousControl)
        
        self.ffts = {32: 5, 64: 6, 128: 7, 256: 8, 512: 9, 1024: 10, 2048: 11, 4096: 12, 8192: 13, 16384: 14}
        self.fftsize = 1024        
        self.overlaps = 8
        self.winsize = 2048         
        self.cutoff = 10000
        self.amplitude = 0.7
        self.transpo = 1
        self.linLogSqrt = 0

        box = wx.BoxSizer(wx.VERTICAL)
        self.makeFFTSizeBox(box)
        self.makeFFTOverlapsBox(box)
        self.makeFFTWinSizeBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)
        self.makeTranspoBox(box)
        self.makeCutoffBox(box)
        self.makeAmplitudeBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)
        self.makeYaxisTranspoBox(box, "Y axis (* 100 = Sine pitch)")
        self.SetSizer(box)
        
        self.Bind(wx.EVT_SLIDER, self.handleFFTSize, self.sl_fftsize)        
        self.Bind(wx.EVT_SLIDER, self.handleOverlaps, self.sl_overlaps)        
        self.Bind(wx.EVT_SLIDER, self.handleWindowSize, self.sl_winsize)                
        self.Bind(wx.EVT_SLIDER, self.handleTranspo, self.sl_transpo)        
        self.Bind(wx.EVT_SLIDER, self.handleCutoff, self.sl_cutoff)        
        self.Bind(wx.EVT_SLIDER, self.handleAmp, self.sl_amp)        
        self.tx_ymin.Bind(wx.EVT_CHAR, self.handleYMin)        
        self.tx_ymax.Bind(wx.EVT_CHAR, self.handleYMax)        
        self.Bind(wx.EVT_BUTTON, self.handleLinLog, self.b_linlog)
        
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.SetMaxSize(self.GetSize())
        self.SetPosition((self.parent.GetPosition()[0] + self.parent.GetSize()[0], self.parent.GetPosition()[1]))

        self.widgets = [self.sl_fftsize, self.sl_overlaps, self.sl_winsize]
        self.controls = {'/amplitude': self.getAmp, '/transpo': self.getTranspo, '/cutoff': self.getCutoff}

        self.Show(False)

    def getFixedValues(self):
        return [self.fftsize, self.overlaps, self.winsize]

    def save(self):
        return {'fftsize': self.getFFTSize(),
                'overlaps': self.getOverlaps(),
                'winsize': self.getWindowSize(),
                'transpo': self.getTranspo(),
                'cutoff': self.getCutoff(),
                'amp': self.getAmp(),
                'ymin': self.getYMin(),
                'ymax': self.getYMax(),
                'linlog': self.getLinLog()}

    def load(self, dict):
        self.setFFTSize(dict['fftsize'])
        self.setOverlaps(dict['overlaps'])
        self.setWindowSize(dict['winsize'])
        self.setTranspo(dict['transpo'])
        self.setCutoff(dict['cutoff'])
        self.setAmp(dict['amp'])
        self.setYMin(dict['ymin'])
        self.setYMax(dict['ymax'])
        self.setLinLog(dict['linlog'])

class FMCrossSynthFrame(Module): 
    def __init__(self, parent, surface, continuousControl):
        Module.__init__(self, parent, surface, continuousControl)

        self.ffts = {32: 5, 64: 6, 128: 7, 256: 8, 512: 9, 1024: 10, 2048: 11, 4096: 12, 8192: 13, 16384: 14}
        self.fftsize = 1024        
        self.overlaps = 8
        self.winsize = 2048 
        self.transpo = 1
        self.pitch = 100
        self.carrier = 1
        self.modulator = .5
        self.index = 5
        self.cutoff = 10000
        self.amplitude = 0.7
        self.linLogSqrt = 0

        box = wx.BoxSizer(wx.VERTICAL)
        self.makeFFTSizeBox(box)
        self.makeFFTOverlapsBox(box)
        self.makeFFTWinSizeBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)
        self.makeTranspoBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)
        box.Add(wx.StaticText(self, -1, "FM parameters"), 0, wx.CENTER|wx.TOP, 5)
        self.makePitchBox(box)
        self.makeCarrierBox(box)
        self.makeModulatorBox(box)
        self.makeIndexBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)
        self.makeCutoffBox(box)
        self.makeAmplitudeBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)
        self.makeYaxisTranspoBox(box, "Y axis (FM pitch)")
        self.SetSizer(box)
        
        self.Bind(wx.EVT_SLIDER, self.handleFFTSize, self.sl_fftsize)        
        self.Bind(wx.EVT_SLIDER, self.handleOverlaps, self.sl_overlaps)        
        self.Bind(wx.EVT_SLIDER, self.handleWindowSize, self.sl_winsize)        
        self.Bind(wx.EVT_SLIDER, self.handleTranspo, self.sl_transpo)        
        self.Bind(wx.EVT_SLIDER, self.handlePitch, self.sl_pitch)        
        self.Bind(wx.EVT_SLIDER, self.handleCarrier, self.sl_carrier)        
        self.Bind(wx.EVT_SLIDER, self.handleModulator, self.sl_modulator)        
        self.Bind(wx.EVT_SLIDER, self.handleIndex, self.sl_index)        
        self.Bind(wx.EVT_SLIDER, self.handleCutoff, self.sl_cutoff)        
        self.Bind(wx.EVT_SLIDER, self.handleAmp, self.sl_amp)        
        self.tx_ymin.Bind(wx.EVT_CHAR, self.handleYMin)        
        self.tx_ymax.Bind(wx.EVT_CHAR, self.handleYMax)        
        self.Bind(wx.EVT_BUTTON, self.handleLinLog, self.b_linlog)
        
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.SetMaxSize(self.GetSize())
        self.SetPosition((self.parent.GetPosition()[0] + self.parent.GetSize()[0], self.parent.GetPosition()[1]))

        self.widgets = [self.sl_fftsize, self.sl_overlaps, self.sl_winsize, self.sl_pitch]
        self.controls = {'/amplitude': self.getAmp, '/transpo': self.getTranspo, '/carrier': self.getCarrier, 
                         '/modulator': self.getModulator, '/index': self.getIndex, '/cutoff': self.getCutoff}

        self.Show(False)

    def getFixedValues(self):
        return [self.fftsize, self.overlaps, self.winsize, self.pitch]

    def save(self):
        return {'fftsize': self.getFFTSize(),
                'overlaps': self.getOverlaps(),
                'winsize': self.getWindowSize(),
                'transpo': self.getTranspo(),
                'pitch': self.getPitch(),
                'carrier': self.getCarrier(),
                'modulator': self.getModulator(),
                'index': self.getIndex(),
                'cutoff': self.getCutoff(),
                'amp': self.getAmp(),
                'ymin': self.getYMin(),
                'ymax': self.getYMax(),
                'linlog': self.getLinLog()}

    def load(self, dict):
        self.setFFTSize(dict['fftsize'])
        self.setOverlaps(dict['overlaps'])
        self.setWindowSize(dict['winsize'])
        self.setTranspo(dict['transpo'])
        self.setPitch(dict['pitch'])
        self.setCarrier(dict['carrier'])
        self.setModulator(dict['modulator'])
        self.setIndex(dict['index'])
        self.setCutoff(dict['cutoff'])
        self.setAmp(dict['amp'])
        self.setYMin(dict['ymin'])
        self.setYMax(dict['ymax'])
        self.setLinLog(dict['linlog'])

class AutoModulationFrame(Module): 
    def __init__(self, parent, surface, continuousControl):
        Module.__init__(self, parent, surface, continuousControl)
        
        self.amplitude = 0.7

        box = wx.BoxSizer(wx.VERTICAL)
        self.makeAmplitudeBox(box)
        self.SetSizer(box)
        
        self.Bind(wx.EVT_SLIDER, self.handleAmp, self.sl_amp)        
        
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.SetMaxSize(self.GetSize())
        self.SetPosition((self.parent.GetPosition()[0] + self.parent.GetSize()[0], self.parent.GetPosition()[1]))

        self.widgets = []
        self.controls = {'/amplitude': self.getAmp}

        self.Show(False)

    def getFixedValues(self):
        return []

    def save(self):
        return {'amp': self.getAmp()}

    def load(self, dict):
        self.setAmp(dict['amp'])
