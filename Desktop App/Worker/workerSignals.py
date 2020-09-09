from PyQt5.QtCore import *


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress

    '''
    error = pyqtSignal(tuple)
    progress = pyqtSignal(str)
