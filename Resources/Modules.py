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
from .constants import BACKGROUND_COLOUR, PLATFORM

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
        staticLabel = wx.StaticText(self.panel1, -1, label)
        font, psize = staticLabel.GetFont(), staticLabel.GetFont().GetPointSize()
        if PLATFORM == "win32":
            font.SetPointSize(psize-1)
        else:
            font.SetPointSize(psize-2)
        staticLabel.SetFont(font)
        box.Add(staticLabel, 0, wx.LEFT, 10)
        sliderBox = wx.BoxSizer(wx.HORIZONTAL)
        slider = ControlSlider(self.panel1, minval, maxval, val, size=(250, 16), 
                               log=log, integer=integer, outFunction=callback)
        sliderBox.Add(slider, 1, wx.LEFT | wx.RIGHT, 5)
        box.Add(sliderBox, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
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

    def handleFilterFreq(self, x, fromSlider=True):
        self.filtfreq = x
        self.sg_audio.setFilterFreq(x)
        if not fromSlider:
            self.sl_filtf.SetValue(x)

    def handleFilterQ(self, x, fromSlider=True):
        self.filtq = x
        self.sg_audio.setFilterQ(x)
        if not fromSlider:
            self.sl_filtq.SetValue(x)

    def handleFilterType(self, x, fromSlider=True):
        self.filtt = x
        self.sg_audio.setFilterType(x)
        if not fromSlider:
            self.sl_filtt.SetValue(x)

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

    def handleRandFilterFreq(self, x, fromSlider=True):
        self.rndffr = x
        self.sg_audio.setRandFilterFreq(x)
        if not fromSlider:
            self.sl_rndffr.SetValue(x)

    def handleRandFilterQ(self, x, fromSlider=True):
        self.rndfqr = x
        self.sg_audio.setRandFilterQ(x)
        if not fromSlider:
            self.sl_rndfqr.SetValue(x)

    def makeTransBox(self, box):
        staticLabel1 = wx.StaticText(self.panel1, -1, "Random Transpo per Grain (list of ratios)")
        font, psize = staticLabel1.GetFont(), staticLabel1.GetFont().GetPointSize()
        if PLATFORM == "win32":
            font.SetPointSize(psize-1)
        else:
            font.SetPointSize(psize-2)
        staticLabel1.SetFont(font)
        box.Add(staticLabel1, 0, wx.CENTER|wx.TOP, 5)
        transBox = wx.BoxSizer(wx.HORIZONTAL)
        self.tx_trans = wx.TextCtrl(self.panel1, -1, "1, ", size=(250, -1), 
                                    style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB)
        self.tx_trans.SetFont(font)
        self.tx_trans.Bind(wx.EVT_TEXT_ENTER, self.handleTrans)
        self.tx_trans.Bind(wx.EVT_CHAR, self.onCharTrans)
        transBox.Add(self.tx_trans, 1, wx.LEFT | wx.RIGHT, 5)
        box.Add(transBox, 0, wx.EXPAND | wx.ALL, 5)

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

    def makeFilterTransBox(self, box):
        staticLabel1 = wx.StaticText(self.panel1, -1, "Random Filter Freq per Grain (list of ratios)")
        font, psize = staticLabel1.GetFont(), staticLabel1.GetFont().GetPointSize()
        if PLATFORM == "win32":
            font.SetPointSize(psize-1)
        else:
            font.SetPointSize(psize-2)
        staticLabel1.SetFont(font)
        box.Add(staticLabel1, 0, wx.CENTER|wx.TOP, 5)
        transBox = wx.BoxSizer(wx.HORIZONTAL)
        self.tx_ftrans = wx.TextCtrl(self.panel1, -1, "1, ", size=(250, -1), 
                                     style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB)
        self.tx_ftrans.SetFont(font)
        self.tx_ftrans.Bind(wx.EVT_TEXT_ENTER, self.handleFilterTrans)
        self.tx_ftrans.Bind(wx.EVT_CHAR, self.onCharFilterTrans)
        transBox.Add(self.tx_ftrans, 1, wx.LEFT | wx.RIGHT, 5)
        box.Add(transBox, 0, wx.EXPAND | wx.ALL, 5)

    def getFilterTrans(self):
        return [float(value) for value in self.tx_ftrans.GetValue().split(',') if value not in [" ", ""]]

    def setFilterTrans(self, trans):
        self.tx_ftrans.SetValue(", ".join(str(t) for t in trans))
        self.handleFilterTrans(None)

    def handleFilterTrans(self, evt):
        self.sg_audio.setDiscreteFilterTrans(self.getFilterTrans())

    def onCharFilterTrans(self, evt):
        if evt.GetKeyCode() == wx.WXK_TAB:
            self.handleFilterTrans(evt)
        evt.Skip()

    ########################################################################################################
    ### Second window ###
    ########################################################################################################
    def makeYaxisBox(self, box, label, checked, minval, maxval, midval, name):
        label = wx.StaticText(self.panel2, -1, label)
        font, psize = label.GetFont(), label.GetFont().GetPointSize()
        if PLATFORM == "win32":
            font.SetPointSize(psize-1)
        else:
            font.SetPointSize(psize-2)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        label.SetFont(font)
        box.Add(label, 0, wx.LEFT|wx.TOP|wx.BOTTOM, 3)

        textBox = wx.BoxSizer(wx.HORIZONTAL)

        tx_check = wx.CheckBox(self.panel2, -1, "", name="y_%s_check" % name)
        tx_check.SetValue(checked)
        tx_check.Bind(wx.EVT_CHECKBOX, self.handleCheck)
        textBox.Add(tx_check, 0, wx.LEFT | wx.RIGHT, 10)

        minLabel = wx.StaticText(self.panel2, -1, "Min: ")
        font.SetWeight(wx.FONTWEIGHT_NORMAL)
        minLabel.SetFont(font)
        textBox.Add(minLabel, 0, wx.TOP, 4)
        tx_min = wx.TextCtrl(self.panel2, -1, minval, size=(50, -1), 
                             style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB, 
                             name="y_%s_map" % name)
        tx_min.SetFont(font)
        tx_min.Bind(wx.EVT_TEXT_ENTER, self.handleMapMin)
        tx_min.Bind(wx.EVT_CHAR, self.onCharMapMin)
        textBox.Add(tx_min, 0, wx.RIGHT, 20)

        midLabel = wx.StaticText(self.panel2, -1, "Mid: ")
        font.SetWeight(wx.FONTWEIGHT_NORMAL)
        midLabel.SetFont(font)
        textBox.Add(midLabel, 0, wx.TOP, 4)
        tx_mid = wx.TextCtrl(self.panel2, -1, midval, size=(50, -1),
                             style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB,
                             name="y_%s_map" % name)
        tx_mid.SetFont(font)
        tx_mid.Bind(wx.EVT_TEXT_ENTER, self.handleMapMid)
        tx_mid.Bind(wx.EVT_CHAR, self.onCharMapMid)
        textBox.Add(tx_mid, 0, wx.RIGHT, 20)

        maxLabel = wx.StaticText(self.panel2, -1, "Max: ")
        maxLabel.SetFont(font)
        textBox.Add(maxLabel, 0, wx.TOP, 4)
        tx_max = wx.TextCtrl(self.panel2, -1, maxval, size=(50, -1), 
                             style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB, 
                             name="y_%s_map" % name)
        tx_max.SetFont(font)
        tx_max.Bind(wx.EVT_TEXT_ENTER, self.handleMapMax)
        tx_max.Bind(wx.EVT_CHAR, self.onCharMapMax)
        textBox.Add(tx_max, 0, wx.RIGHT, 20)

        box.Add(textBox, 0, wx.LEFT | wx.RIGHT, 10)
        box.AddSpacer(4)
        return tx_check, tx_min, tx_max, tx_mid

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

    def onCharMapMid(self, evt):
        if evt.GetKeyCode() == wx.WXK_TAB:
            self.handleMapMid(evt)
        evt.Skip()

    def handleMapMid(self, evt):
        which = evt.GetEventObject().GetName()
        value = evt.GetEventObject().GetValue()
        if value == "":
            self.sg_audio.setMapMid(which, None)
        else:
            self.sg_audio.setMapMid(which, float(value))

class GranulatorFrame(Module):
    def __init__(self, parent, sg_audio):
        Module.__init__(self, parent, sg_audio)

        self.density = 32
        self.pitch = 1.
        self.graindur = 200
        self.graindev = 0
        self.filtfreq = 15000.0
        self.filtq = 0.7
        self.filtt = 0.0
        self.rnddens = 0
        self.rnddur = 0
        self.rndpos = 0
        self.rndpit = 0
        self.rndpan = 0
        self.rndffr = 0
        self.rndfqr = 0

        box = wx.BoxSizer(wx.VERTICAL)

        self.box1.AddSpacer(10)
        self.sl_dens = self.makeSliderBox(self.box1, "Density of Grains per Second", 1, 500, self.density, True, False, self.handleDensity)
        self.sl_pit = self.makeSliderBox(self.box1, "Global Transposition", 0.25, 2., self.pitch, False, False, self.handlePitch)
        self.sl_dur = self.makeSliderBox(self.box1, "Grains Duration (ms)", 5, 1000, self.graindur, True, False, self.handleGrainDur)
        self.sl_dev = self.makeSliderBox(self.box1, "Grains Start Time Deviation", 0, 1, self.graindev, False, False, self.handleGrainDev)
        self.sl_filtf = self.makeSliderBox(self.box1, "Grains Filter Frequency", 20.0, 18000.0, self.filtfreq, False, True, self.handleFilterFreq)
        self.sl_filtq = self.makeSliderBox(self.box1, "Grains Filter Q", 0.5, 20.0, self.filtq, False, True, self.handleFilterQ)
        self.sl_filtt = self.makeSliderBox(self.box1, "Grains Filter Type (lp - hp - bp - bs - ap)", 0, 4, self.filtt, True, False, self.handleFilterType)
        self.sl_rnddens = self.makeSliderBox(self.box1, "Grains Density Random", 0, 1, self.rnddens, False, False, self.handleRandDens)
        self.sl_rndpit = self.makeSliderBox(self.box1, "Grains Pitch Random", 0, 0.5, self.rndpit, False, False, self.handleRandPit)
        self.sl_rnddur = self.makeSliderBox(self.box1, "Grains Duration Random", 0, 1, self.rnddur, False, False, self.handleRandDur)
        self.sl_rndpos = self.makeSliderBox(self.box1, "Grains Position Random", 0, 1, self.rndpos, False, False, self.handleRandPos)
        self.sl_rndpan = self.makeSliderBox(self.box1, "Grains Panning Random", 0, 1, self.rndpan, False, False, self.handleRandPan)
        self.sl_rndffr = self.makeSliderBox(self.box1, "Grains Filter Freq Random", 0, 1, self.rndffr, False, False, self.handleRandFilterFreq)
        self.sl_rndfqr = self.makeSliderBox(self.box1, "Grains Filter Q Random", 0, 1, self.rndfqr, False, False, self.handleRandFilterQ)
        self.makeTransBox(self.box1)
        self.makeFilterTransBox(self.box1)
        self.panel1.SetSizer(self.box1)
        self.notebook.AddPage(self.panel1, "Granulator")

        self.tx_ydns_ch, self.tx_dns_ymin, self.tx_dns_ymax, self.tx_dns_ymid = self.makeYaxisBox(self.box2, "Density of Grains Multiplier", 0, "0.", "1.", "", "dns")
        self.tx_ypit_ch, self.tx_pit_ymin, self.tx_pit_ymax, self.tx_pit_ymid = self.makeYaxisBox(self.box2, "Transposition Multiplier", 1, "0.", "1.", "", "pit")
        self.tx_ylen_ch, self.tx_len_ymin, self.tx_len_ymax, self.tx_len_ymid = self.makeYaxisBox(self.box2, "Grains Duration Multiplier", 0, "0.", "1.", "", "len")
        self.tx_ydev_ch, self.tx_dev_ymin, self.tx_dev_ymax, self.tx_dev_ymid = self.makeYaxisBox(self.box2, "Grains Start Time Deviation", 0, "0.", "1.", "", "dev")
        self.tx_yamp_ch, self.tx_amp_ymin, self.tx_amp_ymax, self.tx_amp_ymid = self.makeYaxisBox(self.box2, "Amplitude Multiplier", 0, "0.", "1.", "", "amp")
        self.tx_yfif_ch, self.tx_fif_ymin, self.tx_fif_ymax, self.tx_fif_ymid = self.makeYaxisBox(self.box2, "Grains Filter Freq Multiplier", 0, "0.", "1.", "", "fif")
        self.tx_yfiq_ch, self.tx_fiq_ymin, self.tx_fiq_ymax, self.tx_fiq_ymid = self.makeYaxisBox(self.box2, "Grains Filter Q Multiplier", 0, "0.", "1.", "", "fiq")
        self.tx_ytrs_ch, self.tx_trs_ymin, self.tx_trs_ymax, self.tx_trs_ymid = self.makeYaxisBox(self.box2, "Grains Transposition Random", 0, "0.", "1.", "", "trs")
        self.tx_ydur_ch, self.tx_dur_ymin, self.tx_dur_ymax, self.tx_dur_ymid = self.makeYaxisBox(self.box2, "Grains Duration Random", 0, "0.", "0.5", "", "dur")
        self.tx_ypos_ch, self.tx_pos_ymin, self.tx_pos_ymax, self.tx_pos_ymid = self.makeYaxisBox(self.box2, "Grains Position Random", 0, "0.", "0.5", "", "pos")
        self.tx_yffr_ch, self.tx_ffr_ymin, self.tx_ffr_ymax, self.tx_ffr_ymid = self.makeYaxisBox(self.box2, "Grains Filter Freq Random", 0, "0.", "1.0", "", "ffr")
        self.tx_yfqr_ch, self.tx_fqr_ymin, self.tx_fqr_ymax, self.tx_fqr_ymid = self.makeYaxisBox(self.box2, "Grains Filter Q Random", 0, "0.", "1.0", "", "fqr")
        self.tx_ypan_ch, self.tx_pan_ymin, self.tx_pan_ymax, self.tx_pan_ymid = self.makeYaxisBox(self.box2, "Grains Panning", 0, "0.", "1.", "", "pan")
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
                'filtfreq': self.filtfreq,
                'filtq': self.filtq,
                'filtt': self.filtt,
                'rnddens': self.rnddens,
                'rnddur': self.rnddur,
                'rndpos': self.rndpos,
                'rndpit': self.rndpit,
                'rndpan': self.rndpan,
                'rndffr': self.rndffr,
                'rndfqr': self.rndfqr,
                'trans': self.getTrans(),
                'ftrans': self.getFilterTrans(),
                'dnsCheck': self.tx_ydns_ch.GetValue(),
                'dnsYmin': float(self.tx_dns_ymin.GetValue()),
                'dnsYmax': float(self.tx_dns_ymax.GetValue()),
                'dnsYmid': self.tx_dns_ymid.GetValue(),
                'pitCheck': self.tx_ypit_ch.GetValue(),
                'pitYmin': float(self.tx_pit_ymin.GetValue()),
                'pitYmax': float(self.tx_pit_ymax.GetValue()),
                'pitYmid': self.tx_pit_ymid.GetValue(),
                'lenCheck': self.tx_ylen_ch.GetValue(),
                'lenYmin': float(self.tx_len_ymin.GetValue()),
                'lenYmax': float(self.tx_len_ymax.GetValue()),
                'lenYmid': self.tx_len_ymid.GetValue(),
                'devCheck': self.tx_ydev_ch.GetValue(),
                'devYmin': float(self.tx_dev_ymin.GetValue()),
                'devYmax': float(self.tx_dev_ymax.GetValue()),
                'devYmid': self.tx_dev_ymid.GetValue(),
                'ampCheck': self.tx_yamp_ch.GetValue(),
                'ampYmin': float(self.tx_amp_ymin.GetValue()),
                'ampYmax': float(self.tx_amp_ymax.GetValue()),
                'ampYmid': self.tx_amp_ymid.GetValue(),
                'fifCheck': self.tx_yfif_ch.GetValue(),
                'fifYmin': float(self.tx_fif_ymin.GetValue()),
                'fifYmax': float(self.tx_fif_ymax.GetValue()),
                'fifYmid': self.tx_fif_ymid.GetValue(),
                'fiqCheck': self.tx_yfiq_ch.GetValue(),
                'fiqYmin': float(self.tx_fiq_ymin.GetValue()),
                'fiqYmax': float(self.tx_fiq_ymax.GetValue()),
                'fiqYmid': self.tx_fiq_ymid.GetValue(),
                'trsCheck': self.tx_ytrs_ch.GetValue(),
                'trsYmin': float(self.tx_trs_ymin.GetValue()),
                'trsYmax': float(self.tx_trs_ymax.GetValue()),
                'trsYmid': self.tx_trs_ymid.GetValue(),
                'durCheck': self.tx_ydur_ch.GetValue(),
                'durYmin': float(self.tx_dur_ymin.GetValue()),
                'durYmax': float(self.tx_dur_ymax.GetValue()),
                'durYmid': self.tx_dur_ymid.GetValue(),
                'posCheck': self.tx_ypos_ch.GetValue(),
                'posYmin': float(self.tx_pos_ymin.GetValue()),
                'posYmax': float(self.tx_pos_ymax.GetValue()),
                'posYmid': self.tx_pos_ymid.GetValue(),
                'ffrCheck': self.tx_yffr_ch.GetValue(),
                'ffrYmin': float(self.tx_ffr_ymin.GetValue()),
                'ffrYmax': float(self.tx_ffr_ymax.GetValue()),
                'ffrYmid': self.tx_ffr_ymid.GetValue(),
                'fqrCheck': self.tx_yfqr_ch.GetValue(),
                'fqrYmin': float(self.tx_fqr_ymin.GetValue()),
                'fqrYmax': float(self.tx_fqr_ymax.GetValue()),
                'fqrYmid': self.tx_fqr_ymid.GetValue(),
                'panCheck': self.tx_ypan_ch.GetValue(),
                'panYmin': float(self.tx_pan_ymin.GetValue()),
                'panYmax': float(self.tx_pan_ymax.GetValue()),
                'panYmid': self.tx_pan_ymid.GetValue()}

    def load(self, dict):
        self.handleDensity(dict['density'], fromSlider=False)
        self.handlePitch(dict['pitch'], fromSlider=False)
        self.handleGrainDur(dict['graindur'], fromSlider=False)
        self.handleGrainDev(dict['graindev'], fromSlider=False)
        self.handleFilterFreq(dict.get('filtfreq', 15000.0), fromSlider=False)
        self.handleFilterQ(dict.get('filtq', 0.7), fromSlider=False)
        self.handleFilterType(dict.get('filtt', 0.0), fromSlider=False)
        self.handleRandDens(dict['rnddens'], fromSlider=False)
        self.handleRandDur(dict['rnddur'], fromSlider=False)
        self.handleRandPos(dict['rndpos'], fromSlider=False)
        self.handleRandPit(dict['rndpit'], fromSlider=False)
        self.handleRandPan(dict['rndpan'], fromSlider=False)
        self.handleRandFilterFreq(dict.get('rndffr', 0.0), fromSlider=False)
        self.handleRandFilterQ(dict.get('rndfqr', 0.0), fromSlider=False)
        self.setTrans(dict['trans'])
        self.setFilterTrans(dict.get('ftrans', [1.0]))
                     
        checkboxes = {'dnsCheck': self.tx_ydns_ch, 'pitCheck': self.tx_ypit_ch, 
                      'lenCheck': self.tx_ylen_ch, 'devCheck': self.tx_ydev_ch,
                      'ampCheck': self.tx_yamp_ch, 'trsCheck': self.tx_ytrs_ch, 
                      'durCheck': self.tx_ydur_ch, 'posCheck': self.tx_ypos_ch, 
                      'panCheck': self.tx_ypan_ch, 'fifCheck': self.tx_yfif_ch,
                      'fiqCheck': self.tx_yfiq_ch, 'ffrCheck': self.tx_yffr_ch,
                      'fqrCheck': self.tx_yfqr_ch}
        for key, cb in checkboxes.items():
            value = dict.get(key, 0)
            cb.SetValue(value)
            event = wx.PyCommandEvent(wx.EVT_CHECKBOX.typeId, cb.GetId())
            event.SetEventObject(cb)
            event.SetInt(value)
            wx.PostEvent(cb.GetEventHandler(), event)

        textboxes = {'dnsYmin': self.tx_dns_ymin, 'dnsYmax': self.tx_dns_ymax, 'dnsYmid': self.tx_dns_ymid,
                     'pitYmin': self.tx_pit_ymin, 'pitYmax': self.tx_pit_ymax, 'pitYmid': self.tx_pit_ymid,
                     'lenYmin': self.tx_len_ymin, 'lenYmax': self.tx_len_ymax, 'lenYmid': self.tx_len_ymid,
                     'devYmin': self.tx_dev_ymin, 'devYmax': self.tx_dev_ymax, 'devYmid': self.tx_dev_ymid,
                     'ampYmin': self.tx_amp_ymin, 'ampYmax': self.tx_amp_ymax, 'ampYmid': self.tx_amp_ymid,
                     'fifYmin': self.tx_fif_ymin, 'fifYmax': self.tx_fif_ymax, 'fifYmid': self.tx_fif_ymid,
                     'fiqYmin': self.tx_fiq_ymin, 'fiqYmax': self.tx_fiq_ymax, 'fiqYmid': self.tx_fiq_ymid,
                     'trsYmin': self.tx_trs_ymin, 'trsYmax': self.tx_trs_ymax, 'trsYmid': self.tx_trs_ymid,
                     'durYmin': self.tx_dur_ymin, 'durYmax': self.tx_dur_ymax, 'durYmid': self.tx_dur_ymid,
                     'posYmin': self.tx_pos_ymin, 'posYmax': self.tx_pos_ymax, 'posYmid': self.tx_pos_ymid,
                     'ffrYmin': self.tx_ffr_ymin, 'ffrYmax': self.tx_ffr_ymax, 'ffrYmid': self.tx_ffr_ymid,
                     'fqrYmin': self.tx_fqr_ymin, 'fqrYmax': self.tx_fqr_ymax, 'fqrYmid': self.tx_fqr_ymid,
                     'panYmin': self.tx_pan_ymin, 'panYmax': self.tx_pan_ymax, 'panYmid': self.tx_pan_ymid}
        for key, tb in textboxes.items():
            if "min" in key:
                value = dict.get(key, 0.0)
            elif "max" in key:
                value = dict.get(key, 1.0)
            else:
                value = dict.get(key, "")
            tb.SetValue(str(value))
            event = wx.PyCommandEvent(wx.EVT_TEXT_ENTER.typeId, tb.GetId())
            event.SetEventObject(tb)
            event.SetString(str(value))
            wx.PostEvent(tb.GetEventHandler(), event)
