# What's New

## 6.1.0

### Installation

- Added pip installation with pyo, wxPython, and Markdown dependencies, plus a
  `soundgrain` command for launching the application from any directory.
- Added `soundgrain-register-desktop` to create a per-user application launcher
  on Linux, Windows, and macOS.
- Isolated installed resources so SoundGrain and Cecilia can share a Python
  environment.

### Microphone recording

- Added mono microphone recording directly into the sound table, with an
  adjustable duration and a live waveform display. Recording can run alongside
  trajectory playback, and captured audio can be saved when prompted.
- Added input-device selection in Settings and output-only fallback when the
  input device cannot be opened.

### Trajectories and drawing

- Added a **Var** tab for controlling each trajectory's width, variation speed,
  and blend between periodic and random motion. Wider trajectories appear as
  translucent bands, and the playback position moves within the band.
- Added horizontal canvas zoom around the pointer using vertical scrolling.
  Scroll horizontally or Shift+scroll to pan, and press Escape to restore the
  full view. The waveform shows more detail as you zoom in.
- Preserved variation settings when saving, copying, and memorizing
  trajectories, with defaults for projects created by earlier versions.

### Interface

- Added an **Open Recent** menu for quickly reopening projects.
- Moved audio, project, and recording options into a **Settings** window.
- Updated the interface to follow the system theme and improved the appearance
  of FX balls and the splash screen.
- Improved the layout of the Granulator and MIDI Settings windows.
- Made SoundGrain project files (`*.sg`) the default type in save dialogs.

### Fixes

- Fixed compatibility issues with wxPython 4.
- Fixed crashes and late audio callbacks when quitting, and ensured FX control
  windows close with the application.
- Fixed EQ and compressor knobs sending values during repaint.
