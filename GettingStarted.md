List of commands.

# Menus #

## Menu File ##

### Open, Save or Save as... ###

Open, Save or Save as .sg files (not sound). A .sg file is a snapshot of the state of the project.

### Open Soundfile... ###

(Shift+Ctrl+O) Import a new sound.

### Open FX Window ###

(Ctrl+P) Opens the module's parameters window.

### Run ###

(Ctrl+R) Shortcut to start/stop the sound.

## Menu Drawing ##

### Undo - Redo ###

There is unlimited undo and redo stages. These actions have effect only on drawing surface (trajectories).

### Draw Waveform ###

If checked, the sound waveform will be drawn behind the trajectories.

### Activate Lowpass filter ###

If checked, All points of a trajectory will be filtered by a lowpass filter. This can be used to smooth the trajectory or to insert resonance in the curve when the Q is very high.

### Fill points ###

If checked, spaces between points in a trajectory (especially when stretching the curve) will be filled by adding additional points. If unchecked, number of points in the trajectory won't change, Useful to keep synchronization between similar trajectories.

### Edition levels ###

Set the spread of modification of a trajectory when edited with mouse. Higher values give narrower transformations.

### Reinit counters ###

Re-sync the trajectories points counter. This is automatically done when the audio is started.

## Menu Audio Drivers ##

Used to choose the desired driver. The drivers list is updated only on startup.

# Drawing surface #

  * **clic on empty space** : adds a new trajectory
  * **left-clic on red rect** : moves a trajectory
  * **right-clic on red rect** : deletes a trajectory
  * **alt+clic on red rect** : duplicates a trajectory
  * **left-clic on blue diamond** : rescales a circle or oscil trajectory
  * **left-clic on a trajectory** : the user can drag and modify the shape of the trajectory. See Edition levels.

With the focus on the drawing surface:

  * arrow keys moves all trajectories
  * Shift + arrow keys move the selected trajectory
  * 1 to 8 (not on numeric keypad) freezes and unfreezes the targeted trajectory
  * 0 (not on numeric keypad) freezes and unfreezes all trajectories