import math

class Biquad:
    def __init__(self, freq=5000, q=0.5):
        self.sr = 44100
        self.xn1 = self.xn2 = self.yn1 = self.yn2 = 0
        self.freq = freq
        self.q = q
        self.init = True
        self.computeVariables()
        self.computeLpCoeffs()

    def computeVariables(self):
        self.w0 = 2 * math.pi * self.freq / self.sr
        self.c = math.cos(self.w0)
        self.alpha = math.sin(self.w0) / (2 * self.q)

    def setFreq(self, freq):
        self.freq = freq
        self.computeVariables()
        self.computeLpCoeffs()

    def setQ(self, q):
        self.q = q
        self.computeVariables()
        self.computeLpCoeffs()

    def filter(self, xn):
        if self.init:
            self.xn1 = self.xn2 = self.yn1 = self.yn2 = xn
            self.init = False

        yn = ( ((self.b0/self.a0) * xn) + ((self.b1/self.a0) * self.xn1) + ((self.b2/self.a0) * self.xn2) -
               ((self.a1/self.a0) * self.yn1) - ((self.a2/self.a0) * self.yn2) )
        self.yn2 = self.yn1
        self.yn1 = yn
        self.xn2 = self.xn1
        self.xn1 = xn
        return yn

    def reinit(self):
        self.init = True

class BiquadLP(Biquad):
    def computeLpCoeffs(self):
        self.b0 = (1 - self.c) / 2
        self.b1 = 1 - self.c
        self.b2 = (1 - self.c) / 2
        self.a0 = 1 + self.alpha
        self.a1 = -2 * self.c
        self.a2 = 1 - self.alpha

class BiquadHP(Biquad):
    def computeLpCoeffs(self):
        self.b0 = (1 + self.c) / 2
        self.b1 = -(1 + self.c)
        self.b2 = (1 + self.c) / 2
        self.a0 = 1 + self.alpha
        self.a1 = -2 * self.c
        self.a2 = 1 - self.alpha

class BiquadBP(Biquad):
    def computeLpCoeffs(self):
        self.b0 = self.alpha
        self.b1 = 0
        self.b2 = -self.alpha
        self.a0 = 1 + self.alpha
        self.a1 = -2 * self.c
        self.a2 = 1 - self.alpha

class BiquadBR(Biquad):
    def computeLpCoeffs(self):
        self.b0 = 1
        self.b1 = -2 * self.c
        self.b2 = 1
        self.a0 = 1 + self.alpha
        self.a1 = -2 * self.c
        self.a2 = 1 - self.alpha
