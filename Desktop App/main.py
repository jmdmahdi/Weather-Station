import sys
import time
import traceback
import usb
import faulthandler
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from UI.main_window import Ui_MainWindow
from UI.compass import CompassWidget
import signal

signal.signal(signal.SIGINT, signal.SIG_DFL) # Force Close with ctrl+c

faulthandler.enable() # Properly show Qt faults 

# Define device USB IDs
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
        self.status = "checking"

        self.window = Ui_MainWindow()
        self.window.setupUi(self)
        
        self.compass = CompassWidget()
        self.window.compassLayout.addWidget(self.compass)
        
        # Restore last time window geometry
        self.settings = QSettings('JMDMahdi', 'WeatherStation')
        geometry = self.settings.value('geometry', '')
        if isinstance(geometry, QByteArray):
            self.restoreGeometry(geometry)

        self.setWindAngle(10)
        self.setWindSpeed(4)
        self.setTemperature(26)
        self.setLightIntensity(100)
        self.setHumidity(60)
        self.setPressure(800)
        self.setDate("Sunday, August 30, 2020")
        self.setTime("22:30:45")

	# check device connection status before showing window
        self.check_if_device_connected()

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
        if self.status != "connected":
            self.window.statusbar.showMessage('Connected')
            self.window.statusbar.setStyleSheet('color: green')
            self.status = "connected"

    def device_disconnected(self):
        if self.status != "disconnected":
            self.window.statusbar.showMessage('Disconnected')
            self.window.statusbar.setStyleSheet('color: red')
            self.status = "disconnected"

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
            # Save window geometry to restore next time
            self.settings.setValue('geometry', self.saveGeometry())
            # Tell worker to stop processing
            self.close = True
            # Wait for the worker to end
            self.threadpool.waitForDone()
            # Close app
            event.accept()
        else:
            event.ignore()
            
    def setWindAngle(self, angle):
        self.compass.setAngle(angle)
        self.window.windAngleText.setText(str(angle) + " °")

    def setWindSpeed(self, speed):
        self.window.windSpeedText.setText(str(speed) + " m/s")

    def setTemperature(self, temperature):
        self.window.temperatureText.setText(str(temperature) + " °C")

    def setLightIntensity(self, lightIntensity):
        self.window.lightIntensityText.setText(str(lightIntensity) + " lux")

    def setHumidity(self, humidity):
        self.window.humidityText.setText(str(humidity) + " %")

    def setPressure(self, pressure):
        self.window.pressureText.setText(str(pressure) + " hPa")

    def setDate(self, date):
        self.window.dateText.setText(str(date))

    def setTime(self, time):
        self.window.timeText.setText(str(time))        
        
        
        
if __name__ == "__main__":
    app = QApplication(["Weather Station"])
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
