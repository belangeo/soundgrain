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

import math

class Biquad:
    def __init__(self, freq=5000, q=0.5):
        self.sr = 44100
        self.xn1 = self.xn2 = self.yn1 = self.yn2 = 0
        self.freq = freq
        self.q = q
        self.init = True
        self.computeVariables()
        self.computeCoeffs()

    def computeVariables(self):
        self.w0 = 2 * math.pi * self.freq / self.sr
        self.c = math.cos(self.w0)
        self.alpha = math.sin(self.w0) / (2 * self.q)

    def setFreq(self, freq):
        self.freq = freq
        self.computeVariables()
        self.computeCoeffs()

    def setQ(self, q):
        self.q = q
        self.computeVariables()
        self.computeCoeffs()

    def filter(self, xn):
        if self.init:
            self.xn1 = self.xn2 = self.yn1 = self.yn2 = xn
            self.init = False

        yn = ( (self.b0 * xn) + (self.b1 * self.xn1) + (self.b2 * self.xn2) -
               (self.a1 * self.yn1) - (self.a2 * self.yn2) ) / self.a0
        self.yn2 = self.yn1
        self.yn1 = yn
        self.xn2 = self.xn1
        self.xn1 = xn
        return yn

    def reinit(self):
        self.init = True

class BiquadLP(Biquad):
    def __init__(self, freq=5000, q=0.5):
        Biquad.__init__(self, freq, q)

    def computeCoeffs(self):
        self.b0 = (1 - self.c) / 2
        self.b1 = 1 - self.c
        self.b2 = (1 - self.c) / 2
        self.a0 = 1 + self.alpha
        self.a1 = -2 * self.c
        self.a2 = 1 - self.alpha
