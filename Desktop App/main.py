import sys
import time
import traceback
import usb
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from UI.main_window import Ui_MainWindow

idVendor = 1156
idProduct = 22339


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


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.close = False
        self.is_connected = False
        self.is_configured = False
        self.dev = None

        self.window = Ui_MainWindow()
        self.window.setupUi(self)

        self.check_if_device_connected()  # check device connection status before showing window

        self.threadpool = QThreadPool()
        # Pass the function to execute
        self.worker = Worker(self.execute_this_fn)  # Any other args, kwargs are passed to the run function
        self.worker.signals.progress.connect(self.progress_fn)

        # Execute
        self.threadpool.start(self.worker)

    def progress_fn(self, n):
        self.window.textBrowser.insertPlainText(n + "\n")
        if self.window.checkBox.isChecked():
            self.window.textBrowser.verticalScrollBar().setValue(self.window.textBrowser.verticalScrollBar().maximum())

    def execute_this_fn(self, progress_callback):
        while True:
            if self.close:
                return
            if self.is_connected:
                try:
                    result = self.dev.read(0x81, 64, 60000)
                    progress_callback.emit(result.tobytes().decode('utf-8',errors="ignore"))
                except Exception as e:
                    print(e)
                    self.check_if_device_connected(True)
                    pass
            else:
                time.sleep(1)
                self.check_if_device_connected(True)

    def device_connected(self):
        self.window.statusbar.showMessage('Connected')
        self.window.statusbar.setStyleSheet('color: green')

    def device_disconnected(self):
        self.window.statusbar.showMessage('Disconnected')
        self.window.statusbar.setStyleSheet('color: red')

    def find_device(self):
        dev_g = usb.core.find(idVendor=idVendor, idProduct=idProduct, find_all=True)
        dev_list = list(dev_g)
        if dev_list is None:
            return None
        try:
            dev = dev_list[0]
        except:
            try:
                dev = dev_list.next()
            except:
                return None
        return dev

    def check_if_device_connected(self, force=False):
        self.dev = self.find_device()
        if self.dev is None:
            self.is_connected = False
            self.is_configured = False
            self.device_disconnected()
        else:
            self.is_connected = True
            self.device_connected()
            if force or not self.is_configured:
                self.config_device()

    def config_device(self):
        try:
            self.dev.reset()
        except:
            self.is_configured = False
            return
            pass
        try:
            self.dev.set_configuration()
        except usb.core.USBError:
            pass
        cfg = self.dev.get_active_configuration()
        intf = usb.util.find_descriptor(cfg, bInterfaceNumber=1)
        if not intf:
            raise print("Interface not found")
        if self.dev.is_kernel_driver_active(intf.bInterfaceNumber) is True:
            self.dev.detach_kernel_driver(intf.bInterfaceNumber)
        self.is_configured = True

    def closeEvent(self, event):
        # Confirm close
        reply = QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Tell worker to stop processing
            self.close = True
            # Wait for the worker to end
            self.threadpool.waitForDone()
            # Close app
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    app = QApplication(["Weather Station"])
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
