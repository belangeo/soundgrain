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

import os, sys, unicodedata
from types import UnicodeType

reload(sys)
sys.setdefaultencoding("utf-8")

DEFAULT_ENCODING = sys.getdefaultencoding()
SYSTEM_ENCODING = sys.getfilesystemencoding()

NAME = 'Soundgrain'
SG_VERSION = '4.1.1'
SG_YEAR = '2012'
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

preffile = os.path.join(os.path.expanduser("~"), ".soundgrain-init")
if os.path.isfile(preffile):
    with open(preffile, "r") as f:
        lines = f.readlines()
        if len(lines) > 2:
            SAMPLE_PRECISION = lines[2].split("=")[1].replace("\n", "")
        else:
            SAMPLE_PRECISION = "32-bit"
else:
    SAMPLE_PRECISION = "32-bit"

TRAJTYPES = {0: 'free', 1: 'circle', 2: 'oscil', 3: 'line'}

BACKGROUND_COLOUR = "#ECE6EA"

def ensureNFD(unistr):
    if PLATFORM in ['linux2', 'win32']:
        encodings = [DEFAULT_ENCODING, SYSTEM_ENCODING,
                     'cp1252', 'iso-8859-1', 'utf-16']
        format = 'NFC'
    else:
        encodings = [DEFAULT_ENCODING, SYSTEM_ENCODING,
                     'macroman', 'iso-8859-1', 'utf-16']
        format = 'NFC'
    decstr = unistr
    if type(decstr) != UnicodeType:
        for encoding in encodings:
            try:
                decstr = decstr.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
            except:
                decstr = "UnableToDecodeString"
                print "Unicode encoding not in a recognized format..."
                break
    if decstr == "UnableToDecodeString":
        return unistr
    else:
        return unicodedata.normalize(format, decstr)

def toSysEncoding(unistr):
    try:
        if PLATFORM == "win32":
            unistr = unistr.encode(SYSTEM_ENCODING)
        else:
            unistr = unicode(unistr)
    except:
        pass
    return unistr
