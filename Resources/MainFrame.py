# encoding: utf-8
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
import os, wx, time
from Resources.constants import *
from Resources.audio import *
from Resources.Modules import *
from pyolib._wxwidgets import Grapher, BACKGROUND_COLOUR
from Resources.Trajectory import Trajectory
from Resources.MidiSettings import MidiSettings
from Resources.CommandFrame import CommandFrame
from Resources.DrawingSurface import DrawingSurface
from Resources.ControlPanel import ControlPanel

if sys.version_info[0] < 3:
    import xmlrpclib
else:
    import xmlrpc.client as xmlrpclib

if "phoenix" in wx.version():
    from wx.adv import AboutDialogInfo, AboutBox
else:
    from wx import AboutDialogInfo, AboutBox

class EnvelopeFrame(wx.Frame):
    def __init__(self, parent, size=(600, 300)):
        wx.Frame.__init__(self, parent, -1, "Envelope Shape", size=size)
        self.parent = parent
        self.env = None
        menuBar = wx.MenuBar()
        self.menu = wx.Menu()
        self.menu.Append(200, 'Close\tCtrl+W', "")
        menuBar.Append(self.menu, "&File")
        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_CLOSE, self.handleClose)
        self.Bind(wx.EVT_MENU, self.handleClose, id=200)

        self.graph = Grapher(self, init=[(0.0,0),(0.3,1),(0.7,1),(1.0,0)], mode=1)

        self.Show(False)

    def setEnv(self, env):
        self.env = env
        self.env.replace(self.graph.getValues())
        self.graph.outFunction = self.env.replace

    def handleClose(self, event):
        self.Hide()

    def save(self):
        return {'envelope': self.graph.getPoints()}

    def load(self, dict):
        self.graph.setInitPoints(dict.get('envelope', [(0.0,0),(0.3,1),(0.7,1),(1.0,0)]))
        if self.env != None:
            self.env.replace(self.graph.getValues())

class MainFrame(wx.Frame):
    def __init__(self, parent, id, pos, size, screen_size):
        wx.Frame.__init__(self, parent, id, "", pos, size)
        self.SetMinSize((600,300))
        self.screen_size = screen_size
        self.is_unsaved = False
        self.currentFile = None
        self.currentPath = None
        self.temps = []
        self.draw = True
        self.lowpass = True
        self.fillPoints = True
        self.editionLevels = [2, 4, 8, 12, 16, 24, 32, 50]
        self.editionLevel = 2
        self.audioDriver = None
        self.recall = self.undos = 0
        self.sample_precision = SAMPLE_PRECISION

        self.status = wx.StatusBar(self, -1)
        self.SetStatusBar(self.status)

        self.menuBar = wx.MenuBar()
        self.menu = wx.Menu()
        self.menu.Append(11, "New...\tCtrl+N")
        self.Bind(wx.EVT_MENU, self.handleNew, id=11)
        self.menu.Append(1, "Open...\tCtrl+O")
        self.Bind(wx.EVT_MENU, self.handleOpen, id=1)
        self.menu.Append(2, "Open Soundfile...\tShift+Ctrl+O")
        self.Bind(wx.EVT_MENU, self.handleLoad, id=2)
        self.menu.Append(12, "Insert Soundfile...\tShift+Ctrl+I")
        self.Bind(wx.EVT_MENU, self.handleInsert, id=12)
        self.menu.Append(3, "Save\tCtrl+S")
        self.Bind(wx.EVT_MENU, self.handleSave, id=3)
        self.menu.Append(4, "Save as...\tShift+Ctrl+S")
        self.Bind(wx.EVT_MENU, self.handleSaveAs, id=4)
        self.menu.AppendSeparator()
        self.menu.Append(6, "Open Granulator Controls\tCtrl+P")
        self.Bind(wx.EVT_MENU, self.openFxWindow, id=6)
        self.menu.Append(5, "Open Envelope Window\tCtrl+E")
        self.Bind(wx.EVT_MENU, self.openEnvelopeWindow, id=5)
        self.menu.AppendSeparator()
        self.menu.Append(7, "Run\tCtrl+R", "", wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.onRun, id=7)
        self.menu.AppendSeparator()
        quit_item = self.menu.Append(wx.ID_EXIT, "Quit\tCtrl+Q")
        self.Bind(wx.EVT_MENU, self.OnClose, id=wx.ID_EXIT)
        self.menuBar.Append(self.menu, "&File")

        self.menu1 = wx.Menu()
        self.menu1.Append(110, "Undo\tCtrl+Z", "")
        self.menu1.Enable(110, False)
        self.Bind(wx.EVT_MENU, self.handleUndo, id=110)
        self.menu1.Append(111, "Redo\tShift+Ctrl+Z", "")
        self.menu1.Enable(111, False)
        self.Bind(wx.EVT_MENU, self.handleUndo, id=111)
        self.menu1.InsertSeparator(2)
        self.menu1.Append(100, "Draw Waveform", "", wx.ITEM_CHECK)
        self.menu1.Check(100, True)
        self.Bind(wx.EVT_MENU, self.handleDrawWave, id=100)
        self.menu1.Append(101, "Activate Lowpass filter", "", wx.ITEM_CHECK)
        self.menu1.Check(101, True)
        self.Bind(wx.EVT_MENU, self.handleActivateLp, id=101)
        self.menu1.Append(102, "Fill points", "", wx.ITEM_CHECK)
        self.menu1.Check(102, True)
        self.Bind(wx.EVT_MENU, self.handleActivateFill, id=102)
        self.submenu1 = wx.Menu()
        for i, level in enumerate(self.editionLevels):
            menuId = 1000 + i
            self.submenu1.Append(menuId, str(level), "", wx.ITEM_RADIO)
            self.Bind(wx.EVT_MENU, self.handlesEditionLevels, id=menuId)
        self.menu1.AppendSubMenu(self.submenu1, "Edition levels")
        self.menu1.InsertSeparator(7)
        self.menu1.Append(103, "Reinit counters\tCtrl+T", "")
        self.Bind(wx.EVT_MENU, self.handleReinit, id=103)
        self.menuBar.Append(self.menu1, "&Drawing")

        self.menu2 = wx.Menu()
        self.menuBar.Append(self.menu2, "&Audio Drivers")

        self.menu3 = wx.Menu()
        self.menu3.Append(2004, "Memorize Trajectory\tShift+Ctrl+M", "")
        self.Bind(wx.EVT_MENU, self.handleMemorize, id=2004)
        self.menu3.Append(2005, "Midi Settings...\tShift+Alt+Ctrl+M", "")
        self.Bind(wx.EVT_MENU, self.showMidiSettings, id=2005)
        self.menuBar.Append(self.menu3, "&Midi")

        self.menu4 = wx.Menu()
        self.menu4.Append(400, "Add Reverb ball\tCtrl+1", "")
        self.menu4.Append(401, "Add Delay ball\tCtrl+2", "")
        self.menu4.Append(402, "Add Disto ball\tCtrl+3", "")
        self.menu4.Append(403, "Add Waveguide ball\tCtrl+4", "")
        self.menu4.Append(404, "Add Complex Resonator ball\tCtrl+5", "")
        self.menu4.Append(405, "Add Degrade ball\tCtrl+6", "")
        self.menu4.Append(406, "Add Harmonizer ball\tCtrl+7", "")
        self.menu4.Append(407, "Add Clipper ball\tCtrl+8", "")
        self.menu4.Append(408, "Add Flanger ball\tCtrl+9", "")
        self.menu4.Append(409, "Add Detuned Resonator ball\tCtrl+0", "")
        for i in range(10):
            self.Bind(wx.EVT_MENU, self.addFxBall, id=400+i)
        self.menuBar.Append(self.menu4, "&FxBall")

        menu5 = wx.Menu()
        helpItem = menu5.Append(wx.ID_ABOUT, '&About %s %s' % (NAME, SG_VERSION))
        self.Bind(wx.EVT_MENU, self.showAbout, helpItem)
        commands = menu5.Append(501, "Open SoundGrain Documentation\tCtrl+H")
        self.Bind(wx.EVT_MENU, self.openCommandsPage, commands)
        self.menuBar.Append(menu5, '&Help')

        self.SetMenuBar(self.menuBar)

        preffile = os.path.join(os.path.expanduser("~"), ".soundgrain-init")
        if os.path.isfile(preffile):
            with open(preffile, "r") as f:
                lines = f.readlines()
                auDriver = ensureNFD(lines[0].split("=")[1].replace("\n", ""))
                miDriver = ensureNFD(lines[1].split("=")[1].replace("\n", ""))
        else:
            auDriver = None
            miDriver = None

        mainBox = wx.BoxSizer(wx.HORIZONTAL)
        self.panel = DrawingSurface(self)
        self.controls = ControlPanel(self, self.panel)
        mainBox.Add(self.panel, 20, wx.EXPAND, 5)
        mainBox.Add(self.controls, 0, wx.EXPAND, 5)
        self.SetSizer(mainBox)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.SetTitle('%s %s - ' % (NAME, SG_VERSION))
        self.envelopeFrame = EnvelopeFrame(self)
        self.sg_audio = SG_Audio(self.panel.clock, self.panel.Refresh, 
                                 self.controls, self.panel.addTrajFromMemory,
                                 self.panel.deleteMemorizedTraj, self.envelopeFrame)
        self.granulatorControls = GranulatorFrame(self, self.sg_audio)
        self.midiSettings = MidiSettings(self, self.panel, self.sg_audio, miDriver)
        self.createInitTempFile()

        self.check(auDriver)

    def onRun(self, event):
        self.controls.handleAudio(event)

    def check(self, pref=None):
        self.status.SetStatusText('Scanning audio drivers...')
        self.driversList, self.driverIndexes, selected = checkForDrivers()
        self.driversList = [ensureNFD(driver) for driver in self.driversList]
        if pref == None:
            self.audioDriver = selected
        else:
            if pref in self.driversList:
                self.audioDriver = self.driverIndexes[self.driversList.index(pref)]
            else:
                self.audioDriver = selected
        for i, driver in enumerate(self.driversList):
            menuId = 200 + i
            self.menu2.Append(menuId, driver, "", wx.ITEM_RADIO)
            self.Bind(wx.EVT_MENU, self.handleDriver, id=menuId)
            if driver == self.driversList[self.driverIndexes.index(self.audioDriver)]:
                self.menu2.Check(menuId, True)
        self.menu2.AppendSeparator()
        precision_label = self.menu2.Append(-1, "Sample Precision (Require restarting the app)", "")
        precision_label.Enable(False)
        menuId += 1
        item32 = self.menu2.Append(menuId, "32-bit", "", wx.ITEM_CHECK)
        if SAMPLE_PRECISION == "32-bit":
            self.menu2.Check(menuId, True)
            self.menu2.Enable(menuId, False)
        self.Bind(wx.EVT_MENU, self.handlePrecision, id=menuId)
        menuId += 1
        item64 = self.menu2.Append(menuId, "64-bit", "", wx.ITEM_CHECK)
        if SAMPLE_PRECISION == "64-bit":
            self.menu2.Check(menuId, True)
            self.menu2.Enable(menuId, False)
        self.Bind(wx.EVT_MENU, self.handlePrecision, id=menuId)
        self.status.SetStatusText('Audio drivers loaded')
        self.controls.bootServer()

    def showMidiSettings(self, evt):
        self.midiSettings.show()

    def enableDrivers(self, state):
        for i in range(len(self.driversList)):
            self.menu2.FindItemById(200+i).Enable(state)

    def handleReinit(self, evt):
        for t in self.panel.getAllTrajectories():
            t.initCounter()

    def addFxBall(self, evt):
        self.panel.addFxBall(evt.GetId() - 400)

    def handleMemorize(self, evt):
        self.panel.Memorize()

    def handleDrawWave(self, evt):
        self.draw = self.menu1.IsChecked(100)
        self.drawing()

    def setDraw(self, state):
        self.menu1.Check(100, state)
        self.draw = state

    def drawing(self):
        if not self.draw:
            self.panel.sndBitmap = None
            self.panel.needBitmap = True
            self.panel.Refresh()
        else:
            if self.controls.sndPath != "":
                if self.controls.sndPath in self.panel.bitmapDict:
                    self.panel.list = self.panel.bitmapDict[self.controls.sndPath]
                    self.panel.create_bitmap()
                else:
                    self.panel.analyse(self.controls.sndPath)

    def handleActivateLp(self, evt):
        self.lowpass = self.menu1.IsChecked(101)
        self.checkLowpass()

    def setLowpass(self, state):
        self.menu1.Check(101, state)
        self.lowpass = state
        self.checkLowpass()

    def checkLowpass(self):
        for t in self.panel.getAllTrajectories():
            t.activateLp(self.lowpass)
        if self.lowpass:
            self.controls.drawing.sl_cutoff.Enable()
            self.controls.drawing.sl_q.Enable()
        else:
            self.controls.drawing.sl_cutoff.Disable()
            self.controls.drawing.sl_q.Disable()

    def handleActivateFill(self, evt):
        self.fillPoints = self.menu1.IsChecked(102)

    def setFillPoints(self, state):
        self.menu1.Check(102, state)
        self.fillPoints = state

    def handlesEditionLevels(self, evt):
        menuId = evt.GetId()
        self.editionLevel = self.editionLevels[menuId - 1000]
        self.pushEditionLevel()

    def setEditionLevel(self, level):
        self.submenu1.Check(self.editionLevels.index(level)+1000, True)
        self.editionLevel = level
        self.pushEditionLevel()

    def pushEditionLevel(self):
        for t in self.panel.getAllTrajectories():
            t.setEditionLevel(self.editionLevel)

    def handleDriver(self, evt):
        status, path = self.checkForMixedSound()
        if not status:
            for i, driver in enumerate(self.driversList):
                menuId = 200 + i
                if driver == self.driversList[self.driverIndexes.index(self.audioDriver)]:
                    self.menu2.Check(menuId, True)
            return
        if "Mixed sound" in self.controls.sndPath:
            self.controls.sndPath = path
            if path == "":
                self.panel.sndBitmap = None
                self.panel.needBitmap = True
                wx.CallAfter(self.panel.Refresh)
        menuId = evt.GetId()
        self.audioDriver = self.driverIndexes[menuId - 200]
        self.controls.shutdownServer()
        self.controls.bootServer()

    def handlePrecision(self, evt):
        menuId = evt.GetId()
        item = self.menu2.FindItemById(menuId)
        label = item.GetItemLabel()
        self.sample_precision = label
        if label == "32-bit":
            self.menu2.Check(menuId, True)
            self.menu2.Enable(menuId, False)
            self.menu2.Check(menuId+1, False)
            self.menu2.Enable(menuId+1, True)
        elif label == "64-bit":
            self.menu2.Check(menuId, True)
            self.menu2.Enable(menuId, False)
            self.menu2.Check(menuId-1, False)
            self.menu2.Enable(menuId-1, True)

    def openFxWindow(self, evt):
        if self.granulatorControls.IsShown():
            self.granulatorControls.Hide()
        else:
            self.granulatorControls.SetTitle('Granulator controls')
            self.granulatorControls.Show()

    def openEnvelopeWindow(self, evt):
        if self.envelopeFrame.IsShown():
            self.envelopeFrame.Hide()
        else:
            self.envelopeFrame.Show()

    def handleUndo(self, evt):
        self.recallTempFile(evt.GetId())

    def handleNew(self, evt):
        cancel = False
        if self.is_unsaved or newpath:
            if self.currentFile == None:
                curfile = "Granulator.sg"
            else:
                curfile = self.currentFile
            dlg = wx.MessageDialog(self, 
                    "Do you want to save the changes you made in the document %s ?" % curfile,
                    'File Unsaved...', wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION)
            ret = dlg.ShowModal()
            if ret == wx.ID_YES:
                self.handleSave(None)
            elif ret == wx.ID_CANCEL:
                cancel = True
            dlg.Destroy()
        if cancel:
            return
        self.panel.sndBitmap = None
        self.controls.sndPath = ""
        self.loadFile(os.path.join(RESOURCES_PATH, 'new_soundgrain_file.sg'))

    def handleOpen(self, evt):
        dlg = wx.FileDialog(self, message="Open SoundGrain file...",
                            defaultDir=os.path.expanduser("~"),
                            defaultFile="",
                            wildcard="SoundGrain file (*.sg)|*.sg",
                            style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.loadFile(ensureNFD(path))
        dlg.Destroy()

    def handleLoad(self, evt):
        self.controls.handleLoad()

    def handleInsert(self, evt):
        self.controls.handleInsert()

    def handleSave(self, evt):
        if self.currentFile:
            self.saveFile(self.currentFile)
        else:
            self.handleSaveAs(None)

    def handleSaveAs(self, evt):
        dlg = wx.FileDialog(self, message="Save file as ...",
                            defaultDir=os.path.expanduser("~"),
                            defaultFile="Granulator.sg",
                            style=wx.FD_SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if os.path.isfile(path):
                dlg2 = wx.MessageDialog(self,
                      '"%s" already exists. Do you want to replace it?' % os.path.split(path)[1],
                      'Warning!', wx.OK | wx.ICON_INFORMATION | wx.CANCEL)
                if dlg2.ShowModal() == wx.ID_OK:
                    dlg2.Destroy()
                    self.saveFile(path)
                    dlg.Destroy()
                else:
                    dlg2.Destroy()
                    dlg.Destroy()
                    self.handleSaveAs(None)
            else:
                self.saveFile(path)
                dlg.Destroy()

    def getState(self):
        saveDict = {}
        ### Main Frame ###
        saveDict['version'] = SG_VERSION
        saveDict['platform'] = PLATFORM
        saveDict['MainFrame'] = {}
        saveDict['MainFrame']['draw'] = self.draw
        saveDict['MainFrame']['lowpass'] = self.lowpass
        saveDict['MainFrame']['fillPoints'] = self.fillPoints
        saveDict['MainFrame']['editionLevel'] = self.editionLevel
        saveDict['MainFrame']['size'] = tuple(self.GetSize())
        ### Surface Panel ###
        saveDict["SurfaceSize"] = tuple(self.panel.GetSize())
        ### Controls Frame ###
        saveDict['ControlFrame'] = self.granulatorControls.save()
        ### Midi Frame ###
        saveDict['MidiSettings'] = self.midiSettings.save()
        ### Control Panel ###
        saveDict['ControlPanel'] = {}
        saveDict['ControlPanel']['type'] = self.controls.getType()
        saveDict['ControlPanel']['closed'] = self.controls.getClosed()
        saveDict['ControlPanel']['cutoff'] = self.controls.getCutoff()
        saveDict['ControlPanel']['q'] = self.controls.getQ()
        saveDict['ControlPanel']['period'] = self.controls.getPeriod()
        saveDict['ControlPanel']['scaling'] = self.controls.getScaling()
        saveDict['ControlPanel']['globalamp'] = self.controls.getAmp()
        saveDict['ControlPanel']['nchnls'] = self.controls.getNchnls()
        saveDict['ControlPanel']['sr'] = self.controls.getSamplingRate()
        saveDict['ControlPanel']['fileformat'] = self.controls.getFileFormat()
        saveDict['ControlPanel']['sampletype'] = self.controls.getSampleType()
        saveDict['ControlPanel']['sound'] = self.controls.sndPath
        saveDict['ControlPanel']['recfolder'] = self.controls.tx_rec_folder.GetValue()
        saveDict['ControlPanel']['filename'] = self.controls.tx_output.GetValue()
        ### Trajectories ###
        saveDict['Trajectories'] = {}
        for i, t in enumerate(self.panel.getAllTrajectories()):
            saveDict['Trajectories'][str(i)] = t.getAttributes()
        saveDict['MemorizedTrajectory'] = self.panel.memorizedTrajectory.getAttributes()
        ### Grain Envelope ###
        saveDict['Envelope'] = self.envelopeFrame.save()
        ### Fx Balls ###
        saveDict['fxballs'] = {}
        for key, value in self.panel.fxballs.items():
            saveDict['fxballs'][str(key)] = value.save()
        return saveDict

    def saveFile(self, path):
        if self.controls.sndPath != "":
            status, sndpath = self.checkForMixedSound()
            if not status:
                return
            if sndpath != "":
                self.controls.sndPath = sndpath
        self.currentFile = path
        self.currentPath = os.path.split(path)[0]
        saveDict = self.getState()
        msg = xmlrpclib.dumps((saveDict, ), allow_none=True)
        f = open(path, 'w')
        f.write(msg)
        f.close()
        self.SetTitle('%s %s - %s' % (NAME, SG_VERSION, os.path.split(self.currentFile)[1]))
        self.is_unsaved = False

    def setState(self, dict):
        version = dict.get('version', '3.0')
        platform = dict.get('platform', 'darwin')
        ### Surface panel ###
        surfaceSize = dict.get('SurfaceSize', None)
        if surfaceSize != None:
            self.panel.SetSize(surfaceSize)
        ### Main Frame ###
        self.setDraw(dict['MainFrame']['draw'])
        self.setLowpass(dict['MainFrame']['lowpass'])
        self.setFillPoints(dict['MainFrame']['fillPoints'])
        self.setEditionLevel(dict['MainFrame']['editionLevel'])
        size = dict['MainFrame']['size']
        if platform == 'darwin':
            if sys.platform == 'darwin':
                self.SetSize(size)
            elif sys.platform == "win32":
                self.SetSize((size[0]+10, size[1]+38))
            else:
                self.SetSize((size[0]+3, size[1]+13))
        elif platform == "win32":
            if sys.platform == 'darwin':
                self.SetSize((size[0]-10, size[1]-38))
            elif sys.platform == "win32":
                self.SetSize(size)
            else:
                self.SetSize((size[0]-7, size[1]-25))
        else:
            if sys.platform == 'darwin':
                self.SetSize((size[0]-3, size[1]-13))
            elif sys.platform == "win32":
                self.SetSize((size[0]+7, size[1]+25))
            else:
                self.SetSize(size)
        if surfaceSize != None:
            xfac = float(self.panel.GetSize()[0]) / surfaceSize[0]
            yfac = float(self.panel.GetSize()[1]) / surfaceSize[1]
        else:
            xfac, yfac = 1, 1
        ### Control Frame ###
        self.granulatorControls.load(dict['ControlFrame'])
        ### Midi Frame ###
        self.midiSettings.load(dict.get("MidiSettings", None))
        ### Control panel ###
        self.controls.setType(dict['ControlPanel']['type'])
        self.controls.setClosed(dict['ControlPanel']['closed'])
        self.controls.setCutoff(dict['ControlPanel']['cutoff'])
        self.controls.setQ(dict['ControlPanel']['q'])
        self.controls.setPeriod(dict['ControlPanel']['period'])
        self.controls.setScaling(dict['ControlPanel']['scaling'])
        self.controls.setAmp(dict['ControlPanel']['globalamp'])
        self.controls.setNchnls(dict['ControlPanel'].get('nchnls', "2"))
        self.controls.setSamplingRate(dict['ControlPanel'].get('sr', 44100))
        self.controls.setFileFormat(dict['ControlPanel'].get('fileformat', 0))
        self.controls.setSampleType(dict['ControlPanel'].get('sampletype', 0))
        self.controls.loadSound(ensureNFD(dict['ControlPanel']['sound']))
        self.controls.setRecordFolder(ensureNFD(dict['ControlPanel'].get('recfolder', '~/Desktop')))
        self.controls.setRecordFilename(ensureNFD(dict['ControlPanel'].get('filename', 'snd')))
        ### Trajectories ###
        for i, t in enumerate(self.panel.getAllTrajectories()):
            t.setAttributes(dict['Trajectories'][str(i)], xfac, yfac)
        if 'MemorizedTrajectory' in dict:
            self.panel.memorizedTrajectory.setAttributes(dict['MemorizedTrajectory'], xfac, yfac)
        ### Grain Envelope ###
        if "Envelope" in dict:
            self.envelopeFrame.load(dict["Envelope"])
        if 'fxballs' in dict:
            self.panel.restoreFxBalls(dict["fxballs"], xfac, yfac)
        self.controls.resetPlaybackSliders()

    def loadFile(self, path):
        if self.midiSettings.IsShown():
            self.midiSettings.Hide()
        self.panel.removeAllFxBalls()
        f = open(path, 'r')
        msg = f.read()
        f.close()
        result, method = xmlrpclib.loads(msg)
        dict = result[0]
        if 'new_soundgrain_file.sg' in path:
            self.currentFile = None
            self.currentPath = None
            title = '%s %s - ' % (NAME, SG_VERSION)
            self.status.SetStatusText("")
        else:
            self.currentFile = path
            self.currentPath = os.path.split(path)[0]
            title = '%s %s - %s' % (NAME, SG_VERSION, os.path.split(self.currentFile)[1])
        self.panel.trajectories = [Trajectory(self.panel, i+1) for i in range(MAX_STREAMS)]
        self.panel.memorizedTrajectory = Trajectory(self.panel, -1)
        self.panel.memorizedId = {}
        self.controls.setSelected(0)
        self.setState(dict)
        self.SetTitle(title)
        self.panel.needBitmap = True
        size = self.GetSize()
        if size[0] > self.screen_size[0]:
            x = self.screen_size[0] - 50
        else:
            x = size[0]
        if size[1] > self.screen_size[1]:
            y = self.screen_size[1] - 50
        else:
            y = size[1]
        size = (x, y)
        wx.CallAfter(self.panel.Refresh)
        wx.CallLater(100, self.SetSize, size)

    def createInitTempFile(self):
        d = {}
        for i, t in enumerate(self.panel.getAllTrajectories()):
            d[i] = str(t.getAttributes())
        self.temps.insert(0, d)

    def createTempFile(self):
        d = {}
        for i, t in enumerate(self.panel.getAllTrajectories()):
            d[i] = str(t.getAttributes())
        self.temps.insert(0, d)
        self.recall = self.undos = 0
        self.menu1.Enable(110, True)
        self.menu1.Enable(111, False)
        self.is_unsaved = True

    def recallTempFile(self, id):
        if self.temps and self.recall < len(self.temps):
            if id == 110:
                self.recall += 1
                self.undos += 1
            else:
                self.recall -= 1
                self.undos -= 1
            d = self.temps[self.recall]
            for i, t in enumerate(self.panel.getAllTrajectories()):
                t.setAttributes(eval(d[i]))
            self.panel.needBitmap = True
            self.Refresh()
        if self.recall >= len(self.temps) - 1:
            self.menu1.Enable(110, False)
        else:
            self.menu1.Enable(110, True)
        if self.undos == 0:
            self.menu1.Enable(111, False)
        else:
            self.menu1.Enable(111, True)
        self.is_unsaved = True

    def checkForMixedSound(self):
        return_status = True
        saved_path = ""
        if "Mixed sound" in self.controls.sndPath:
            dlg = wx.MessageDialog(self, "There is a mixed sound loaded in the drawing table, if you don't save it, it will be lost. Do you want to save it on disk ?",
                                   'Mixed sound no saved...', wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION)
            ret = dlg.ShowModal()
            if ret == wx.ID_YES:
                save_dialog = True
                return_status = True
            elif ret == wx.ID_NO:
                save_dialog = False
                return_status = True
            else:
                save_dialog = False
                return_status = False
            dlg.Destroy()
            if save_dialog:
                ext = EXPORT_FORMATS[self.controls.fileformat].lower()
                wildcard = AUDIO_WILDCARD
                dlg2 = wx.FileDialog(self, message="Choose a filename...", 
                                     defaultDir=os.path.expanduser("~"),
                                     defaultFile="mixedtable.%s" % ext, 
                                     wildcard=wildcard, 
                                     style=wx.FD_SAVE | wx.FD_CHANGE_DIR)
                if dlg2.ShowModal() == wx.ID_OK:
                    path = dlg2.GetPath()
                    if path != "":
                        p, ext = os.path.splitext(path)
                        if ext.upper() in EXPORT_FORMATS:
                            fileformat = EXPORT_FORMATS[ext.upper()]
                        else:
                            fileformat = self.controls.fileformat
                        sampletype = self.controls.sampletype
                        self.sg_audio.table.save(path, fileformat, sampletype)
                        saved_path = path
                dlg2.Destroy()
        return return_status, saved_path

    def OnClose(self, evt):
        newpath = False
        if self.controls.sndPath != "":
            status, path = self.checkForMixedSound()
            if "Mixed sound" in self.controls.sndPath:
                self.controls.sndPath = path
                if path != "":
                    newpath = True
        if self.is_unsaved or newpath:
            if self.currentFile == None:
                curfile = "Granulator.sg"
            else:
                curfile = self.currentFile
            dlg = wx.MessageDialog(self, "Do you want to save the changes you made in the document %s ?" % curfile,
                                   'File Unsaved...', wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION)
            ret = dlg.ShowModal()
            if ret == wx.ID_YES:
                self.handleSave(None)
            elif ret == wx.ID_CANCEL:
                return
            dlg.Destroy()
        auDriver = self.driversList[self.driverIndexes.index(self.audioDriver)]
        miDriver = self.midiSettings.getInterface()
        with open(os.path.join(os.path.expanduser("~"), ".soundgrain-init"), "w") as f:
            f.write("audioDriver=%s\n" % toSysEncoding(auDriver))
            f.write("midiDriver=%s\n" % toSysEncoding(miDriver))
            f.write("samplePrecision=%s\n" % self.sample_precision)
        if self.granulatorControls.IsShown():
            self.granulatorControls.Hide()
        self.controls.meter.OnClose(evt)
        if self.sg_audio.server.getIsStarted():
            self.sg_audio.server.stop()
            time.sleep(0.2)
        self.controls.shutdownServer()
        time.sleep(0.2)
        self.Destroy()
        sys.exit()

    def log(self, text):
        self.status.SetStatusText(text)

    def openCommandsPage(self, evt):
        win = CommandFrame(self, wx.ID_ANY, 
                           "%s %s - Documentation" % (NAME, SG_VERSION), 
                           size=(900, 650))

    def showAbout(self, evt):
        info = AboutDialogInfo()

        description = "Soundgrain is a graphical interface where " \
        "users can draw and edit trajectories to control granular sound synthesis.\n\n" \
        "Soundgrain is written with Python and " \
        "WxPython and uses pyo as its audio engine.\n\n" \

        info.SetName(NAME)
        info.SetVersion('%s' % SG_VERSION)
        info.SetDescription(description)
        info.SetCopyright(u'(C) %s Olivier Bélanger' % SG_YEAR)
        AboutBox(info)
