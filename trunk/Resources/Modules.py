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

import wx, sys
from Slider import ControlSlider

class Module(wx.Frame):
    def __init__(self, parent, surface, continuousControl):
        wx.Frame.__init__(self, parent, -1, "Controls")

        menuBar = wx.MenuBar()
        self.menu = wx.Menu()
        self.menu.Append(200, 'Close\tCtrl+W', "")
        self.menu.Append(200, 'Close\tCtrl+P', "")
        self.menu.AppendSeparator()
        self.menu.Append(201, "Run\tCtrl+R", "", wx.ITEM_CHECK)
        menuBar.Append(self.menu, "&File")

        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_CLOSE, self.handleClose)
        self.Bind(wx.EVT_MENU, self.handleClose, id=200)
        self.Bind(wx.EVT_MENU, self.onRun, id=201)

        self.parent = parent
        self.surface = surface
        self.continuousControl = continuousControl

    def onRun(self, event):
        self.parent.onRun(event)
        
    def handleClose(self, event):
        self.Show(False)

    def activateWidgets(self, audioState):
        if audioState:
            for widget in self.widgets:
                widget.Disable()
        else:
            for widget in self.widgets:
                widget.Enable()

    def initControlValues(self):
        for key, func in self.controls.iteritems():
            self.continuousControl(key, func())

    def makeGrainOverlapsBox(self, box):
        box.Add(wx.StaticText(self, -1, "Number of grains"), 0, wx.LEFT|wx.TOP, 10)
        overlapsBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_overlaps = ControlSlider(self, 1, 48, self.grainoverlaps, size=(250, 16), integer=True, outFunction=self.handleGrainOverlaps)
        overlapsBox.Add(self.sl_overlaps, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(overlapsBox, 0, wx.LEFT | wx.RIGHT, 5)

    def handleGrainOverlaps(self, val):
        self.grainoverlaps = val

    def getGrainOverlaps(self):
        return self.grainoverlaps

    def setGrainOverlaps(self, overlaps):
        self.grainoverlaps = overlaps
        self.sl_overlaps.SetValue(overlaps)

    def makeGrainSizeBox(self, box):
        box.AddSpacer(5)
        box.Add(wx.StaticText(self, -1, "Grain size (ms)"), 0, wx.LEFT, 10)
        sizeBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_size = ControlSlider(self, 50, 500, self.grainsize, size=(250, 16), integer=True, outFunction=self.handleGrainSize)
        sizeBox.Add(self.sl_size, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(sizeBox, 0, wx.LEFT | wx.RIGHT, 5)

    def handleGrainSize(self, val):
        self.grainsize = val
        self.continuousControl('/grainsize', self.grainsize)   

    def getGrainSize(self):
        return self.grainsize

    def setGrainSize(self, size):
        self.grainsize = size
        self.sl_size.SetValue(self.grainsize)

    def makeAmplitudeBox(self, box):
        box.AddSpacer(5)
        box.Add(wx.StaticText(self, -1, "Amplitude"), 0, wx.LEFT, 10)
        ampBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_amp = ControlSlider(self, 0, 4, self.amplitude, size=(250, 16), outFunction=self.handleAmp)
        ampBox.Add(self.sl_amp, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(ampBox, 0, wx.LEFT | wx.RIGHT, 5)

    def handleAmp(self, val):
        self.amplitude = val
        self.continuousControl('/amplitude', self.amplitude)   

    def getAmp(self):
        return self.amplitude

    def setAmp(self, amp):
        self.amplitude = amp
        self.sl_amp.SetValue(self.amplitude)

    def makeCutoffBox(self, box):
        box.AddSpacer(5)
        box.Add(wx.StaticText(self, -1, "Lowpass cutoff"), 0, wx.LEFT, 10)
        cutoffBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_cutoff = ControlSlider(self, 100, 18000, self.cutoff, size=(250, 16), integer=True, log=True, outFunction=self.handleCutoff)
        cutoffBox.Add(self.sl_cutoff, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(cutoffBox, 0, wx.LEFT | wx.RIGHT, 5)

    def handleCutoff(self, val):
        self.cutoff = val
        self.continuousControl('/cutoff', self.cutoff)   

    def getCutoff(self):
        return self.cutoff

    def setCutoff(self, cutoff):
        self.cutoff = cutoff
        self.sl_cutoff.SetValue(cutoff)

    def makeTransBox(self, box):
        box.Add(wx.StaticText(self, -1, "Random transposition per grain"), 0, wx.CENTER|wx.TOP, 5)
        box.Add(wx.StaticText(self, -1, "List of transposition ratios"), 0, wx.CENTER|wx.TOP, 1)
        transBox = wx.BoxSizer(wx.HORIZONTAL)
        self.tx_trans = wx.TextCtrl( self, -1, "1, ", size=(250, -1))
        transBox.Add(self.tx_trans, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(transBox, 0, wx.ALL, 5)                        

    def getTrans(self):
        return [float(value) for value in self.tx_trans.GetValue().split(',') if value not in [" ", ""]]

    def setTrans(self, trans):
        self.tx_trans.SetValue(", ".join(str(t) for t in trans))

    def makeFFTSizeBox(self, box):
        box.AddSpacer(5)
        box.Add(wx.StaticText(self, -1, "FFT size (power of 2)"), 0, wx.LEFT, 10)
        fftsizeBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_fftsize = ControlSlider(self, 5, 14, self.fftsize, size=(250, 16), powoftwo=True, outFunction=self.handleFFTSize)
        fftsizeBox.Add(self.sl_fftsize, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(fftsizeBox, 0, wx.LEFT | wx.RIGHT, 5)

    def handleFFTSize(self, val):
        print val
        self.fftsize = val

    def getFFTSize(self):
        return self.fftsize

    def setFFTSize(self, fftsize):
        self.fftsize = fftsize
        self.sl_fftsize.SetValue(self.fftsize)

    def makeFFTOverlapsBox(self, box):
        box.AddSpacer(5)
        box.Add(wx.StaticText(self, -1, "FFT Overlaps"), 0, wx.LEFT, 10)
        overlapsBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_overlaps = ControlSlider(self, 2, 16, self.overlaps, size=(250, 16), integer=True, outFunction=self.handleOverlaps)
        overlapsBox.Add(self.sl_overlaps, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(overlapsBox, 0, wx.LEFT | wx.RIGHT, 5)

    def handleOverlaps(self, val):
        self.overlaps = val

    def getOverlaps(self):
        return self.overlaps

    def setOverlaps(self, overlaps):
        self.overlaps = overlaps
        self.sl_overlaps.SetValue(self.overlaps)

    def makeFFTWinSizeBox(self, box):
        box.AddSpacer(5)
        box.Add(wx.StaticText(self, -1, "FFT window size ( >= FFT size)"), 0, wx.LEFT, 10)
        winsizeBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_winsize = ControlSlider(self, 5, 14, self.winsize, size=(250, 16), powoftwo=True, outFunction=self.handleWindowSize)
        winsizeBox.Add(self.sl_winsize, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(winsizeBox, 0, wx.LEFT | wx.RIGHT, 5)

    def handleWindowSize(self, val):
        self.winsize = val

    def getWindowSize(self):
        return self.winsize

    def setWindowSize(self, winsize):
        self.winsize = winsize
        self.sl_winsize.SetValue(self.winsize)

    def makeNumBinsBox(self, box):
        box.AddSpacer(5)
        box.Add(wx.StaticText(self, -1, "Number of bins to synthesize"), 0, wx.LEFT, 10)
        numbinsBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_numbins = ControlSlider(self, 1, 200, self.numbins, size=(250, 16), integer=True, outFunction=self.handleNumBins)
        numbinsBox.Add(self.sl_numbins, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(numbinsBox, 0, wx.LEFT | wx.RIGHT, 5)

    def handleNumBins(self, val):
        self.numbins = val

    def getNumBins(self):
        return self.numbins

    def setNumBins(self, num):
        self.numbins = num
        self.sl_numbins.SetValue(self.numbins)

    def makeFirstBinBox(self, box):
        box.AddSpacer(5)
        box.Add(wx.StaticText(self, -1, "First bin"), 0, wx.LEFT, 10)
        firstBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_first = ControlSlider(self, 0, 50, self.first, size=(250, 16), integer=True, outFunction=self.handleFirst)
        firstBox.Add(self.sl_first, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(firstBox, 0, wx.LEFT | wx.RIGHT, 5)

    def handleFirst(self, val):
        self.first = val

    def getFirst(self):
        return self.first

    def setFirst(self, first):
        self.first = first
        self.sl_first.SetValue(self.first)

    def makeIncrementBox(self, box):
        box.AddSpacer(5)
        box.Add(wx.StaticText(self, -1, "Bin increment"), 0, wx.LEFT, 10)
        incrBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_incr = ControlSlider(self, 1, 50, self.incr, size=(250, 16), integer=True, outFunction=self.handleIncr)
        incrBox.Add(self.sl_incr, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(incrBox, 0, wx.LEFT | wx.RIGHT, 5)
           
    def handleIncr(self, val):
        self.incr = val

    def getIncr(self):
        return self.incr

    def setIncr(self, incr):
        self.incr = incr    
        self.sl_incr.SetValue(self.incr)    

    def makeTranspoBox(self, box):
        box.AddSpacer(5)
        box.Add(wx.StaticText(self, -1, "Sound transposition"), 0, wx.LEFT, 10)
        transpoBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sl_transpo = ControlSlider(self, 0, 2, self.transpo, size=(250, 16), outFunction=self.handleTranspo)
        transpoBox.Add(self.sl_transpo, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(transpoBox, 0, wx.LEFT | wx.RIGHT, 5)
   
    def handleTranspo(self, val):
        self.transpo = val
        self.continuousControl('/transpo', self.transpo)   

    def getTranspo(self):
        return self.transpo

    def setTranspo(self, transpo):
        self.transpo = transpo
        self.sl_transpo.SetValue(transpo)
   
    def makeYaxisTranspoBox(self, box, label=None):
        if label == None: lab = "Y axis (transposition)"
        else: lab = label
        box.Add(wx.StaticText(self, -1, lab), 0, wx.CENTER|wx.TOP|wx.BOTTOM, 5)
        textBox = wx.BoxSizer(wx.HORIZONTAL)
        self.tx_ytrans_ch = wx.CheckBox(self, -1, "")
        self.tx_ytrans_ch.SetValue(1)
        textBox.Add(self.tx_ytrans_ch, 0, wx.LEFT | wx.RIGHT, 10)
        textBox.Add(wx.StaticText(self, -1, "Min: "), 0, wx.TOP, 4)
        self.tx_tr_ymin = wx.TextCtrl( self, -1, "0.", size=(50, -1))
        textBox.Add(self.tx_tr_ymin, 0, wx.RIGHT, 20)
        textBox.Add(wx.StaticText(self, -1, "Max: "), 0, wx.TOP, 4)
        self.tx_tr_ymax = wx.TextCtrl( self, -1, "1.", size=(50, -1))
        textBox.Add(self.tx_tr_ymax, 0, wx.RIGHT, 20)
        box.Add(textBox, 0, wx.LEFT | wx.RIGHT, 10)

    def getTransCheck(self):
        return self.tx_ytrans_ch.GetValue()

    def setTransCheck(self, value):
        self.tx_ytrans_ch.SetValue(value)
                        
    def getTransYMin(self):
        return float(self.tx_tr_ymin.GetValue())

    def setTransYMin(self, ymin):
        self.tx_tr_ymin.SetValue(str(ymin))
    
    def getTransYMax(self):
        return float(self.tx_tr_ymax.GetValue())

    def setTransYMax(self, ymax):
        self.tx_tr_ymax.SetValue(str(ymax))

    def makeYaxisCutoffBox(self, box, label=None):
        if label == None: lab = "Y axis (lowpass cutoff)"
        else: lab = label
        box.AddSpacer(5)
        box.Add(wx.StaticText(self, -1, lab), 0, wx.CENTER|wx.TOP, 5)
        self.tx_filtype = wx.Choice(self, -1, choices = ['Lowpass', 'Highpass', 'Bandpass', 'Bandreject'])
        self.tx_filtype.SetSelection(0)
        box.Add(self.tx_filtype, 0, wx.CENTER | wx.TOP, 5)
        textBox = wx.BoxSizer(wx.HORIZONTAL)
        self.tx_ycutoff_ch = wx.CheckBox(self, -1, "")
        self.tx_ycutoff_ch.SetValue(0)
        textBox.Add(self.tx_ycutoff_ch, 0, wx.LEFT | wx.RIGHT, 10)
        textBox.Add(wx.StaticText(self, -1, "Min: "), 0, wx.TOP, 4)
        self.tx_cut_ymin = wx.TextCtrl( self, -1, "100", size=(50, -1))
        textBox.Add(self.tx_cut_ymin, 0, wx.RIGHT, 20)
        textBox.Add(wx.StaticText(self, -1, "Max: "), 0, wx.TOP, 4)
        self.tx_cut_ymax = wx.TextCtrl( self, -1, "10000", size=(50, -1))
        textBox.Add(self.tx_cut_ymax, 0, wx.RIGHT, 20)
        box.Add(textBox, 0, wx.ALL, 10)

    def getCutoffCheck(self):
        return self.tx_ycutoff_ch.GetValue()

    def setCutoffCheck(self, value):
        self.tx_ycutoff_ch.SetValue(value)

    def getFilterType(self):
        return self.tx_filtype.GetSelection()

    def setFilterType(self, filtype):
        self.tx_filtype.SetSelection(filtype)
                        
    def getCutoffYMin(self):
        return float(self.tx_cut_ymin.GetValue())

    def setCutoffYMin(self, ymin):
        self.tx_cut_ymin.SetValue(str(ymin))
    
    def getCutoffYMax(self):
        return float(self.tx_cut_ymax.GetValue())

    def setCutoffYMax(self, ymax):
        self.tx_cut_ymax.SetValue(str(ymax))

    def makeYaxisRingBox(self, box, label=None):
        if label == None: lab = "Y axis (Ring Mod frequency)"
        else: lab = label
        box.Add(wx.StaticText(self, -1, lab), 0, wx.CENTER|wx.TOP, 5)
        self.tx_ringwav = wx.Choice(self, -1, choices = ['Sine', 'Square', 'Sawtooth'])
        self.tx_ringwav.SetSelection(0)
        box.Add(self.tx_ringwav, 0, wx.CENTER | wx.TOP | wx.BOTTOM, 5)
        textBox = wx.BoxSizer(wx.HORIZONTAL)
        self.tx_yring_ch = wx.CheckBox(self, -1, "")
        self.tx_yring_ch.SetValue(0)
        textBox.Add(self.tx_yring_ch, 0, wx.LEFT | wx.RIGHT, 10)
        textBox.Add(wx.StaticText(self, -1, "Min: "), 0, wx.TOP, 4)
        self.tx_ring_ymin = wx.TextCtrl( self, -1, "0.", size=(50, -1))
        textBox.Add(self.tx_ring_ymin, 0, wx.RIGHT, 20)
        textBox.Add(wx.StaticText(self, -1, "Max: "), 0, wx.TOP, 4)
        self.tx_ring_ymax = wx.TextCtrl( self, -1, "100.", size=(50, -1))
        textBox.Add(self.tx_ring_ymax, 0, wx.RIGHT, 20)
        box.AddSpacer(5)
        box.Add(textBox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

    def getRingCheck(self):
        return self.tx_yring_ch.GetValue()

    def setRingCheck(self, value):
        self.tx_yring_ch.SetValue(value)

    def getRingWav(self):
        return self.tx_ringwav.GetSelection()

    def setRingWav(self, wav):
        self.tx_ringwav.SetSelection(wav)
                        
    def getRingYMin(self):
        return float(self.tx_ring_ymin.GetValue())

    def setRingYMin(self, ymin):
        self.tx_ring_ymin.SetValue(str(ymin))
    
    def getRingYMax(self):
        return float(self.tx_ring_ymax.GetValue())

    def setRingYMax(self, ymax):
        self.tx_ring_ymax.SetValue(str(ymax))

    def makeYaxisDistoBox(self, box, label=None):
        if label == None: lab = "Y axis (Distortion drive)"
        else: lab = label
        box.Add(wx.StaticText(self, -1, lab), 0, wx.CENTER|wx.TOP|wx.BOTTOM, 5)
        textBox = wx.BoxSizer(wx.HORIZONTAL)
        self.tx_ydisto_ch = wx.CheckBox(self, -1, "")
        self.tx_ydisto_ch.SetValue(0)
        textBox.Add(self.tx_ydisto_ch, 0, wx.LEFT | wx.RIGHT, 10)
        textBox.Add(wx.StaticText(self, -1, "Min: "), 0, wx.TOP, 4)
        self.tx_disto_ymin = wx.TextCtrl( self, -1, "0.", size=(50, -1))
        textBox.Add(self.tx_disto_ymin, 0, wx.RIGHT, 20)
        textBox.Add(wx.StaticText(self, -1, "Max: "), 0, wx.TOP, 4)
        self.tx_disto_ymax = wx.TextCtrl( self, -1, "1.", size=(50, -1))
        textBox.Add(self.tx_disto_ymax, 0, wx.RIGHT, 20)
        box.Add(textBox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
    def getDistoCheck(self):
        return self.tx_ydisto_ch.GetValue()

    def setDistoCheck(self, value):
        self.tx_ydisto_ch.SetValue(value)
                 
    def getDistoYMin(self):
        return float(self.tx_disto_ymin.GetValue())

    def setDistoYMin(self, ymin):
        self.tx_disto_ymin.SetValue(str(ymin))
    
    def getDistoYMax(self):
        return float(self.tx_disto_ymax.GetValue())

    def setDistoYMax(self, ymax):
        self.tx_disto_ymax.SetValue(str(ymax))
                     
class GranulatorFrame(Module): 
    def __init__(self, parent, surface, continuousControl):
        Module.__init__(self, parent, surface, continuousControl)
  
        self.grainoverlaps = 8
        self.grainsize = 200
        self.cutoff = 10000
        self.amplitude = 0.7
        
        box = wx.BoxSizer(wx.VERTICAL)
        self.makeGrainOverlapsBox(box)
        self.makeGrainSizeBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.TOP, 5)
        self.makeCutoffBox(box)
        self.makeAmplitudeBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.TOP, 5)
        self.makeTransBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)
        self.makeYaxisTranspoBox(box)
        self.makeYaxisCutoffBox(box)
        self.makeYaxisRingBox(box)
        self.makeYaxisDistoBox(box)
        self.SetSizer(box)
        
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.SetMaxSize(self.GetSize())
        self.SetPosition((self.parent.GetPosition()[0] + self.parent.GetSize()[0], self.parent.GetPosition()[1]))

        self.widgets = [self.sl_overlaps, self.tx_ytrans_ch, self.tx_ycutoff_ch, self.tx_filtype, 
                        self.tx_yring_ch, self.tx_ringwav, self.tx_ydisto_ch]
        self.controls = {'/amplitude': self.getAmp, '/cutoff': self.getCutoff, '/grainsize': self.getGrainSize}

        self.Show(False)

    def getFixedValues(self):
        return [self.grainoverlaps, self.getTrans(), self.getTransCheck(), self.getTransYMin(), self.getTransYMax(),
                self.getCutoffCheck(), self.getCutoffYMin(), self.getCutoffYMax(), self.getFilterType(),
                self.getRingCheck(), self.getRingYMin(), self.getRingYMax(), self.getRingWav(), self.getDistoCheck(), self.getDistoYMin(), self.getDistoYMax()]

    def save(self):
        return {'grainoverlaps': self.getGrainOverlaps(),
                'grainsize': self.getGrainSize(),
                'cutoff': self.getCutoff(),
                'amp': self.getAmp(),
                'trans': self.getTrans(),
                'transCheck': self.getTransCheck(),
                'transYmin': self.getTransYMin(),
                'transYmax': self.getTransYMax(),
                'cutoffCheck': self.getCutoffCheck(),
                'cutoffYmin': self.getCutoffYMin(),
                'cutoffYmax': self.getCutoffYMax(),
                'filterType': self.getFilterType(),
                'ringCheck': self.getRingCheck(),
                'ringYmin': self.getRingYMin(),
                'ringYmax': self.getRingYMax(),
                'ringwav': self.getRingWav(),
                'distoCheck': self.getDistoCheck(),
                'distoYmin': self.getDistoYMin(),
                'distoYmax': self.getDistoYMax()}

    def load(self, dict):
        self.setGrainOverlaps(dict['grainoverlaps'])
        self.setGrainSize(dict['grainsize'])
        self.setCutoff(dict['cutoff'])
        self.setAmp(dict['amp'])
        self.setTrans(dict['trans'])
        self.setTransCheck(dict['transCheck'])
        self.setTransYMin(dict['transYmin'])
        self.setTransYMax(dict['transYmax'])
        self.setCutoffCheck(dict['cutoffCheck'])
        self.setCutoffYMin(dict['cutoffYmin'])
        self.setCutoffYMax(dict['cutoffYmax'])
        self.setFilterType(dict['filterType'])
        self.setRingCheck(dict['ringCheck'])
        self.setRingYMin(dict['ringYmin'])
        self.setRingYMax(dict['ringYmax'])
        self.setRingWav(dict['ringwav'])
        self.setDistoCheck(dict['distoCheck'])
        self.setDistoYMin(dict['distoYmin'])
        self.setDistoYMax(dict['distoYmax'])

class FFTReaderFrame(Module): 
    def __init__(self, parent, surface, continuousControl):
        Module.__init__(self, parent, surface, continuousControl)

        self.fftsize = 1024        
        self.overlaps = 8
        self.winsize = 2048 
        self.cutoff = 10000
        self.amplitude = 0.7

        box = wx.BoxSizer(wx.VERTICAL)
        self.makeFFTSizeBox(box)
        self.makeFFTOverlapsBox(box)
        self.makeFFTWinSizeBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.TOP, 5)
        self.makeCutoffBox(box)
        self.makeAmplitudeBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.TOP, 5)
        self.makeYaxisTranspoBox(box)
        self.makeYaxisCutoffBox(box)
        self.makeYaxisRingBox(box)
        self.makeYaxisDistoBox(box)
        self.SetSizer(box)
       
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.SetMaxSize(self.GetSize())
        self.SetPosition((self.parent.GetPosition()[0] + self.parent.GetSize()[0], self.parent.GetPosition()[1]))

        self.widgets = [self.sl_fftsize, self.sl_overlaps, self.sl_winsize,
                        self.tx_ytrans_ch, self.tx_ycutoff_ch, self.tx_filtype, self.tx_yring_ch, self.tx_ringwav, self.tx_ydisto_ch]
        self.controls = {'/amplitude': self.getAmp, '/cutoff': self.getCutoff}

        self.Show(False)

    def getFixedValues(self):
        return [self.fftsize, self.overlaps, self.winsize, self.getTransCheck(), self.getTransYMin(), 
                self.getTransYMax(), self.getCutoffCheck(), self.getCutoffYMin(), self.getCutoffYMax(), self.getFilterType(),
                self.getRingCheck(), self.getRingYMin(), self.getRingYMax(), self.getRingWav(), self.getDistoCheck(), self.getDistoYMin(), self.getDistoYMax()]

    def save(self):
        return {'fftsize': self.getFFTSize(),
                'overlaps': self.getOverlaps(),
                'winsize': self.getWindowSize(),
                'cutoff': self.getCutoff(),
                'amp': self.getAmp(),
                'transCheck': self.getTransCheck(),
                'transYmin': self.getTransYMin(),
                'transYmax': self.getTransYMax(),
                'cutoffCheck': self.getCutoffCheck(),
                'cutoffYmin': self.getCutoffYMin(),
                'cutoffYmax': self.getCutoffYMax(),
                'filterType': self.getFilterType(),
                'ringCheck': self.getRingCheck(),
                'ringYmin': self.getRingYMin(),
                'ringYmax': self.getRingYMax(),
                'ringwav': self.getRingWav(),
                'distoCheck': self.getDistoCheck(),
                'distoYmin': self.getDistoYMin(),
                'distoYmax': self.getDistoYMax()}

    def load(self, dict):
        self.setFFTSize(dict['fftsize'])
        self.setOverlaps(dict['overlaps'])
        self.setWindowSize(dict['winsize'])
        self.setCutoff(dict['cutoff'])
        self.setAmp(dict['amp'])
        self.setTransCheck(dict['transCheck'])
        self.setTransYMin(dict['transYmin'])
        self.setTransYMax(dict['transYmax'])
        self.setCutoffCheck(dict['cutoffCheck'])
        self.setCutoffYMin(dict['cutoffYmin'])
        self.setCutoffYMax(dict['cutoffYmax'])
        self.setFilterType(dict['filterType'])
        self.setRingCheck(dict['ringCheck'])
        self.setRingYMin(dict['ringYmin'])
        self.setRingYMax(dict['ringYmax'])
        self.setRingWav(dict['ringwav'])
        self.setDistoCheck(dict['distoCheck'])
        self.setDistoYMin(dict['distoYmin'])
        self.setDistoYMax(dict['distoYmax'])

class FFTAdsynFrame(Module): 
    def __init__(self, parent, surface, continuousControl):
        Module.__init__(self, parent, surface, continuousControl)

        self.fftsize = 1024        
        self.overlaps = 8
        self.winsize = 2048 
        self.numbins = 50
        self.first = 0
        self.incr = 3        
        self.cutoff = 10000
        self.amplitude = 0.7

        box = wx.BoxSizer(wx.VERTICAL)
        self.makeFFTSizeBox(box)
        self.makeFFTOverlapsBox(box)
        self.makeFFTWinSizeBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.TOP, 5)
        self.makeNumBinsBox(box)
        self.makeFirstBinBox(box)
        self.makeIncrementBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.TOP, 5)
        self.makeCutoffBox(box)
        self.makeAmplitudeBox(box)
        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.TOP, 5)
        self.makeYaxisTranspoBox(box)
        self.makeYaxisCutoffBox(box)
        self.makeYaxisRingBox(box)
        self.makeYaxisDistoBox(box)
        self.SetSizer(box)
        
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.SetMaxSize(self.GetSize())
        self.SetPosition((self.parent.GetPosition()[0] + self.parent.GetSize()[0], self.parent.GetPosition()[1]))

        self.widgets = [self.sl_fftsize, self.sl_overlaps, self.sl_winsize, self.sl_numbins, self.sl_first, self.sl_incr,
                        self.tx_ytrans_ch, self.tx_ycutoff_ch, self.tx_filtype, self.tx_yring_ch, self.tx_ringwav, self.tx_ydisto_ch]
        self.controls = {'/amplitude': self.getAmp, '/cutoff': self.getCutoff}

        self.Show(False)

    def getFixedValues(self):
        return [self.fftsize, self.overlaps, self.winsize, self.numbins, self.first, self.incr, self.getTransCheck(), 
                self.getTransYMin(), self.getTransYMax(), self.getCutoffCheck(), self.getCutoffYMin(), self.getCutoffYMax(), 
                self.getFilterType(), self.getRingCheck(), self.getRingYMin(), self.getRingYMax(), self.getRingWav(), self.getDistoCheck(), 
                self.getDistoYMin(), self.getDistoYMax()]

    def save(self):
        return {'fftsize': self.getFFTSize(),
                'overlaps': self.getOverlaps(),
                'winsize': self.getWindowSize(),
                'numbins': self.getNumBins(),
                'first': self.getFirst(),
                'incr': self.getIncr(),
                'cutoff': self.getCutoff(),
                'amp': self.getAmp(),
                'transCheck': self.getTransCheck(),
                'transYmin': self.getTransYMin(),
                'transYmax': self.getTransYMax(),
                'cutoffCheck': self.getCutoffCheck(),
                'cutoffYmin': self.getCutoffYMin(),
                'cutoffYmax': self.getCutoffYMax(),
                'filterType': self.getFilterType(),
                'ringCheck': self.getRingCheck(),
                'ringYmin': self.getRingYMin(),
                'ringYmax': self.getRingYMax(),
                'ringwav': self.getRingWav(),
                'distoCheck': self.getDistoCheck(),
                'distoYmin': self.getDistoYMin(),
                'distoYmax': self.getDistoYMax()}

    def load(self, dict):
        self.setFFTSize(dict['fftsize'])
        self.setOverlaps(dict['overlaps'])
        self.setWindowSize(dict['winsize'])
        self.setNumBins(dict['numbins'])
        self.setFirst(dict['first'])
        self.setIncr(dict['incr'])
        self.setCutoff(dict['cutoff'])
        self.setAmp(dict['amp'])
        self.setTransCheck(dict['transCheck'])
        self.setTransYMin(dict['transYmin'])
        self.setTransYMax(dict['transYmax'])
        self.setCutoffCheck(dict['cutoffCheck'])
        self.setCutoffYMin(dict['cutoffYmin'])
        self.setCutoffYMax(dict['cutoffYmax'])
        self.setFilterType(dict['filterType'])
        self.setRingCheck(dict['ringCheck'])
        self.setRingYMin(dict['ringYmin'])
        self.setRingYMax(dict['ringYmax'])
        self.setRingWav(dict['ringwav'])
        self.setDistoCheck(dict['distoCheck'])
        self.setDistoYMin(dict['distoYmin'])
        self.setDistoYMax(dict['distoYmax'])
