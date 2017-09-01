Granulator Controls
===================

The __Granulator Controls__ window (_File_ -> _Open Granulator Controls (Ctrl+P)_)
allow the user to fine-tune the behaviour of the granulators, globally or in 
relation with the position of the trajectory's reading head in the Y axis of 
the surface.
 
______________________________________________________________________________

Granulator
----------

In the first tab of the window, user can set the global parameters of the 
granulator. These controls modify the granulator of all trajectories at once.

##### Density of Grains per Second #####

This parameter controls how many grains will start per second.
 
##### Global Transposition #####

This parameter transposes the pitch of every grains at once.

##### Grains Duration (ms) #####

Duration, in milliseconds, of the grains. The density times the duration gives
the total number of overlaps of the granulators.

##### Grains Start Time Deviation #####

With no start time deviation (0), grain streams are syncronous. That means each
grain will start at a fixed intervall of _1 / density_, in second. The start
time deviation allows to do asynchronous granulation by adding a random amount
of time to the starting intervall of each grain, breaking the rhythm.

##### Grains Filter Frequency #####

Cutoff or center freqency of the second-order IIR filter applied independently on
each grain. The frequency of the filter is sampled at the beginning of the grain.

##### Grains Filter Q #####

Q (amount of resonance) of the second-order IIR filter applied independently on
each grain. The Q of the filter is sampled at the beginning of the grain.

##### Grains Filter Type (lp - hp - bp - bs - ap) #####

Type of the second-order IIR filter applied independently on
each grain. The type of the filter is sampled at the beginning of the grain.
Types are: 0 = lowpass, 1 = highpass, 2 = bandpass, 3 = bandstop, 4 = allpass.

##### Grains Density Random #####

Adds some random to the grain density.

##### Grains Pitch Random #####

Adds some random to the pitch of each grain individually.

##### Grains Duration Random #####

Adds some random to the duration of each grain individually.

##### Grains Position Random #####

Adds some random to the position of each grain in the file.

##### Grains Panning Random #####

Adds some random to the panning of each grain individually.

##### Grains Filter Freq Random #####

Adds some random to the filter's cutoff or center frequency of each grain
individually.

##### Grains Filter Q Random #####

Adds some random to the filter's Q of each grain individually.

##### Random Transpo per Grain (list of ratios) #####

Transpose each grain individually by an amount randomly picked up from a
user-defined list (comma separated). A value of 1 does no transposition, 
0.5 is an octave below, 2 is an octave above and so on...

##### Random Filter Freq per Grain (list of ratios) #####

Transpose the filter's cutoff or center frequency of each grain individually
by an amount randomly picked up from a user-defined list (comma separated).
A value of 1 does no transposition, 0.5 is an octave below, 2 is an octave 
above and so on...

______________________________________________________________________________

Y Axis
------

In the second tab of the window, the user can decide which parameter(s) will
be linked to the position of the trajectory's reading head in the Y axis of 
the surface. The numerical range can also be adjusted (_min_ is the bottom
of the surface and _max_ is the top).
 
##### Density of Grains Multiplier #####

Multiply the grain density of the granulator by the position of the reading
head scaled inside _min_ and _max_.

##### Transposition Multiplier #####

Multiply the grain pitches of the granulator by the position of the reading
head scaled inside _min_ and _max_.

##### Grains Duration Multiplier #####

Multiply the grain durations of the granulator by the position of the reading
head scaled inside _min_ and _max_.

##### Grains Start Time Deviation #####

Add some start time deviation to the global start time deviation for the given
trajectory. 

##### Amplitude Multiplier #####

Multiply the grain amplitudes of the granulator by the position of the reading
head scaled inside _min_ and _max_.

##### Grains Filter Freq Multiplier #####

Multiply the grain filter's cutoff or center frequency of the granulator by the
position of the reading head scaled inside _min_ and _max_.

##### Grains Filter Q Multiplier #####

Multiply the grain filter's Q of the granulator by the position of the reading
head scaled inside _min_ and _max_.

##### Grains Transposition Random #####

Add some random to the transposition of each grain for the given trajectory.
The amount of random is controlled by the position of the reading head scaled
inside _min_ and _max_. 

##### Grains Duration Random #####

Add some random to the duration of each grain for the given trajectory.
The amount of random is controlled by the position of the reading head scaled
inside _min_ and _max_. 

##### Grains Position Random #####

Add some random to the position of each grain in the file for the given trajectory.
The amount of random is controlled by the position of the reading head scaled
inside _min_ and _max_. 

##### Grains Filter Freq Random #####

Add some random to the filter's cutoff or center frequency of each grain for the
given trajectory. The amount of random is controlled by the position of the reading
head scaled inside _min_ and _max_. 

##### Grains Filter Q Random #####

Add some random to the filter's Q of each grain for the given trajectory. The amount
of random is controlled by the position of the reading head scaled inside _min_ and _max_. 

##### Grains Panning #####

Change the panning position of each grains of the given trajectory. For example, 
in stereo, the bottom of the surface is far left and the top of the surface is 
far right.
