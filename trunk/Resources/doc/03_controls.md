Control Panel
=============

This panel provides general controls on drawing and playback behaviours,
on global audio settings and on audio recording format.
 
______________________________________________________________________________

Trajectories
------------

The dropdown menu gives the possible type of trajectories:

- Free: Free-hand style drawing.
- Circle: Draw a circle with control on the radius.
- Oscil: Draw oscillations using period and scaling factors adjusted in the 
drawing tab.
- Line: Draw a straight line.

In free-hand style, if the __Closed__ button is activated, the last point will
be automatically connected to the first on mouse up.

With _Circle_ and _Oscil_ types, a little blue diamond is located at the bottom
right of the trajectory. Click and drag on this diamond resize the circle or
the oscillation. If the trajectory is modified with the mouse, the diamond
disappears because the shape is no more a circle or an oscillation.

______________________________________________________________________________

Drawing
-------

The four sliders in the _Drawing_ tab can be used to fine-tune the drawing
behaviour on the surface.

Sliders labelled __Lowpass cutoff__ abd __Lowpass Q__ allow the user to control
the frequency and the resonance of a lowpass filter applied on the sequence of 
drawn points to smooth the trajectory. This feature can be disabled in the 
_Drawing_ menu. Although this filter's main goal is to smooth the drawing curves
on the surface, it can be used to create modulation effect. Higher the Q of 
the filter, deeper the amplitude of the modulation. Low frequencies will create
large modulation while high frequencies will create narrow modulation.
 
Sliders labelled __Oscil period__ and __Oscil scaling__ are enabled only for
the _Oscil_ trajectory type. __Oscil period__ controls how many waves will be
present in the oscillation, and __Oscil scaling__ controls how many back-and-forth
will be drawn. Non-integer values can give very complex trajectories.

______________________________________________________________________________

Playback
--------

In the _Playback_ tab, the user can control independently the reading head and 
the gain of every trajectory.

The dropdown menu indicates which trajectory (or "all") is selected and therefore
which will be affected by the sliders just below.

The slider labelled __Timer speed__ control how fast the sequence of points will
be read (Although a trajectory looks like a curve, it is, under the hood, a 
sequence of points). The value is in milliseconds. The slider labelled __Point step__
control the increment of the reading head. A value of 1 means that the playback 
will read all points. But if this value is 10, only one point over 10 will be read,
making the playback doing longer jumps.

The slider labelled __Amplitude (dB)__ controls the gain of the selected trajectory.
This allow the user to adjust the volume of the trajectories relative to each other.

______________________________________________________________________________

Global Amplitude
----------------

This is the global volume of the application. Adjusting this value will rise
or drop the entirety of the generated signals.

______________________________________________________________________________

Project Settings
----------------

Here the user can set the desired sampling rate and number of audio channels.
These two values must be supported by the current audio driver.

______________________________________________________________________________

Start
-----

The __Start__ button activates the audio server (start/stop the sound). This 
is the same as the menu item _File_ -> _Run_.

______________________________________________________________________________

Record Settings
---------------

In this section, the user can set record settings and start/stop writing audio 
files on disk.

The first two dropdown menus offer a selection of available audio file format 
and sample type for the recorded file.

Just below, the widget labelled __Destination__ let the user enter the complete
path of the repository where to save the file. The button __Choose__ opens a
standard dialog to select the folder graphically.

In the text entry labelled __Filename__, the user can specify the name of the
recorded files. Here we give only the generic name of the files, without 
extension. Soundgrain will automatically append the date, time and the extension 
to the filename, in order to avoid overwriting an existing file. The extension
is chosen according to the file format dropdown menu.

The __Start Rec__ button starts the recording. Don't forget to stop it before
using the recorded file. Otherwise, the file won't be a valid audio file.  
