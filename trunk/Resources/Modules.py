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
from pyolib._wxwidgets import ControlSlider
from constants import BACKGROUND_COLOUR

class Module(wx.Frame):
    def __init__(self, parent, surface, sg_audio):
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
        self.sg_audio = sg_audio

        self.panel = wx.Panel(self, -1)
        self.panel.SetBackgroundColour(BACKGROUND_COLOUR)
        self.notebook = wx.Notebook(self.panel, -1, style=wx.BK_DEFAULT | wx.EXPAND)
        self.panel1 = wx.Panel(self.notebook, wx.ID_ANY)
        self.panel1.SetBackgroundColour(BACKGROUND_COLOUR)
        self.panel2 = wx.Panel(self.notebook, wx.ID_ANY)
        self.panel2.SetBackgroundColour(BACKGROUND_COLOUR)
        self.box1 = wx.BoxSizer(wx.VERTICAL)
        self.box2 = wx.BoxSizer(wx.VERTICAL)
        
    def onRun(self, event):
        self.parent.onRun(event)
        
    def handleClose(self, event):
        self.Show(False)

    ########################################################################################################    
    ### First window ###
    ########################################################################################################
    def makeSliderBox(self, box, label, minval, maxval, val, integer, callback):
        box.Add(wx.StaticText(self.panel1, -1, label), 0, wx.LEFT, 10)
        sliderBox = wx.BoxSizer(wx.HORIZONTAL)
        slider = ControlSlider(self.panel1, minval, maxval, val, size=(250, 16), integer=integer, outFunction=callback)
        sliderBox.Add(slider, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(sliderBox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        return slider

    def handleGrainOverlaps(self, val):
        self.grainoverlaps = val
        self.sg_audio.setNumGrains(self.grainoverlaps)

    def getGrainOverlaps(self):
        return self.grainoverlaps

    def setGrainOverlaps(self, overlaps):
        self.grainoverlaps = overlaps
        self.sl_overlaps.SetValue(overlaps)
        self.sg_audio.setNumGrains(self.grainoverlaps)

    def handlePitch(self, val):
        self.pitch = val
        self.sg_audio.setBasePitch(self.pitch)  

    def getPitch(self):
        return self.pitch

    def setPitch(self, pitch):
        self.pitch = pitch
        self.sl_pit.SetValue(self.pitch)
        self.sg_audio.setBasePitch(self.pitch)  

    def handleGrainSize(self, val):
        self.grainsize = val
        self.sg_audio.setGrainSize(self.grainsize * 0.001)  

    def getGrainSize(self):
        return self.grainsize

    def setGrainSize(self, size):
        self.grainsize = size
        self.sl_size.SetValue(self.grainsize)
        self.sg_audio.setGrainSize(self.grainsize * 0.001)  

    def handleRandDur(self, val):
        self.rnddur = val
        self.sg_audio.dur_noise.mul = self.rnddur * self.grainsize * 0.001

    def getRandDur(self):
        return self.rnddur

    def setRandDur(self, rnd):
        self.rnddur = rnd
        self.sl_rnddur.SetValue(self.rnddur)
        self.sg_audio.dur_noise.mul = self.rnddur * self.grainsize * 0.001

    def handleRandPos(self, val):
        self.rndpos = val
        self.sg_audio.pos_noise.mul = self.rndpos

    def getRandPos(self):
        return self.rndpos

    def setRandPos(self, rnd):
        self.rndpos = rnd
        self.sl_rndpos.SetValue(self.rndpos)
        self.sg_audio.pos_noise.mul = self.rndpos

    def handleAmp(self, val):
        self.amplitude = val
        self.sg_audio.amplitude.value = self.amplitude

    def getAmp(self):
        return self.amplitude

    def setAmp(self, amp):
        self.amplitude = amp
        self.sl_amp.SetValue(self.amplitude)
        self.sg_audio.amplitude.value = self.amplitude

    def makeTransBox(self, box):
        box.Add(wx.StaticText(self.panel1, -1, "Random transposition per grain"), 0, wx.CENTER|wx.TOP, 5)
        box.Add(wx.StaticText(self.panel1, -1, "List of transposition ratios"), 0, wx.CENTER|wx.TOP, 1)
        transBox = wx.BoxSizer(wx.HORIZONTAL)
        self.tx_trans = wx.TextCtrl(self.panel1, -1, "1, ", size=(250, -1), style=wx.TE_PROCESS_ENTER)
        self.tx_trans.Bind(wx.EVT_TEXT_ENTER, self.handleTrans)
        transBox.Add(self.tx_trans, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(transBox, 0, wx.ALL, 5)                        

    def getTrans(self):
        return [float(value) for value in self.tx_trans.GetValue().split(',') if value not in [" ", ""]]

    def setTrans(self, trans):
        self.tx_trans.SetValue(", ".join(str(t) for t in trans))           
        self.sg_audio.trans_noise.choice = self.getTrans()

    def handleTrans(self, event):
        self.sg_audio.trans_noise.choice = self.getTrans()
    
    ########################################################################################################    
    ### Second window ###
    ########################################################################################################
    def makeYaxisBox(self, box, label, checked, ch_callback, minval, min_callback, maxval, max_callback):
        box.Add(wx.StaticText(self.panel2, -1, label), 0, wx.CENTER|wx.TOP|wx.BOTTOM, 5)
        textBox = wx.BoxSizer(wx.HORIZONTAL)
        tx_check = wx.CheckBox(self.panel2, -1, "")
        tx_check.SetValue(checked)
        tx_check.Bind(wx.EVT_CHECKBOX, ch_callback)
        textBox.Add(tx_check, 0, wx.LEFT | wx.RIGHT, 10)
        textBox.Add(wx.StaticText(self.panel2, -1, "Min: "), 0, wx.TOP, 4)
        tx_min = wx.TextCtrl(self.panel2, -1, minval, size=(50, -1), style=wx.TE_PROCESS_ENTER)
        tx_min.Bind(wx.EVT_TEXT_ENTER, min_callback)
        textBox.Add(tx_min, 0, wx.RIGHT, 20)
        textBox.Add(wx.StaticText(self.panel2, -1, "Max: "), 0, wx.TOP, 4)
        tx_max = wx.TextCtrl(self.panel2, -1, maxval, size=(50, -1), style=wx.TE_PROCESS_ENTER)
        tx_max.Bind(wx.EVT_TEXT_ENTER, max_callback)
        textBox.Add(tx_max, 0, wx.RIGHT, 20)
        box.Add(textBox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        return tx_check, tx_min, tx_max

    def getTransCheck(self):
        return self.tx_ytrans_ch.GetValue()

    def setTransCheck(self, value):
        self.tx_ytrans_ch.SetValue(value)
        self.sg_audio.pitch_check = self.tx_ytrans_ch.GetValue()
    
    def handleTransCheck(self, event):
        self.sg_audio.pitch_check = self.tx_ytrans_ch.GetValue()
   
    def getTransYMin(self):
        return float(self.tx_tr_ymin.GetValue())

    def setTransYMin(self, ymin):
        self.tx_tr_ymin.SetValue(str(ymin))
        self.sg_audio.pitch_map.setMin(float(self.tx_tr_ymin.GetValue()))

    def handleTransYMin(self, event):
        self.sg_audio.pitch_map.setMin(float(self.tx_tr_ymin.GetValue()))
        
    def getTransYMax(self):
        return float(self.tx_tr_ymax.GetValue())

    def setTransYMax(self, ymax):
        self.tx_tr_ymax.SetValue(str(ymax))
        self.sg_audio.pitch_map.setMax(float(self.tx_tr_ymax.GetValue()))

    def handleTransYMax(self, event):
        self.sg_audio.pitch_map.setMax(float(self.tx_tr_ymax.GetValue()))

    def getAmpCheck(self):
        return self.tx_yamp_ch.GetValue()

    def setAmpCheck(self, value):
        self.tx_yamp_ch.SetValue(value)
        self.sg_audio.amp_check = self.tx_yamp_ch.GetValue()

    def handleAmpCheck(self, event):
        self.sg_audio.amp_check = self.tx_yamp_ch.GetValue()

    def getAmpYMin(self):
        return float(self.tx_amp_ymin.GetValue())

    def setAmpYMin(self, ymin):
        self.tx_amp_ymin.SetValue(str(ymin))
        self.sg_audio.amp_map.setMin(float(self.tx_amp_ymin.GetValue()))

    def handleAmpYMin(self, event):
        self.sg_audio.amp_map.setMin(float(self.tx_amp_ymin.GetValue()))

    def getAmpYMax(self):
        return float(self.tx_amp_ymax.GetValue())

    def setAmpYMax(self, ymax):
        self.tx_amp_ymax.SetValue(str(ymax))
        self.sg_audio.amp_map.setMax(float(self.tx_amp_ymax.GetValue()))

    def handleAmpYMax(self, event):
        self.sg_audio.amp_map.setMax(float(self.tx_amp_ymax.GetValue()))

    def getDurCheck(self):
        return self.tx_ydur_ch.GetValue()

    def setDurCheck(self, value):
        self.tx_ydur_ch.SetValue(value)
        self.sg_audio.dur_check = self.tx_ydur_ch.GetValue()

    def handleDurCheck(self, event):
        self.sg_audio.dur_check = self.tx_ydur_ch.GetValue()

    def getDurYMin(self):
        return float(self.tx_dur_ymin.GetValue())

    def setDurYMin(self, ymin):
        self.tx_dur_ymin.SetValue(str(ymin))
        self.sg_audio.dur_map.setMin(float(self.tx_dur_ymin.GetValue()))

    def handleDurYMin(self, event):
        self.sg_audio.dur_map.setMin(float(self.tx_dur_ymin.GetValue()))

    def getDurYMax(self):
        return float(self.tx_dur_ymax.GetValue())

    def setDurYMax(self, ymax):
        self.tx_dur_ymax.SetValue(str(ymax))
        self.sg_audio.dur_map.setMax(float(self.tx_dur_ymax.GetValue()))

    def handleDurYMax(self, event):
        self.sg_audio.dur_map.setMax(float(self.tx_dur_ymax.GetValue()))

    def getPosCheck(self):
        return self.tx_ypos_ch.GetValue()

    def setPosCheck(self, value):
        self.tx_ypos_ch.SetValue(value)
        self.sg_audio.pos_check = self.tx_ypos_ch.GetValue()

    def handlePosCheck(self, event):
        self.sg_audio.pos_check = self.tx_ypos_ch.GetValue()

    def getPosYMin(self):
        return float(self.tx_pos_ymin.GetValue())

    def setPosYMin(self, ymin):
        self.tx_pos_ymin.SetValue(str(ymin))
        self.sg_audio.pos_map.setMin(float(self.tx_pos_ymin.GetValue()))

    def handlePosYMin(self, event):
        self.sg_audio.pos_map.setMin(float(self.tx_pos_ymin.GetValue()))

    def getPosYMax(self):
        return float(self.tx_pos_ymax.GetValue())

    def setPosYMax(self, ymax):
        self.tx_pos_ymax.SetValue(str(ymax))
        self.sg_audio.pos_map.setMax(float(self.tx_pos_ymax.GetValue()))

    def handlePosYMax(self, event):
        self.sg_audio.pos_map.setMax(float(self.tx_pos_ymax.GetValue()))
                     
class GranulatorFrame(Module): 
    def __init__(self, parent, surface, sg_audio):
        Module.__init__(self, parent, surface, sg_audio)
  
        self.grainoverlaps = 8
        self.pitch = 1.
        self.grainsize = 200
        self.rnddur = 0
        self.rndpos = 0
        self.amplitude = 0.7
        
        box = wx.BoxSizer(wx.VERTICAL)
        
        self.box1.AddSpacer(10)
        self.sl_overlaps = self.makeSliderBox(self.box1, "Number of grains", 1, 100, self.grainoverlaps, True, self.handleGrainOverlaps)
        self.sl_pit = self.makeSliderBox(self.box1, "Transposition", 0.5, 2., self.pitch, False, self.handlePitch)
        self.sl_size = self.makeSliderBox(self.box1, "Grain size (ms)", 10, 500, self.grainsize, True, self.handleGrainSize)
        self.sl_rnddur = self.makeSliderBox(self.box1, "Grain duration random", 0, 0.5, self.rnddur, False, self.handleRandDur)
        self.sl_rndpos = self.makeSliderBox(self.box1, "Position random", 0, 0.5, self.rndpos, False, self.handleRandPos)
        self.sl_amp = self.makeSliderBox(self.box1, "Amplitude", 0, 4, self.amplitude, False, self.handleAmp)
        self.makeTransBox(self.box1)
        self.panel1.SetSizer(self.box1)
        self.notebook.AddPage(self.panel1, "Granulator")
        
        self.tx_ytrans_ch, self.tx_tr_ymin, self.tx_tr_ymax = self.makeYaxisBox(self.box2, "Transposition", 1, self.handleTransCheck, 
                                                                                "0.", self.handleTransYMin, "1.", self.handleTransYMax)
        self.tx_yamp_ch, self.tx_amp_ymin, self.tx_amp_ymax = self.makeYaxisBox(self.box2, "Amplitude", 0, self.handleAmpCheck, 
                                                                                "0.", self.handleAmpYMin, "1.", self.handleAmpYMax)
        self.tx_ydur_ch, self.tx_dur_ymin, self.tx_dur_ymax = self.makeYaxisBox(self.box2, "Grains duration random", 0, self.handleDurCheck, 
                                                                                "0.", self.handleDurYMin, "0.5", self.handleDurYMax)
        self.tx_ypos_ch, self.tx_pos_ymin, self.tx_pos_ymax = self.makeYaxisBox(self.box2, "Grains Position random", 0, self.handlePosCheck, 
                                                                                "0.", self.handlePosYMin, "0.5", self.handlePosYMax)
        self.panel2.SetSizer(self.box2)
        self.notebook.AddPage(self.panel2, "Y Axis")
        
        box.Add(self.notebook, 0, wx.ALL, 5)
        self.panel.SetSizerAndFit(box)
        
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.SetMaxSize(self.GetSize())
        self.SetPosition((self.parent.GetPosition()[0] + self.parent.GetSize()[0], self.parent.GetPosition()[1]))
        self.Show(False)

    def save(self):
        return {'grainoverlaps': self.getGrainOverlaps(),
                'grainsize': self.getGrainSize(),
                'pitch': self.getPitch(),
                'rnddur': self.getRandDur(),
                'rndpos': self.getRandPos(),
                'amp': self.getAmp(),
                'trans': self.getTrans(),
                'transCheck': self.getTransCheck(),
                'transYmin': self.getTransYMin(),
                'transYmax': self.getTransYMax(),
                'ampCheck': self.getAmpCheck(),
                'ampYmin': self.getAmpYMin(),
                'ampYmax': self.getAmpYMax(),
                'durCheck': self.getDurCheck(),
                'durYmin': self.getDurYMin(),
                'durYmax': self.getDurYMax(),
                'posCheck': self.getPosCheck(),
                'posYmin': self.getPosYMin(),
                'posYmax': self.getPosYMax()}

    def load(self, dict):
        self.setGrainOverlaps(dict['grainoverlaps'])
        self.setPitch(dict['pitch'])
        self.setGrainSize(dict['grainsize'])
        self.setRandDur(dict['rnddur'])
        self.setRandPos(dict['rndpos'])
        self.setAmp(dict['amp'])
        self.setTrans(dict['trans'])
        self.setTransCheck(dict['transCheck'])
        self.setTransYMin(dict['transYmin'])
        self.setTransYMax(dict['transYmax'])
        self.setAmpCheck(dict['ampCheck'])
        self.setAmpYMin(dict['ampYmin'])
        self.setAmpYMax(dict['ampYmax'])
        self.setDurCheck(dict['durCheck'])
        self.setDurYMin(dict['durYmin'])
        self.setDurYMax(dict['durYmax'])
        self.setPosCheck(dict['posCheck'])
        self.setPosYMin(dict['posYmin'])
        self.setPosYMax(dict['posYmax'])
