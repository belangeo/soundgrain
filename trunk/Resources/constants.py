"""
Copyright 2009 Olivier Belanger

This file is part of SoundGrain.

SoundGrain is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

SoundGrain is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with SoundGrain.  If not, see <http://www.gnu.org/licenses/>.
"""

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
    