Menu Bar
========

This section provides documentation for the menu items located in the
menu bar of the application. OSX users should replace the shortcut _Ctrl_ 
key with the _Cmd_ key.

______________________________________________________________________________

File Menu
---------

##### New... (*Ctrl+N*) #####
    
Closes the current project (ask to save if modified) and starts a new one.

##### Open... (*Ctrl+O*) #####

Open a previously created .sg file.

##### Open Soundfile... (*Shift+Ctrl+O*) #####

Import a new sound into the drawing area.

##### Insert Soundfile... (*Shift+Ctrl+I*) #####

Insert a new sound (with crossfade) into the current drawing area.

##### Save (*Ctrl+S*) #####

Save the current state of the project.

##### Save As... (*Shift+Ctrl+S*) #####

Save the current state of the project in a new .sg file.

##### Open Granulator Controls (*Ctrl+P*) #####

Open the [granulator's parameters window](04_granulator.md). This window, 
in the tab called 'Granulator', allows the user to change the density of 
grains per second, the global transposition, the grain duration, the grain 
start time deviation (synchronous vs asynchronous) and various randoms 
applied to the granulator. In the second tab, called 'Y axis', one can 
decide on which parameters, and its range, the Y axis of the drawing area 
will be mapped. Available parameters are: Density of grains, transposition, 
grain duration, start time deviation, amplitude, grain panning and various 
per grain randoms applied to the granulator.

##### Open Envelope Window (*Ctrl+E*) #####

Open a grapher window to modify the shape of the grain's envelope.

##### Run (*Ctrl+R*) #####

Start/stop audio processing.

______________________________________________________________________________

Drawing Menu
------------

##### Undo, Redo (*Ctrl+Z, Shift+Ctrl+Z*) #####

Unlimited undo and redo stages for the drawing area (only trajectories).

##### Draw Waveform  #####

If checked, the loaded soundfile's waveform will be drawn behind the trajectories.

##### Activate Lowpass filter  #####

If checked, all points of a new trajectory will be filtered using a lowpass 
filter. Controls of the filter are located in the Drawing section of the control 
panel. This can be used to smooth out the trajectory or to insert resonance in 
the curve when the Q is very high.

##### Fill points  #####

If checked, spaces between points in a trajectory (especially when stretching 
the curve) will be filled with additional points. If unchecked, the number of 
points in the trajectory won't change, allowing synchronization between similar 
trajectories.

##### Edition levels  #####

Set the modification spread of a trajectory when edited with the mouse (higher 
values mean narrower transformations).

##### Reinit counters  (*Ctrl+T*) #####

Re-sync the trajectories's counters (automatically done when audio is started).

______________________________________________________________________________

Audio Drivers Menu
------------------

##### Audio Driver #####

Choose the desired audio driver. The drivers list is updated only at startup.

##### Sample Precision #####

Set the audio sample precision either 32 or 64 bits. Require restarting the application.

______________________________________________________________________________

Midi Menu
---------

##### Memorize Trajectory (*Shift+Ctrl+M*) ######

Memorize the state of the selected trajectory The ensuing snapshot will be the 
initial state for trajectories triggered by MIDI notes.

##### Midi Settings... ######

Open the MIDI configuration and controls window.

See the [Midi Controls page](06_midi.md) for the detail about how to use MIDI 
with Soundgrain.

______________________________________________________________________________

FxBall Menu
-----------

FxBalls allow the user to add effect regions on the drawing surface. Only the
trajectories that cross a ball (and only for the time that the trajectory is
inside the ball) will send their audio output through the chosen effect.

See the [FX Balls page](05_fxballs.md) for the detail about available effects.

##### Add Reverb ball (*Ctrl+1*) #####

Create a reverb region on the drawing surface.

##### Add Delay ball (*Ctrl+2*) #####

Create a recursive delay region on the drawing surface.

##### Add Disto ball (*Ctrl+3*) #####

Create a distortion region on the drawing surface.

##### Add Waveguide ball (*Ctrl+4*) #####

Create a resonator region on the drawing surface.

##### Add Complex Resonator ball (*Ctrl+5*) #####

Create a very selective resonating region on the drawing surface.

##### Add Degrade ball (*Ctrl+6*) #####

Create a degradation region on the drawing surface.

##### Add Harmonizer ball (*Ctrl+7*) #####

Create a harmonization region on the drawing surface.

##### Add Clipper ball (*Ctrl+8*) #####

Create a hard clipping region on the drawing surface.

##### Add Flanger ball (*Ctrl+9*) #####

Create a flanging region on the drawing surface.

##### Add Detuned Resonator ball (*Ctrl+0*) #####

Create an allpass-detuned resonator region on the drawing surface.

