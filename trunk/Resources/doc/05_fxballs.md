FX Balls
========

FxBalls allow the user to add effect regions on the drawing surface. Only the
trajectories that cross a ball (and only for the time that the trajectory is
inside the ball) will send their audio output through the chosen effect.

This section provides documentation about the effects available with the 
FX balls.

See the mouse bindings on [Surface page](02_surface.md) for the detail about 
how to interact graphically with the balls.

A right-click on the ball opens the parameter window for the chosen effects.
All effects provides controls for the amplitude and the panning of the effect.
The first two sliders on the window are related to the chosen effect.
______________________________________________________________________________

Effects
-------

##### Reverb #####

A simple reverberator made of a network of eight waveguides.

<br>

- __Feedback__: Amount of output signal sent back into the delay line network.
Related, in some way, to the size of the room.
- __Cutoff__: Cutoff frequency, in Hz, of the post-network lowpass filter.

##### Delay #####

A simple recursive delay line.

<br>

- __Delay__: Duration of the delay, in seconds.
- __Feedback__: Amount of output signal sent back into the delay line.

##### Disto #####

A simple arc-tangent distortion.

<br>

- __Drive__: Amount of distortion applied to the signal.
- __Slope__: Slope of the lowpass filter applied after the distortion. The 
higher the slope, the lower the cutoff frequency of the filter.

##### Waveguide #####

This waveguide model is composed of one delay-line with a simple lowpass 
filtering and lagrange interpolation.

<br>

- __Frequency__: Frequency, in Hz, of the resonator.
- __Fall Time__: Duration, in seconds, for the waveguide to drop 40 dB below 
its maxima.

##### Complex Resonator #####

Complex one-pole resonator filter. Implements a resonator derived from a 
complex multiplication, which is very similar to a digital filter.

<br>

- __Frequency__: Center frequency, in Hz, of the filter.
- __Decay__: Decay time, in seconds, for the filter's response.

##### Degrade #####

Signal quality reducer. Takes an audio signal and reduces its sampling rate 
and/or its bit-depth.

<br>

- __Bit Depth__: Signal quantization in number of bits.
- __SR Scale__: Signal sampling rate multiplier.

##### Harmonizer #####

Generates harmonizing voice in synchrony with its audio input.

<br>

- __Transposition__: Transposition factor in semitone.
- __Feedback__: Amount of output signal sent back into the delay lines.

##### Clipper #####

Clips an signal according to a bipolar threshold (Harsh distortion).

<br>

- __Threshold__: Negative minimum value and positive maximum value of the 
signal's sample amplitude in output.
- __Cutoff__: Cutoff frequency, in Hz, of the post-process lowpass filter.

##### Flanger #####

A simple flanger effect. A flanger effect is produced by mixing two identical 
signals together, one signal delayed by a small and gradually changing period.

<br>

- __LFO Freq__: Frequency, in Hz, of the lfo producing the gradual changes of 
the delay time.
- __Feedback__: Amount of output signal sent back into the delay line.

##### Detuned Resonator #####

Out of tune waveguide model with a recursive allpass network. This waveguide 
model consisting of one delay-line with a 3-stages recursive allpass filter 
which made the resonances of the waveguide out of tune.

<br>

- __Frequency__: Frequency, in Hz, of the resonator.
- __Detune__: Control the depth of the allpass delay-line filter, i.e. the 
depth of the detuning.
