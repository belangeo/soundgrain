"""
Copyright 2009-2017 Olivier Belanger

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

if sys.version_info[0] < 3:
    unicode_t = unicode
else:
    unicode_t = str

if sys.platform == "win32":
    FILE_ENCODING = "mbcs"
else:
    FILE_ENCODING = "utf-8"
DEFAULT_ENCODING = sys.getdefaultencoding()
SYSTEM_ENCODING = sys.getfilesystemencoding()

NAME = 'Soundgrain'
SG_VERSION = '6.0.0'
SG_YEAR = '2017'
PLATFORM = sys.platform
MAX_STREAMS = 16

if '/SoundGrain.app' in os.getcwd():
    os.environ["LANG"] = "en_CA.UTF-8"
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

PREFFILE = os.path.join(os.path.expanduser("~"), ".soundgrain-init")
if os.path.isfile(PREFFILE):
    with open(PREFFILE, "r", encoding=FILE_ENCODING) as f:
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
EXPORT_TYPES = ['16 int', '24 int', '32 int', '32 flt', '64 flt']
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

FX_BALL_TITLES = {0: "Reverb", 1: "Delay", 2: "Disto", 3: "Waveguide", 
                    4: "Complex Resonator", 5: "Degrade", 6: "Harmonizer", 
                    7: "Clipper", 8: "Flanger", 9: "AllpassWG"}

FX_BALL_SLIDER_1_INIT = {   0: ["Feedback", 0, 1, .75, False],
                            1: ["Delay", 0.01, 1, 0.25, False],
                            2: ["Drive", 0, 1, .75, False],
                            3: ["Frequency", 20, 500, 100, True],
                            4: ["Frequency", 20, 4000, 500, True],
                            5: ["Bit Depth", 2, 32, 8, True],
                            6: ["Transposition", -12, 12, -7, False],
                            7: ["Threshold", 0.001, 0.25, 0.1, True],
                            8: ["LFO Freq", 0.1, 20, 0.2, True],
                            9: ["Frequency", 20, 500, 100, True],
                        }

FX_BALL_SLIDER_2_INIT = {   0: ["Cutoff", 100, 15000, 5000, True],
                            1: ["Feedback", 0, 1, 0.5, False],
                            2: ["Slope", 0, .99, .75, False],
                            3: ["Fall time", 1, 60, 30, False],
                            4: ["Decay", 0.001, 5, 1, True],
                            5: ["SR Scale", 0.01, 1, 0.25, True],
                            6: ["Feedback", 0, 1, 0.25, False],
                            7: ["Cutoff", 100, 15000, 5000, True],
                            8: ["Feedback", 0, 1, 0.5, False],
                            9: ["Detune", 0, 1, 0.5, False],
                        }

def ensureNFD(unistr):
    if unistr == None:
        return None
    if PLATFORM.startswith('linux') or PLATFORM == 'win32':
        encodings = [DEFAULT_ENCODING, SYSTEM_ENCODING,
                     'cp1252', 'iso-8859-1', 'utf-16']
        format = 'NFC'
    else:
        encodings = [DEFAULT_ENCODING, SYSTEM_ENCODING,
                     'macroman', 'iso-8859-1', 'utf-16']
        format = 'NFC'
    decstr = unistr
    if type(decstr) != unicode_t:
        for encoding in encodings:
            try:
                decstr = decstr.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
            except:
                decstr = "UnableToDecodeString"
                print("Unicode encoding not in a recognized format...")
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
