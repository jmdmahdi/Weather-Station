import sys
import time
import traceback
import usb
import faulthandler
from PyQt5.QtChart import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from UI.mainWindow import Ui_MainWindow
from UI.compassWidget import CompassWidget
import signal
from db import sqlite3DB 
from datetime import datetime

signal.signal(signal.SIGINT, signal.SIG_DFL) # Force Close with ctrl+c

faulthandler.enable() # Properly show Qt faults 

# Define device USB IDs
idVendor = 5511
idProduct = 63322


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

        self.DB = sqlite3DB("weatherStation.db")

        self.close = False
        self.is_connected = False
        self.is_configured = False
        self.dev = None
        self.status = "checking"
        self.USBString = ""

        self.window = Ui_MainWindow()
        self.window.setupUi(self)
        
        self.window.textBrowser.setReadOnly(True)
        self.window.textBrowser.setCursorWidth(0)
        
        self.compass = CompassWidget()
        self.window.compassLayout.addWidget(self.compass)
        
        # Restore last time window geometry
        self.settings = QSettings('JMDMahdi', 'WeatherStation')
        geometry = self.settings.value('geometry', '')
        if isinstance(geometry, QByteArray):
            self.restoreGeometry(geometry)

        # Update the home tab with last received data
        self.updateHomeTab()

        series = QLineSeries()
        series.append(0, 6)
        series.append(2, 4)
        series.append(3, 8)
        series.append(7, 4)
        series.append(10, 5)
        
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Temperature records in celcius")

        chart.createDefaultAxes()
        chart.axisX(series).setTitleText("time")
        chart.axisY(series).setTitleText("Temperature")
        
        chart.legend().setVisible(False)
        
        chartView = QChartView(chart)
        chartView.setRenderHint(QPainter.Antialiasing)
        chartView.setMinimumSize(300, 300)
        self.window.chartTabContents.addWidget(chartView)
        
        series = QLineSeries()
        series.append(0, 9)
        series.append(2, 5)
        series.append(3, 8)
        series.append(7, 4)
        series.append(10, 5)
        
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Temperature records in celcius")

        chart.createDefaultAxes()
        chart.axisX(series).setTitleText("time")
        chart.axisY(series).setTitleText("Temperature")
        
        chart.legend().setVisible(False)
        
        chartView = QChartView(chart)
        chartView.setRenderHint(QPainter.Antialiasing)
        chartView.setMinimumSize(300, 300)
        self.window.chartTabContents.addWidget(chartView)
        
        
        self.window.chartTabScrollArea.setWindowFlags(Qt.FramelessWindowHint)
        self.window.chartTabScrollArea.setAttribute(Qt.WA_TranslucentBackground)
        self.window.chartTabScrollArea.setStyleSheet("background:transparent;")
        
	# check device connection status before showing window
        self.check_if_device_connected()

        self.threadpool = QThreadPool()
        # Pass the function to execute
        self.worker = Worker(self.execute_this_fn)  # Any other args, kwargs are passed to the run function
        self.worker.signals.progress.connect(self.progress_fn)

        # Execute
        self.threadpool.start(self.worker)

    def progress_fn(self, data):
        # Fill USBString with received data 
        if data.startswith("["):
            # It is string start
            self.USBString = data
        else:
            # It is rest of data
            self.USBString += data
        # IF hole string received proccess and insert new data
        if self.USBString.startswith("[") and self.USBString.endswith("]"):
            # Remove completed data indicators from string and pass into insertData function, to insert to db
            self.insertData(self.USBString.strip("[").strip("]"))

    def execute_this_fn(self, progress_callback):
        while True:
            if self.close:
                return
            if self.is_connected:
                try:
                    result = self.dev.read(0x81, 64, 60000)
                    progress_callback.emit(result.tobytes().decode('utf-8', errors="ignore"))
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
        reply = QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
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

    def updateHomeTab(self):
        '''Update the home tab with last received data'''
        # Get last data
        lastData = self.DB.getLastRow()
        # Fill lastData with 0 if data not available
        if lastData is None:
            lastData = (0, 0, 0, 0, 0, 0, 0)
        
        # Convert timestamp to datetime
        date = datetime.fromtimestamp((lastData[6]))
        
        # Update home tab with last data
        self.window.temperatureText.setText(str(lastData[0]) + " °C")
        self.window.pressureText.setText(str(lastData[1]) + " hPa")
        self.window.lightIntensityText.setText(str(lastData[2]) + " lux")
        self.window.humidityText.setText(str(lastData[3]) + " %")
        self.window.windSpeedText.setText(str(lastData[4]) + " m/s")
        self.compass.setAngle(lastData[5])
        self.window.windAngleText.setText(str(lastData[5]) + " °")
        self.window.dateText.setText(date.strftime("%A, %-d %B %Y"))
        self.window.timeText.setText(date.strftime("%I:%M %p"))        
        
    def insertData(self, data):
        self.writeLog("Received data: " + data + " | Status: ")
        data_list = data.split(',')
        if len(data_list) == 8:
            self.DB.insert(data_list)
            self.writeLog("Successfully inserted to db\n")
            self.updateHomeTab()
        else: 
            self.writeLog("Invalid data\n")
        
    def writeLog(self, text):
        self.window.textBrowser.moveCursor(QTextCursor.End)
        self.window.textBrowser.insertPlainText(text)
        if self.window.checkBox.isChecked():
            self.window.textBrowser.verticalScrollBar().setValue(self.window.textBrowser.verticalScrollBar().maximum())
        
        
if __name__ == "__main__":
    app = QApplication(["Weather Station"])
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
