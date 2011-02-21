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
VERSION = '4.0.1'
PLATFORM = sys.platform
MAX_STREAMS = 16

if '/SoundGrain.app' in os.getcwd():
    RESOURCES_PATH = os.getcwd()
    currentw = os.getcwd()
    spindex = currentw.index('/SoundGrain.app')
    os.chdir(currentw[:spindex])
else:
    RESOURCES_PATH = os.path.join(os.getcwd(), 'Resources')

if not os.path.isdir(RESOURCES_PATH) and sys.platform == "win32":
    RESOURCES_PATH = os.path.join(os.getenv("ProgramFiles"), "SoundGrain", "Resources")

IMAGES_PATH = os.path.join(RESOURCES_PATH, 'images')

TRAJTYPES = {0: 'free', 1: 'circle', 2: 'oscil', 3: 'line'}

BACKGROUND_COLOUR = "#ECE6EA"

ENCODING = sys.getfilesystemencoding()
