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
from pyolib._wxwidgets import ControlSlider
from constants import BACKGROUND_COLOUR

class Module(wx.Frame):
    def __init__(self, parent, sg_audio):
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
        self.sg_audio = sg_audio

        self.panel = wx.Panel(self, -1)
        self.panel.SetBackgroundColour(BACKGROUND_COLOUR)
        self.notebook = wx.Notebook(self.panel, -1, style=wx.BK_DEFAULT | wx.EXPAND)
        self.notebook.SetBackgroundColour(BACKGROUND_COLOUR)
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

    ################################################################################
    ### First window ###
    ################################################################################
    def makeSliderBox(self, box, label, minval, maxval, val, integer, log, callback):
        box.Add(wx.StaticText(self.panel1, -1, label), 0, wx.LEFT, 10)
        sliderBox = wx.BoxSizer(wx.HORIZONTAL)
        slider = ControlSlider(self.panel1, minval, maxval, val, size=(250, 16), 
                               log=log, integer=integer, outFunction=callback)
        sliderBox.Add(slider, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(sliderBox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        return slider

    def handleDensity(self, x, fromSlider=True):
        self.density = x
        self.sg_audio.setDensity(x)
        if not fromSlider:
            self.sl_dens.SetValue(x)

    def handlePitch(self, x, fromSlider=True):
        self.pitch = x
        self.sg_audio.setBasePitch(x)
        if not fromSlider:
            self.sl_pit.SetValue(x)

    def handleGrainDur(self, x, fromSlider=True):
        self.graindur = x
        self.sg_audio.setGrainDur(x)
        if not fromSlider:
            self.sl_dur.SetValue(x)

    def handleGrainDev(self, x, fromSlider=True):
        self.graindev = x
        self.sg_audio.setGrainDev(x)
        if not fromSlider:
            self.sl_dev.SetValue(x)

    def handleRandDens(self, x, fromSlider=True):
        self.rnddens = x
        self.sg_audio.setRandDens(x)
        if not fromSlider:
            self.sl_rnddens.SetValue(x)

    def handleRandDur(self, x, fromSlider=True):
        self.rnddur = x
        self.sg_audio.setRandDur(x)
        if not fromSlider:
            self.sl_rnddur.SetValue(x)

    def handleRandPos(self, x, fromSlider=True):
        self.rndpos = x
        self.sg_audio.setRandPos(x)
        if not fromSlider:
            self.sl_rndpos.SetValue(x)

    def handleRandPit(self, x, fromSlider=True):
        self.rndpit = x
        self.sg_audio.setRandPit(x)
        if not fromSlider:
            self.sl_rndpit.SetValue(x)

    def handleRandPan(self, x, fromSlider=True):
        self.rndpan = x
        self.sg_audio.setRandPan(x)
        if not fromSlider:
            self.sl_rndpan.SetValue(x)

    def makeTransBox(self, box):
        box.Add(wx.StaticText(self.panel1, -1, "Random Transposition per Grain"), 
                              0, wx.CENTER|wx.TOP, 5)
        box.Add(wx.StaticText(self.panel1, -1, "List of Transposition Ratios"), 
                              0, wx.CENTER|wx.TOP, 1)
        transBox = wx.BoxSizer(wx.HORIZONTAL)
        tw, th = self.GetTextExtent("1,2,3,4,5,6,7,8,9,0")
        self.tx_trans = wx.TextCtrl(self.panel1, -1, "1, ", size=(250, th*2), 
                                    style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB)
        self.tx_trans.Bind(wx.EVT_TEXT_ENTER, self.handleTrans)
        self.tx_trans.Bind(wx.EVT_CHAR, self.onCharTrans)
        transBox.Add(self.tx_trans, 0, wx.LEFT | wx.RIGHT, 5)
        box.Add(transBox, 0, wx.ALL, 5)

    def getTrans(self):
        return [float(value) for value in self.tx_trans.GetValue().split(',') if value not in [" ", ""]]

    def setTrans(self, trans):
        self.tx_trans.SetValue(", ".join(str(t) for t in trans))
        self.handleTrans(None)

    def handleTrans(self, evt):
        self.sg_audio.setDiscreteTrans(self.getTrans())

    def onCharTrans(self, evt):
        if evt.GetKeyCode() == wx.WXK_TAB:
            self.handleTrans(evt)
        evt.Skip()

    ########################################################################################################
    ### Second window ###
    ########################################################################################################
    def makeYaxisBox(self, box, label, checked, minval, maxval, name):
        label = wx.StaticText(self.panel2, -1, label)
        font = label.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        label.SetFont(font)
        box.Add(label, 0, wx.CENTER|wx.TOP|wx.BOTTOM, 3)
        textBox = wx.BoxSizer(wx.HORIZONTAL)
        tx_check = wx.CheckBox(self.panel2, -1, "", name="y_%s_check" % name)
        tx_check.SetValue(checked)
        tx_check.Bind(wx.EVT_CHECKBOX, self.handleCheck)
        textBox.Add(tx_check, 0, wx.LEFT | wx.RIGHT, 10)
        textBox.Add(wx.StaticText(self.panel2, -1, "Min: "), 0, wx.TOP, 4)
        tx_min = wx.TextCtrl(self.panel2, -1, minval, size=(50, -1), 
                             style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB, 
                             name="y_%s_map" % name)
        tx_min.Bind(wx.EVT_TEXT_ENTER, self.handleMapMin)
        tx_min.Bind(wx.EVT_CHAR, self.onCharMapMin)
        textBox.Add(tx_min, 0, wx.RIGHT, 20)
        textBox.Add(wx.StaticText(self.panel2, -1, "Max: "), 0, wx.TOP, 4)
        tx_max = wx.TextCtrl(self.panel2, -1, maxval, size=(50, -1), 
                             style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB, 
                             name="y_%s_map" % name)
        tx_max.Bind(wx.EVT_TEXT_ENTER, self.handleMapMax)
        tx_max.Bind(wx.EVT_CHAR, self.onCharMapMax)
        textBox.Add(tx_max, 0, wx.RIGHT, 20)
        box.Add(textBox, 0, wx.LEFT | wx.RIGHT, 10)
        box.AddSpacer(3)
        return tx_check, tx_min, tx_max

    def handleCheck(self, evt):
        which = evt.GetEventObject().GetName()
        self.sg_audio.setCheck(which, evt.GetInt())

    def onCharMapMin(self, evt):
        if evt.GetKeyCode() == wx.WXK_TAB:
            self.handleMapMin(evt)
        evt.Skip()

    def handleMapMin(self, evt):
        which = evt.GetEventObject().GetName()
        value = float(evt.GetEventObject().GetValue())
        self.sg_audio.setMapMin(which, value)

    def onCharMapMax(self, evt):
        if evt.GetKeyCode() == wx.WXK_TAB:
            self.handleMapMax(evt)
        evt.Skip()

    def handleMapMax(self, evt):
        which = evt.GetEventObject().GetName()
        value = float(evt.GetEventObject().GetValue())
        self.sg_audio.setMapMax(which, value)

class GranulatorFrame(Module):
    def __init__(self, parent, sg_audio):
        Module.__init__(self, parent, sg_audio)

        self.density = 32
        self.pitch = 1.
        self.graindur = 200
        self.graindev = 0
        self.rnddens = 0
        self.rnddur = 0
        self.rndpos = 0
        self.rndpit = 0
        self.rndpan = 0

        box = wx.BoxSizer(wx.VERTICAL)

        self.box1.AddSpacer(10)
        self.sl_dens = self.makeSliderBox(self.box1, "Density of Grains per Second", 1, 500, self.density, True, False, self.handleDensity)
        self.sl_pit = self.makeSliderBox(self.box1, "Global Transposition", 0.25, 2., self.pitch, False, False, self.handlePitch)
        self.sl_dur = self.makeSliderBox(self.box1, "Grains Duration (ms)", 5, 500, self.graindur, True, False, self.handleGrainDur)
        self.sl_dev = self.makeSliderBox(self.box1, "Grains Start Time Deviation", 0, 1, self.graindev, False, False, self.handleGrainDev)
        self.sl_rnddens = self.makeSliderBox(self.box1, "Grains Density Random", 0, 1, self.rnddens, False, False, self.handleRandDens)
        self.sl_rndpit = self.makeSliderBox(self.box1, "Grains Pitch Random", 0, 0.5, self.rndpit, False, False, self.handleRandPit)
        self.sl_rnddur = self.makeSliderBox(self.box1, "Grains Duration Random", 0, 1, self.rnddur, False, False, self.handleRandDur)
        self.sl_rndpos = self.makeSliderBox(self.box1, "Grains Position Random", 0, 1, self.rndpos, False, False, self.handleRandPos)
        self.sl_rndpan = self.makeSliderBox(self.box1, "Grains Panning Random", 0, 1, self.rndpan, False, False, self.handleRandPan)
        self.makeTransBox(self.box1)
        self.panel1.SetSizer(self.box1)
        self.notebook.AddPage(self.panel1, "Granulator")

        self.tx_ydns_ch, self.tx_dns_ymin, self.tx_dns_ymax = self.makeYaxisBox(self.box2, "Density of Grains Multiplier", 0, "0.", "1.", "dns")
        self.tx_ypit_ch, self.tx_pit_ymin, self.tx_pit_ymax = self.makeYaxisBox(self.box2, "Transposition Multiplier", 1, "0.", "1.", "pit")
        self.tx_ylen_ch, self.tx_len_ymin, self.tx_len_ymax = self.makeYaxisBox(self.box2, "Grains Duration Multiplier", 0, "0.", "1.", "len")
        self.tx_ydev_ch, self.tx_dev_ymin, self.tx_dev_ymax = self.makeYaxisBox(self.box2, "Grains Start Time Deviation", 0, "0.", "1.", "dev")
        self.tx_yamp_ch, self.tx_amp_ymin, self.tx_amp_ymax = self.makeYaxisBox(self.box2, "Amplitude Multiplier", 0, "0.", "1.", "amp")
        self.tx_ytrs_ch, self.tx_trs_ymin, self.tx_trs_ymax = self.makeYaxisBox(self.box2, "Grains Transposition Random", 0, "0.", "1.", "trs")
        self.tx_ydur_ch, self.tx_dur_ymin, self.tx_dur_ymax = self.makeYaxisBox(self.box2, "Grains Duration Random", 0, "0.", "0.5", "dur")
        self.tx_ypos_ch, self.tx_pos_ymin, self.tx_pos_ymax = self.makeYaxisBox(self.box2, "Grains Position Random", 0, "0.", "0.5", "pos")
        self.tx_ypan_ch, self.tx_pan_ymin, self.tx_pan_ymax = self.makeYaxisBox(self.box2, "Grains Panning", 0, "0.", "1.", "pan")
        self.panel2.SetSizer(self.box2)
        self.notebook.AddPage(self.panel2, "Y Axis")

        box.Add(self.notebook, 1, wx.ALL, 5)
        self.panel.SetSizerAndFit(box)

        self.Fit()
        X = self.GetSize()[0]
        Y = self.GetSize()[1] + self.tx_trans.GetSize()[1]
        self.SetMinSize((X,Y))
        self.SetMaxSize((X,Y))
        self.SetPosition((self.parent.GetPosition()[0] + self.parent.GetSize()[0], self.parent.GetPosition()[1]))
        self.Show(False)

    def save(self):
        return {'density': self.density,
                'graindur': self.graindur,
                'graindev': self.graindev,
                'pitch': self.pitch,
                'rnddens': self.rnddens,
                'rnddur': self.rnddur,
                'rndpos': self.rndpos,
                'rndpit': self.rndpit,
                'rndpan': self.rndpan,
                'trans': self.getTrans(),
                'dnsCheck': self.tx_ydns_ch.GetValue(),
                'dnsYmin': float(self.tx_dns_ymin.GetValue()),
                'dnsYmax': float(self.tx_dns_ymax.GetValue()),
                'pitCheck': self.tx_ypit_ch.GetValue(),
                'pitYmin': float(self.tx_pit_ymin.GetValue()),
                'pitYmax': float(self.tx_pit_ymax.GetValue()),
                'lenCheck': self.tx_ylen_ch.GetValue(),
                'lenYmin': float(self.tx_len_ymin.GetValue()),
                'lenYmax': float(self.tx_len_ymax.GetValue()),
                'devCheck': self.tx_ydev_ch.GetValue(),
                'devYmin': float(self.tx_dev_ymin.GetValue()),
                'devYmax': float(self.tx_dev_ymax.GetValue()),
                'ampCheck': self.tx_yamp_ch.GetValue(),
                'ampYmin': float(self.tx_amp_ymin.GetValue()),
                'ampYmax': float(self.tx_amp_ymax.GetValue()),
                'trsCheck': self.tx_ytrs_ch.GetValue(),
                'trsYmin': float(self.tx_trs_ymin.GetValue()),
                'trsYmax': float(self.tx_trs_ymax.GetValue()),
                'durCheck': self.tx_ydur_ch.GetValue(),
                'durYmin': float(self.tx_dur_ymin.GetValue()),
                'durYmax': float(self.tx_dur_ymax.GetValue()),
                'posCheck': self.tx_ypos_ch.GetValue(),
                'posYmin': float(self.tx_pos_ymin.GetValue()),
                'posYmax': float(self.tx_pos_ymax.GetValue()),
                'panCheck': self.tx_ypan_ch.GetValue(),
                'panYmin': float(self.tx_pan_ymin.GetValue()),
                'panYmax': float(self.tx_pan_ymax.GetValue())}

    def load(self, dict):
        self.handleDensity(dict['density'], fromSlider=False)
        self.handlePitch(dict['pitch'], fromSlider=False)
        self.handleGrainDur(dict['graindur'], fromSlider=False)
        self.handleGrainDev(dict['graindev'], fromSlider=False)
        self.handleRandDens(dict['rnddens'], fromSlider=False)
        self.handleRandDur(dict['rnddur'], fromSlider=False)
        self.handleRandPos(dict['rndpos'], fromSlider=False)
        self.handleRandPit(dict['rndpit'], fromSlider=False)
        self.handleRandPan(dict['rndpan'], fromSlider=False)
        self.setTrans(dict['trans'])
                     
        checkboxes = {'dnsCheck': self.tx_ydns_ch, 'pitCheck': self.tx_ypit_ch, 
                      'lenCheck': self.tx_ylen_ch, 'devCheck': self.tx_ydev_ch,
                      'ampCheck': self.tx_yamp_ch, 'trsCheck': self.tx_ytrs_ch, 
                      'durCheck': self.tx_ydur_ch, 'posCheck': self.tx_ypos_ch, 
                      'panCheck': self.tx_ypan_ch}
        for key, cb in checkboxes.items():
            cb.SetValue(dict[key])
            event = wx.PyCommandEvent(wx.EVT_CHECKBOX.typeId, cb.GetId())
            event.SetEventObject(cb)
            event.SetInt(dict[key])
            wx.PostEvent(cb.GetEventHandler(), event)

        textboxes = {'dnsYmin': self.tx_dns_ymin, 'dnsYmax': self.tx_dns_ymax,
                     'pitYmin': self.tx_pit_ymin, 'pitYmax': self.tx_pit_ymax,
                     'lenYmin': self.tx_len_ymin, 'lenYmax': self.tx_len_ymax,
                     'devYmin': self.tx_dev_ymin, 'devYmax': self.tx_dev_ymax,
                     'ampYmin': self.tx_amp_ymin, 'ampYmax': self.tx_amp_ymax,
                     'trsYmin': self.tx_dur_ymin, 'trsYmax': self.tx_dur_ymax,
                     'durYmin': self.tx_dur_ymin, 'durYmax': self.tx_dur_ymax,
                     'posYmin': self.tx_pos_ymin, 'posYmax': self.tx_pos_ymax,
                     'panYmin': self.tx_pan_ymin, 'panYmax': self.tx_pan_ymax}
        for key, tb in textboxes.items():
            tb.SetValue(str(dict[key]))
            event = wx.PyCommandEvent(wx.EVT_TEXT_ENTER.typeId, tb.GetId())
            event.SetEventObject(tb)
            event.SetString(str(dict[key]))
            wx.PostEvent(tb.GetEventHandler(), event)
