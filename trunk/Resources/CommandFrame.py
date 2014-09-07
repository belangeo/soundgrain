import wx
import wx.richtext as rt
from Resources.constants import *
from types import ListType

class CommandFrame(wx.Frame):
    def __init__(self, *args, **kw):
        wx.Frame.__init__(self, *args, **kw)
        self.menubar = wx.MenuBar()
        self.fileMenu = wx.Menu()
        closeItem = self.fileMenu.Append(wx.ID_ANY, 'Close...\tCtrl+W', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onClose, id=closeItem.GetId())
        self.menubar.Append(self.fileMenu, "&File")
        self.SetMenuBar(self.menubar)

        self.rtc = rt.RichTextCtrl(self, style=wx.VSCROLL|wx.HSCROLL|wx.NO_BORDER)
        self.rtc.SetEditable(False)
        self.rtc.SetBackgroundColour("#EDEDED")
        self.rtc.GetCaret().Hide()
        self.rtc.Freeze()
        self.rtc.BeginSuppressUndo()
        self.rtc.BeginParagraphSpacing(0, 20)
        wx.CallAfter(self.rtc.SetFocus)

        self.writeBigTitle("Soundgrain - List of Commands")
        self.writeBigTitle("Menus")
        self.writeTitle("File Menu")
        self.writeCommand("New...", "Start a new project.", "(Ctrl+N)")
        self.writeCommand("Open...", "Open a previously created .sg file.", "(Ctrl+O)")
        self.writeCommand("Open Soundfile...", "Import a new sound into the drawing area.", "(Shift+Ctrl+O)")
        self.writeCommand("Insert Soundfile...", "Insert a new sound (with crossfade) into the current drawing area.", "(Shift+Ctrl+I)")
        self.writeCommand("Save", "Save the current state of the project.", "(Ctrl+S)")
        self.writeCommand("Save As...", "Save the current state of the project in a new .sg file.", "(Shift+Ctrl+S)")
        self.writeCommand("Open FX Window", ["Open the granulator's parameters window.", 
                                            "This window, in the tab called 'Granulator', allows the user to change the number of grains, transposition, ", "grain size and various randoms of the granulator.", "In the second tab, called 'Y axis', one can decide on which parameters, and in what range, the Y axis of the drawing ", "area will be mapped.", "Available parameters are: Transposition, Amplitude, Grains Duration Random, Grains Position Random and Panning."], "(Ctrl+P)")
        self.writeCommand("Open Envelope Window", "Open a grapher window to modify the shape of the grain's envelope.", "(Ctrl+E)")
        self.writeCommand("Run", "Start/stop audio processing.", "(Ctrl+R)")
        self.writeTitle("Drawing Menu")
        self.writeCommand("Undo, Redo", "Unlimited undo and redo stages for the drawing area (only trajectories).", "(Ctrl+Z, Shift+Ctrl+Z)")
        self.writeCommand("Draw Waveform", "If checked, the loaded soundfile's waveform will be drawn behind the trajectories.", "")
        self.writeCommand("Activate Lowpass filter", ["If checked, all points of a new trajectory will be filtered using a lowpass filter.",
                                        "Controls of the filter are located in the Drawing section of the control panel.",
                                        "This can be used to smooth out the trajectory or to insert resonance in the curve when the Q is very high."], "")
        self.writeCommand("Fill points", ["If checked, spaces between points in a trajectory (especially when stretching the curve) will be filled with additional points.",
                                    "If unchecked, the number of points in the trajectory won't change, allowing synchronization between similar trajectories."], "")
        self.writeCommand("Edition levels", "Set the modification spread of a trajectory when edited with the mouse (higher values mean narrower transformations).", "")
        self.writeCommand("Reinit counters", "Re-sync the trajectories's counters (automatically done when audio is started).", "(Ctrl+T)")
        self.writeTitle("Audio Drivers Menu")
        self.writeCommand("Audio driver", "Choose the desired driver. The drivers list is updated only at startup.", "")
        self.writeCommand("Sample Precision", "Set the audio sample precision either 32 or 64 bits. Require restarting the application.", "")
        self.writeTitle("Midi Menu")
        self.writeCommand("Memorize Trajectory", ["Memorize the state of the selected trajectory.",
                                            "The ensuing snapshot will be the initial state for trajectories triggered by MIDI notes."], "(Shift+Ctrl+M)")
        self.writeCommand("Midi Settings...", "Open the MIDI configuration and controls window.", "")
        self.writeTitle("FxBall Menu")
        self.writeCommand("Add Reverb ball", "Create a reverb region on the drawing surface.", "(Ctrl+1)")
        self.writeCommand("Add Delay ball", "Create a recursive delay region on the drawing surface.", "(Ctrl+2)")
        self.writeCommand("Add Disto ball", "Create a distortion region on the drawing surface.", "(Ctrl+3)")
        self.writeCommand("Add Waveguide ball", "Create a resonator region on the drawing surface.", "(Ctrl+4)")
        self.writeCommand("Add Ring Modulator ball", "Create a ring modulation region on the drawing surface.", "(Ctrl+5)")
        self.writeCommand("Add Degrade ball", "Create a degradation region on the drawing surface.", "(Ctrl+6)")
        self.writeCommand("Add Harmonizer ball", "Create a harmonization region on the drawing surface.", "(Ctrl+7)")
        self.writeCommand("Add Chorus ball", "Create a Chorusing region on the drawing surface.", "(Ctrl+8)")
        self.writeCommand("Add Frequency Shift ball", "Create a frequency shifter region on the drawing surface.", "(Ctrl+9)")
        self.writeCommand("Add Detuned Resonator ball", "Create an allpass-detuned resonator region on the drawing surface.", "(Ctrl+0)")

        self.writeBigTitle("Drawing Surface")
        self.writeTitle("Mouse Bindings")
        self.writeCommand("Left-click and drag in an empty space", "Create a new trajectory.", "")
        self.writeCommand("Left-click and drag on red rectangle", "Move the trajectory.", "")
        self.writeCommand("Left-click and drag on red rectangle while holding Shift key", "Move all trajectories.", "")
        self.writeCommand("Right-click on red rectangle", "Delete the trajectory.", "")
        self.writeCommand("Alt+click (or double-click) on red rectangle", "Duplicate the trajectory.", "")
        self.writeCommand("Left-click on blue diamond", "Scale the size of a circle or oscil trajectory.", "")
        self.writeCommand("Left-click and drag on a trajectory line", 'Modify the shape of the trajectory (see "Edition levels").', "")
        self.writeCommand("Left-click on the middle part of an FxBall", "Move the ball.", "")
        self.writeCommand("Left-click on the border part of an FxBall", "Resize the ball.", "")
        self.writeCommand("Right-click on the middle part of an FxBall", "Open the effect's parameters window.", "")
        self.writeCommand("Alt+click (or double-click) on an FxBall", "Delete the ball.", "")
        self.writeCommand("Shift+click on the middle part of an FxBall, up and down motion", "Change the effects's fadein/fadeout ramp time.", "")

        self.writeTitle("Keyboard Bindings")
        self.rtc.WriteText("\nWhen the focus is on the drawing surface:\n")
        self.writeCommand("Delete key", "Delete the selected trajectory.", "")
        self.writeCommand("Arrow keys", "Move all trajectories.", "")
        self.writeCommand("Shift + arrow keys", "Move the selected trajectory.", "")
        self.writeCommand("1 to 8 (not on numeric keypad)", "Freeze/unfreeze the selected trajectory.", "")
        self.writeCommand("0 (not on numeric keypad)", "Freeze/unfreeze all trajectories.", "")

        self.closeRTC()
        self.CenterOnParent()
        self.Show(True)

    def closeRTC(self):
        self.rtc.EndParagraphSpacing()
        self.rtc.EndSuppressUndo()
        self.rtc.Thaw()

    def writeBigTitle(self, text):
        self.rtc.BeginAlignment(wx.TEXT_ALIGNMENT_CENTER)
        self.rtc.BeginBold()
        if PLATFORM in ["win32", "linux2"]:
            self.rtc.BeginFontSize(12)
        else:
            self.rtc.BeginFontSize(16)
        self.rtc.Newline()
        self.rtc.Newline()
        self.rtc.WriteText(text)
        self.rtc.Newline()
        self.rtc.EndFontSize()
        self.rtc.EndBold()
        self.rtc.EndAlignment()

    def writeTitle(self, text):
        self.rtc.BeginBold()
        self.rtc.BeginUnderline()
        if PLATFORM in ["win32", "linux2"]:
            self.rtc.BeginFontSize(10)
        else:
            self.rtc.BeginFontSize(14)
        self.rtc.Newline()
        self.rtc.WriteText(text)
        self.rtc.Newline()
        self.rtc.EndFontSize()
        self.rtc.EndUnderline()
        self.rtc.EndBold()

    def writeCommand(self, command, text, shortcut=""):
        if PLATFORM in ["win32", "linux2"]:
            self.rtc.BeginFontSize(8)
        else:
            self.rtc.BeginFontSize(12)
            shortcut = shortcut.replace("Ctrl", "Cmd")
        self.rtc.BeginBold()
        self.rtc.WriteText(command + " ")
        self.rtc.EndBold()
        self.rtc.BeginItalic()
        self.rtc.WriteText(shortcut + " :\n")
        self.rtc.EndItalic()
        if type(text) == ListType:
            for line in text:
                self.rtc.WriteText("\t%s\n" % line)
        else:
            self.rtc.WriteText("\t%s\n" % text)
        self.rtc.EndFontSize()

    def onClose(self, evt):
        self.Destroy()
