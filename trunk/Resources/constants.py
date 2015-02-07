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
SG_VERSION = '5.0.0'
SG_YEAR = '2015'
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

DOCUMENTATION_PATH = os.path.join(RESOURCES_PATH, "doc")
IMAGES_PATH = os.path.join(RESOURCES_PATH, 'images')
SPLASH_FILE = os.path.join(RESOURCES_PATH, "SoundGrainSplash.png")

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

ALLOWED_EXTENSIONS = ["wav","wave","aif","aiff","aifc","au","","sd2","flac","caf","ogg"]
EXPORT_FORMATS = ['WAV', 'AIFF', 'AU', 'RAW', 'SD2', 'FLAC', 'CAF', 'OGG']
EXPORT_TYPES = ['16 int', '24 int', '32 int', '32 float', '64 float']
RECORD_EXTENSIONS = [".wav",".aif",".au","",".sd2",".flac",".caf",".ogg"]
AUDIO_WILDCARD = "All Files |*.*|" \
                 "Wave file |*.wav;*.wave;*.WAV;*.WAVE;*.Wav;*.Wave|" \
                 "AIFF file |*.aif;*.aiff;*.aifc;*.AIF;*.AIFF;*.Aif;*.Aiff|" \
                 "AU file |*.au;*.Au;*.AU|" \
                 "RAW file |*|" \
                 "SD2 file |*.sd2;*.Sd2;*.SD2|" \
                 "FLAC file |*.flac;*.Flac;*.FLAC|" \
                 "CAF file |*.caf;*.Caf;*.CAF|" \
                 "OGG file |*.ogg;*.Ogg;*.OGG"

def ensureNFD(unistr):
    if unistr == None:
        return None
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
