# encoding: utf-8
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
from constants import BACKGROUND_COLOUR, ensureNFD, toSysEncoding
from Resources.audio import checkForMidiDrivers

class MidiSettings(wx.Frame):
    def __init__(self, parent, surface, sg_audio, miDriver):
        wx.Frame.__init__(self, parent, -1, "Midi Settings")
        menuBar = wx.MenuBar()
        self.menu = wx.Menu()
        self.menu.Append(200, 'Close\tCtrl+W', "")
        self.menu.AppendSeparator()
        self.menu.Append(201, "Run\tCtrl+R", "", wx.ITEM_CHECK)
        menuBar.Append(self.menu, "&File")
        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_CLOSE, self.handleClose)
        self.Bind(wx.EVT_MENU, self.handleClose, id=200)

        self.parent = parent
        self.surface = surface
        self.sg_audio = sg_audio

        self.panel = wx.Panel(self, -1)
        self.panel.SetBackgroundColour(BACKGROUND_COLOUR)

        mainBox = wx.BoxSizer(wx.VERTICAL)
        box = wx.BoxSizer(wx.VERTICAL)

        box.Add(wx.StaticText(self.panel, id=-1, label="Midi Interface"), 0, wx.CENTER|wx.ALL, 2)
        self.interfaceList, self.interfaceIndexes, selected = checkForMidiDrivers()
        self.interfaceList = [ensureNFD(driver) for driver in self.interfaceList]
        if self.interfaceList != []:
            self.interfaceList.append("All")
            self.interfaceIndexes.append(99)
            if miDriver == None:
                self.selectedInterface = selected
            else:
                if miDriver in self.interfaceList:
                    self.selectedInterface = self.interfaceIndexes[self.interfaceList.index(miDriver)]
                else:
                    self.selectedInterface = selected
            self.popupInterface = wx.Choice(self.panel, id=-1, size=(200, -1), choices=self.interfaceList)
            if self.selectedInterface:
                self.popupInterface.SetSelection(self.interfaceIndexes.index(self.selectedInterface))
            self.popupInterface.Bind(wx.EVT_CHOICE, self.changeInterface)
            self.parent.controls.midiInterface = self.selectedInterface
        else:
            self.selectedInterface = None
            self.popupInterface = wx.Choice(self.panel, id=-1, size=(200, -1), choices=["No interface"])
            self.popupInterface.SetSelection(0)
        box.Add(self.popupInterface, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)

        box.Add(wx.StaticText(self.panel, id=-1, label="Add / Remove Method"), 0, wx.CENTER|wx.ALL, 2)
        self.popupMethod = wx.Choice(self.panel, id=-1, size=(200, -1), choices=["Noteon / Noteoff", "Noteon / Noteon"])
        self.popupMethod.SetSelection(0)
        self.popupMethod.Bind(wx.EVT_CHOICE, self.handleMethod)
        box.Add(self.popupMethod, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)

        box.Add(wx.StaticLine(self.panel, size=(200, 1)), 0, wx.ALL, 5)

        box.Add(wx.StaticText(self.panel, id=-1, label="Pitch Mapping"), 0, wx.CENTER|wx.ALL, 5)

        self.xTranspo = wx.CheckBox(self.panel, label="Transposition")
        self.xTranspo.SetValue(True)
        self.xTranspo.Bind(wx.EVT_CHECKBOX, self.handleTranspo)
        box.Add(self.xTranspo, 0, wx.ALL, 5)

        self.xPosition = wx.CheckBox(self.panel, label="X Axis Position")
        self.xPosition.Bind(wx.EVT_CHECKBOX, self.handlePosition)
        box.Add(self.xPosition, 0, wx.ALL, 5)

        box.Add(wx.StaticText(self.panel, id=-1, label="X Position Octave Spread"), 0, wx.CENTER|wx.ALL, 2)
        self.octaveSpread = ControlSlider(self.panel, 1, 4, 2, size=(200, 16), outFunction=self.handleSpread)
        self.enableOctaveSpread(self.xPosition.GetValue())
        box.Add(self.octaveSpread, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)

        mainBox.Add(box, 0, wx.ALL, 10)
        self.panel.SetSizerAndFit(mainBox)

        size = (230, 300)
        self.SetMinSize(size)
        self.SetMaxSize(size)
        self.SetPosition((self.parent.GetPosition()[0] + self.parent.GetSize()[0], self.parent.GetPosition()[1]))
        self.Show(False)
        wx.CallAfter(self.SetSize, size)

    def show(self):
        self.Show()

    def handleClose(self, event):
        self.Show(False)

    def getInterface(self):
        if self.selectedInterface == None:
            return None
        else:
            return self.interfaceList[self.interfaceIndexes.index(self.selectedInterface)]

    def changeInterface(self, evt):
        status, path = self.parent.checkForMixedSound()
        if not status:
            for i, driver in enumerate(self.interfaceList):
                if driver == self.interfaceList[self.interfaceIndexes.index(self.selectedInterface)]:
                    self.popupInterface.SetSelection(i)
            return
        if "Mixed sound" in self.parent.controls.sndPath:
            self.parent.controls.sndPath = path
            if path == "":
                self.parent.panel.sndBitmap = None
                self.parent.panel.needBitmap = True
                wx.CallAfter(self.parent.panel.Refresh)
        selectedInterface = self.popupInterface.GetStringSelection()
        self.selectedInterface = self.interfaceIndexes[self.interfaceList.index(selectedInterface)]
        self.parent.controls.midiInterface = self.selectedInterface
        self.parent.controls.shutdownServer()
        self.parent.controls.bootServer()

    # TODO: replace handle, set and get method with events
    def handleMethod(self, evt):
        self.sg_audio.setMidiMethod(self.popupMethod.GetSelection())

    def setMethod(self, met):
        self.popupMethod.SetSelection(met)
        self.sg_audio.setMidiMethod(met)

    def getMethod(self):
        return self.popupMethod.GetSelection()

    def handleTranspo(self, evt):
        self.surface.setMidiTranspose(self.xTranspo.GetValue())

    def setTranspo(self, value):
        self.xTranspo.SetValue(value)
        self.surface.setMidiTranspose(value)

    def getTranspo(self):
        return self.xTranspo.GetValue()

    def handlePosition(self, evt):
        state = self.xPosition.GetValue()
        self.surface.setMidiXposition(state)
        self.enableOctaveSpread(state)

    def setPosition(self, value):
        self.xPosition.SetValue(value)
        self.surface.setMidiXposition(value)
        self.enableOctaveSpread(value)

    def getPosition(self):
        return self.xPosition.GetValue()

    def enableOctaveSpread(self, state):
        if state:
            self.octaveSpread.Enable()
        else:
            self.octaveSpread.Disable()

    def handleSpread(self, value):
        self.surface.setMidiOctaveSpread(value)

    def setSpread(self, value):
        self.octaveSpread.SetValue(value)

    def getSpread(self):
        return self.octaveSpread.GetValue()

    def save(self):
        return {"method": self.getMethod(),
                "transpo": self.getTranspo(),
                "position": self.getPosition(),
                "spread": self.getSpread()}

    def load(self, dict):
        if dict != None:
            self.setMethod(dict["method"])
            self.setTranspo(dict["transpo"])
            self.setPosition(dict["position"])
            self.setSpread(dict["spread"])
