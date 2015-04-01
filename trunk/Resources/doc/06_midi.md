Midi Controls
=============

This section provides documentation about how to setup the MIDI controls in
Soundgrain. 

The MIDI keyboard can be used to trigger a memorized trajectory at different
position on the surface and/or with different transposition factors.
 
______________________________________________________________________________

Midi Interface
--------------

This dropdown menu let the user to choose the desired MIDI interface. Be sure
to plug your MIDI interface before launching the application as the interface
list is updated only at startup time.

______________________________________________________________________________

Add / Remove Method
-------------------

There is two modes to add and remove trajectories on the surface.

<br>

- __Noteon / Noteoff__: With this mode, a noteon adds a new trajectory and the
corresponding noteoff removes it.
- __Noteon / Noteon__: With this mode, a noteon adds a new trajectory on the 
surface (if no trajectory is already associated with the pitch of the note) 
and a second hit on the same midi note will remove the corresponding trajectory.
______________________________________________________________________________

Pitch Mapping
-------------

The pitch of the midi notes can work in two (complementary) ways. 

If the __Transposition__ check box is on, the new trajectory will be transposed 
by the difference (in semitones) between the middle C (note 60) and the played
note. 

If the __X Axis Position__ check box is on, the pitch of the midi notes will 
change the position of the new trajectory on the surface. The surface is
divided, around middle C, in a number of octaves (12 semitones). The lower
note will create the trajectory far left on the surface and the higher note
will create the trajectory far right on the surface. The user can change the
number of octaves which divide the surface with the __X Position Octave Spread__
slider.

Velocity Mapping
----------------

The velocity of the MIDI note gives the position of the trajectory on the Y axis.
Velocity 0 is the bottom of the surface and velocity 127 is the top.
 
