import os, sys

NAME = 'Sound Grain'
VERSION = '2.0'

PLATFORM = sys.platform

if '/SoundGrain.app' in os.getcwd():
    RESOURCES_PATH = os.getcwd()
    currentw = os.getcwd()
    spindex = currentw.index('/SoundGrain.app')
    os.chdir(currentw[:spindex])
else:
    RESOURCES_PATH = os.path.join(os.getcwd(), 'Resources')

OUNK_PATH = os.path.join(os.path.expanduser('~'), '.ounk')
TEMP_PATH = os.path.join(os.path.expanduser('~'), '.soundgrain')

if not os.path.isdir(TEMP_PATH):
    os.mkdir(TEMP_PATH)
    