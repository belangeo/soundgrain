Sound Grain is a graphical interface where users can draw and edit trajectories to control granular sound synthesis modules.

# Requirements #

**Minimum versions (for running SoundGrain from sources):**

[Python](http://python.org/download/releases/2.7.2/) : 2.6.x

[WxPython](http://www.wxpython.org/download.php#stable) : 2.8.x

[pyo](http://code.google.com/p/pyo/downloads/list) : sources up-to-date

# News #

## SoundGrain version 4.1.1 - June 2012 ##

This version fixes an important memory leak and a few minor bugs.

## SoundGrain version 4.1.0 - February 2012 ##

This version fixes several bugs and adds some important features :

  * Fixed crash when playing with number of channels.

  * Fixed unicode support, allowing non-ascii characters.

  * Fixed trajectories and FxBalls position when resizing the application frame.

  * Added support for ASIO driver on Windows.

  * Added sample floating-point precision in the Audio Drivers menu.

  * Added new FxBalls : Chorus, Frequency Shift, Detuned Resonator.

  * Added the possibility to mix multiple sounds (with crossfade) into the drawing area.

## SoundGrain version 4.0.1 - February 2011 ##

This a small bug fix release for OSX 10.6.6.

  * The **psyco** library is no more used.

## SoundGrain version 4 - February 2011 ##

In version 4.0 is the return of Windows support with a standalone combining the interface and the audio engine.

This version fixes all known bugs and adds some important features :

  * Midi support : User can add and remove trajectories with a midi keyboard

  * Fx balls : User can put balls on the drawing surface to add temporary effects on sound produced by the granular process

  * Grain envelope : User can modify the grain envelope with a graph window

  * Amplitude control on each trajectory

  * Panning can be assigned to the Y axis

## SoundGrain version 3 ##

-------- CSOUND REPLACED BY PYO --------

[Revision 180](https://code.google.com/p/soundgrain/source/detail?r=180) is a breaking compatilibity turn around. It's the starting point of version 3.0 and the end of MS Windows support. Csound have been replaced by [pyo](http://code.google.com/p/pyo) as the audio engine. pyo offers more flexibility for granulation process and the ability to build an App with all dependencies embeded. I hope you will enjoy!

## SoundGrain version 1 and 2 ##

Sound Grain v1.0 and v2.0 are written with Python and use Csound as their audio engine. Csound 5 must be installed on the system to allow Sound Grain to run.

Csound's download page - http://csound.sourceforge.net/#Downloads

# Contact #

For questions and comments please mail belangeo(at)gmail.com

## Donation ##

This project is developed by Olivier Bélanger on his free time to provide a simple and expressive tool for sound exploration. If you feel this project is useful to you and want to support it and it's future development please consider donating money. I only ask for a small donation, but of course I appreciate any amount.

[![](https://www.paypal.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=9CA99DH6ES3HA)