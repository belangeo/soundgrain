Control Panel
=============

This panel provides controls for drawing, playback, global audio processing
and starting or stopping audio and recording. Audio, project and recording settings
are in the Settings window (_File_ -> _Open Settings_, _Ctrl+;_).
 
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

The __Var__ tab between __Draw__ and __Play__ contains three sliders:

- __Width__: pen width from 2 to 500 pixels, defaulting to 2.
- __Variation speed__: the speed of the smooth sideways variation, from 0.1x
  to 10x. The default of 1x is normal speed; lower values drift more slowly and
  higher values drift faster. This does not change progress along the line.

- __Periodic &lt;--&gt; Random__: blends between sinusoidal motion at 0 and fully random,
  smooth motion at 1. Intermediate values gradually blend the two. The default
  is 0 (sinusoidal motion). At 0, a full sine cycle takes
  1.6 seconds at 1x variation speed; the speed slider scales both kinds of motion.

The __Selected Traj__ popup selects which trajectory the sliders affect. It is
synchronized with the popup in __Play__. Choose __all__ to affect all active
trajectories. All three sliders take effect immediately, including during playback.
Selecting a trajectory displays its own width, random speed and periodicity without changing
other trajectories. With __all__ selected, the sliders initially display the
first trajectory's settings; moving a slider applies that value to all active
trajectories.

Each trajectory saves its width, random speed and periodicity independently in the project.
Copies and memorized trajectories retain all three settings. New trajectories start
with the values currently displayed in __Var__.

At the default width of 2, playback follows the centerline exactly. Wider
trajectories appear as translucent bands. Self-crossings retain the same color
and opacity without cutting holes in the band. Bands have small rounded corners at their
ends. The band extends only enough to surround the trajectory number at its
start and stops at the final point. The playback ball wanders smoothly
from side to side, perpendicular to the local direction of the line, while
advancing at the same pace set by __Timer speed__ and __Point step__. Its displaced
position controls the sound and its interaction with FX balls. The marker uses lighter and darker shades of the trajectory color to keep
the current position visible over the colored band.

With _Circle_ and _Oscil_ types, a little blue diamond is located at the bottom
right of the trajectory. Click and drag on this diamond resize the circle or
the oscillation. If the trajectory is modified with the mouse, the diamond
disappears because the shape is no more a circle or an oscillation.

______________________________________________________________________________

Drawing
-------

The four sliders in the _Draw_ tab can be used to fine-tune the drawing
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

In the _Play_ tab, the user can control independently the reading head and
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

4 Bands Equalizer
-----------------

This is a four bands equalizer that you can use to adjust the spectrum of the 
output sound. All trajectories and fx balls are mixed before passing through the
EQ.

The controls are the three frequencies, in Hz, delimiting the four bands and the
four dB gains adjusting the amplitude of each band. 

______________________________________________________________________________

Dynamic Compressor
------------------

This is a dynamic compressor taking as input the output of the EQ, compressing the
signal and sending its output to the final "Global Amplitude" control.

The controls are:

__Thresh__: Level, expressed in dB, above which the signal is reduced. Reference 
level is 0dB.

__Ratio__: Determines the input/output ratio for signals above the threshold.

__Rise__: Used in the compressor's amplitude follower, time to reach upward value 
in seconds.

__Fall__: Used in the compressor's amplitude follower, time to reach downward value
in seconds.
______________________________________________________________________________

Global Amplitude
----------------

This is the global volume of the application. Adjusting this value will rise
or drop the entirety of the generated signals.

______________________________________________________________________________

Start and Rec Start
-------------------

The __Start__ and __Rec Start__ buttons sit side by side at the bottom of the
control panel.

The __Start__ button activates the audio server, starting sound playback, and
changes to __Stop__ while audio is running. This is the same as the menu item
_File_ -> _Run_ (_Ctrl+R_).

The __Rec Start__ button starts writing audio to disk and changes to __Rec Stop__
while recording. Click __Rec Stop__ to finish the recording before using the
file, so that it is saved as a valid audio file.

To change the sampling rate, channel count, recording format, sample type,
destination folder or filename, open _File_ -> _Open Settings_ (_Ctrl+;_).
See [Open Settings in the File menu documentation](01_menus.md) for details.
