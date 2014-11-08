import initExample ## Add path to library (just for examples; you do not need this)
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import pygame
import time
import os

GRAPH_SND_RATIO = 100

def speedx(snd_array, factor):
    """ Speeds up / slows down a sound, by some factor. """
    indices = np.round( np.arange(0, len(snd_array), factor) )
    indices = indices[indices < len(snd_array)].astype(int)
    return snd_array[ indices ]

def stretch(snd_array, factor, window_size=2**13, h=2**11):
    """ Stretches/shortens a sound, by some factor. """
    phase  = np.zeros(window_size)
    hanning_window = np.hanning(window_size)
    result = np.zeros( len(snd_array) /factor + window_size)

    for i in np.arange(0, len(snd_array)-(window_size+h), h*factor):

        # two potentially overlapping subarrays
        a1 = snd_array[i: i + window_size]
        a2 = snd_array[i + h: i + window_size + h]

        # the spectra of these arrays
        s1 =  np.fft.fft(hanning_window * a1)
        s2 =  np.fft.fft(hanning_window * a2)

        #  rephase all frequencies
        phase = (phase + np.angle(s2/s1)) % 2*np.pi

        a2_rephased = np.fft.ifft(np.abs(s2)*np.exp(1j*phase))
        i2 = int(i/factor)
        result[i2 : i2 + window_size] += hanning_window*a2_rephased

    result = ((2**(16-4)) * result/result.max()) # normalize (16bit)

    return result.astype('int16')

def pitchshift(snd_array, n, window_size=2**13, h=2**11):
    """ Changes the pitch of a sound by ``n`` semitones. """
    factor = 2**(1.0 * n / 12.0)
    stretched = stretch(snd_array, 1.0/factor, window_size, h)
    return speedx(stretched[window_size:], factor)


def init():
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.mixer.init()

def load_sound(path):
    snd = pygame.mixer.Sound(path)
    array = pygame.sndarray.array(snd)
    return array

pg.mkQApp()

## Define main window class from template
path = os.path.dirname(os.path.abspath(__file__))
uiFile = os.path.join(path, 'designerExample.ui')
WindowTemplate, TemplateBaseClass = pg.Qt.loadUiType(uiFile)

print TemplateBaseClass

class MainWindow(TemplateBaseClass):  
    def __init__(self):
        TemplateBaseClass.__init__(self)
        self.setWindowTitle('My own down sampler')
        
        self.play_ch = None

        #
        # Create the main window
        #
        self.ui = WindowTemplate()
        self.ui.setupUi(self)
        self.ui.plotBtn.clicked.connect(self.play)
        
        self.show()
        
    def play(self):
        
        if self.play_ch is not None:
            self.play_ch.stop()

        start, end = [i*GRAPH_SND_RATIO for i in self.lr.getRegion()]
        array = self.snd_array[start:end, ...]
        array = np.ascontiguousarray(np.vstack(([stretch(array[:, i], 0.75) for i in range(2)])).T)
        
        snd = pygame.sndarray.make_sound(array)
        self.play_ch = snd.play(loops=-1)

    def plot(self, snd_array):
        self.snd_array = snd_array
        garray = snd_array[::GRAPH_SND_RATIO, 0].astype(np.float)

        self.ui.plot.plot(garray, pen=(255,255,255,200))
        self.lr = pg.LinearRegionItem([400,700])
        self.lr.setZValue(-10)
        self.ui.plot.addItem(self.lr)

        #self.lr.sigRegionChanged.connect(updatePlot)

    def on_event(self, event):
        print event


win = MainWindow()


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    init()
    snd_array = load_sound('Blues.wav')

    win.plot(snd_array)

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()



