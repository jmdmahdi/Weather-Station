import sys, signal, platform, time, usb, faulthandler
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtChart import *
from PyQt5.QtWidgets import *
from UI.mainWindow import Ui_MainWindow
from UI.compassWidget import compassWidget
from UI.chartWidget import chartWidget
from DB.db import sqlite3DB
from datetime import datetime, timedelta
from Worker.worker import Worker
from Worker.signalWakeupHandler import SignalWakeupHandler
import usb.backend.libusb1
import numpy as np

backend = usb.backend.libusb1.get_backend(find_library=lambda x: "libusb-1.0.dll")

# Properly show Qt faults
faulthandler.enable()

# Define global variables
_CloseApp = False


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        # Define DB instance
        self.DB = sqlite3DB("DB/weatherStation.db")
        # Define properties
        self.is_connected = False
        self.is_configured = False
        self.dev = None
        self.status = "checking"
        self.USBString = ""

        # Define main ui
        self.window = Ui_MainWindow()
        self.window.setupUi(self)

        # Set log textBrowser as read only
        self.window.textBrowser.setReadOnly(True)
        self.window.textBrowser.setCursorWidth(0)
        # Generate compass widget
        self.compass = compassWidget()
        self.window.compassLayout.addWidget(self.compass)

        # Restore last time window geometry
        self.settings = QSettings('JMDMahdi', 'WeatherStation')
        geometry = self.settings.value('geometry', '')
        if isinstance(geometry, QByteArray):
            self.restoreGeometry(geometry)

        # Update the home tab with last received data
        self.updateHomeTab()

        # Define chart tab charts and add them to view
        self.generateCharts()

	# Set default statusbar text
        self.window.statusbar.showMessage('Checking ...')

        # Build background thread for USB
        self.threadpool = QThreadPool()

        # Pass the function to execute in background
        self.worker = Worker(self.USB_process)
        self.worker.signals.progress.connect(self.processData)
        self.worker.signals.statusbar.connect(self.updateStatusBar)

        # Execute
        self.threadpool.start(self.worker)

    def processData(self, data):
        # Remove completed data indicators from string and pass into insertData function, to insert to db
        self.insertData(data)

    def USB_process(self, process_callback, UIUpdateCallBack):
        global _CloseApp
        # Check device status continuously
        while True:
            if _CloseApp:  # End thread on close signal
                # Close UI
                QApplication.quit()
                return
            if self.is_connected:
                # Wait for data from device 
                try:
                    # Get USB data and pass to main thread to process
                    data = self.dev.read(0x81, 32, 2000)
                    # Convert data to uint8 array
                    dataBytes = np.array(data.tolist(), dtype=np.uint8)
                    # Convert data to float list
                    process_callback.emit(dataBytes.view(dtype=np.float32).tolist())
                except Exception as e:
                    if not ("Operation timed out" in str(e) or "Pipe error" in str(e) or "Input/Output Error" in str(e) or "No such device" in str(e)):
                        print("self.dev.read error: " + str(e))
                    # Recheck device status
                    self.check_if_device_connected(UIUpdateCallBack, True)
                    time.sleep(1)
                    pass
            else:
                # Recheck device status every 1 secound if device not connected
                time.sleep(1)
                UIUpdateCallBack.emit(self.is_connected)
                self.check_if_device_connected(UIUpdateCallBack, True)

    def device_connected(self):
        # Set device status on UI as connected
        if self.status != "connected":
            self.writeLog("Device connected\n")
            self.window.statusbar.showMessage('Connected')
            self.window.statusbar.setStyleSheet('color: green')
            self.status = "connected"

    def device_disconnected(self):
        # Set device status on UI as disconnected
        if self.status != "disconnected":
            self.writeLog("Device disconnected\n")
            self.window.statusbar.showMessage('Disconnected')
            self.window.statusbar.setStyleSheet('color: red')
            self.status = "disconnected"

    def updateStatusBar(self, status):
        if status:
            self.device_connected()
        else:
            self.device_disconnected()

    def find_device(self):
        # Search connected device for our device and return device descriptor
        dev_g = usb.core.find(backend=backend, idVendor=5511, idProduct=63322, find_all=True)
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

    def check_if_device_connected(self, UIUpdateCallBack, force=False):
        # Search for our device
        self.dev = self.find_device()
        if self.dev is None:
            self.is_connected = False
            self.is_configured = False
        else:
            self.is_connected = True
            # Gain access to read the device if not done already
            if force or not self.is_configured:
                # This must be done on every connection
                self.config_device()
        # Set status on UI
        UIUpdateCallBack.emit(self.is_connected)

    def config_device(self):
        # Gain access to device
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
            raise("Interface not found")
        if platform.system() != "Windows":
            if self.dev.is_kernel_driver_active(intf.bInterfaceNumber) is True:
                self.dev.detach_kernel_driver(intf.bInterfaceNumber)
        self.is_configured = True

    def closeEvent(self, event):
        global _CloseApp
        # Confirm close
        reply = QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Save window geometry to restore next time
            self.settings.setValue('geometry', self.saveGeometry())
            # Tell worker to stop processing
            _CloseApp = True
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
        self.window.pressureText.setText(str(lastData[1] / 100) + " hPa")
        self.window.lightIntensityText.setText(str(lastData[2]) + " lux")
        self.window.humidityText.setText(str(lastData[3]) + " %")
        self.window.windSpeedText.setText(str(lastData[4]) + " m/s")
        self.compass.setAngle(int(lastData[5]))
        self.window.windAngleText.setText(str(lastData[5]) + " °")
        if platform.system() != "Windows":
            self.window.dateText.setText(date.strftime("%A, %-d %B %Y"))
        else:
            self.window.dateText.setText(date.strftime("%A, %e %B %Y"))
        self.window.timeText.setText(date.strftime("%I:%M %p"))

    def insertData(self, data):
        self.writeLog("Received data: " + " ,".join(map(str, data)) + " | Status: ")
        if len(data) == 8:
            self.DB.insert(data)
            self.writeLog("Successfully inserted to db\n", False)
            self.updateHomeTab()
        else:
            self.writeLog("Invalid data\n", False)

    def writeLog(self, text, insertTime=True):
        self.window.textBrowser.moveCursor(QTextCursor.End)
        if insertTime:
            self.window.textBrowser.insertPlainText(datetime.now().strftime("%a %b %d %H:%M:%S.%f %Y") + "> ")
        self.window.textBrowser.insertPlainText(text)
        if self.window.checkBox.isChecked():
            self.window.textBrowser.verticalScrollBar().setValue(self.window.textBrowser.verticalScrollBar().maximum())

    def generateCharts(self):
        # Add chart widgets
        self.temperatureChart = chartWidget(None, "Temperature records in celcius", "Time", "Temperature")
        self.window.chartTabContents.addWidget(self.temperatureChart)
        self.pressureChart = chartWidget(None, "Pressure records in Pa", "Time", "Pressure")
        self.window.chartTabContents.addWidget(self.pressureChart)
        self.LightIntensityChart = chartWidget(None, "Light intensity records in lux", "Time", "Light intensity")
        self.window.chartTabContents.addWidget(self.LightIntensityChart)
        self.humidityChart = chartWidget(None, "Humidity records in percent", "Time", "Humidity")
        self.window.chartTabContents.addWidget(self.humidityChart)
        self.windSpeedChart = chartWidget(None, "Wind speed records in m/s", "Time", "Wind speed")
        self.window.chartTabContents.addWidget(self.windSpeedChart)
        # Update dateEdits date 
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        self.window.firstDate.setDate(week_ago.date())
        self.window.secondDate.setDate(today.date())
        # Call updateCharts on date changes
        self.window.firstDate.dateChanged.connect(self.updateCharts)
        self.window.secondDate.dateChanged.connect(self.updateCharts)
        # Update charts series from db
        self.updateCharts()

    def updateCharts(self):
        # Get dates
        secondDate = self.window.secondDate.date().toPyDate()
        firstDate = self.window.firstDate.date().toPyDate()
        # Generate start and end date based on dates
        if firstDate < secondDate:
            startDate = datetime.combine(firstDate, datetime.min.time())
            endDate = datetime.combine(secondDate, datetime.max.time())
        else:
            endDate = datetime.combine(firstDate, datetime.max.time())
            startDate = datetime.combine(secondDate, datetime.min.time())
        # Get rows between start and end date
        rows = self.DB.getDataBetween(startDate.timestamp(), endDate.timestamp())
        # define QLineSeries instants
        temperatureSeries = QLineSeries()
        pressureSeries = QLineSeries()
        LightIntensitySeries = QLineSeries()
        humiditySeries = QLineSeries()
        windSpeedSeries = QLineSeries()
        # Fill series with db data
        for row in rows:
            temperatureSeries.append(int(row[6] * 1000), row[0])
            pressureSeries.append(int(row[6] * 1000), row[1])
            LightIntensitySeries.append(int(row[6] * 1000), row[2])
            humiditySeries.append(int(row[6] * 1000), row[3])
            windSpeedSeries.append(int(row[6] * 1000), row[4])
        # Update series with new ones
        self.temperatureChart.setSeries(temperatureSeries)
        self.pressureChart.setSeries(pressureSeries)
        self.LightIntensityChart.setSeries(LightIntensitySeries)
        self.humidityChart.setSeries(humiditySeries)
        self.windSpeedChart.setSeries(windSpeedSeries)


def closeApp(sig, frame=None):
    global _CloseApp
    # Ignore additional signals
    signal.signal(sig, signal.SIG_IGN)
    # Tell background process to stop
    _CloseApp = True
    print("\rClosing app ...")


if __name__ == "__main__":
    # Force Close with ctrl+c
    signal.signal(signal.SIGINT, closeApp)
    # Force Close on terminal close
    signal.signal(signal.SIGTERM, closeApp)
    # Start UI
    app = QApplication(["Weather Station"])
    SignalWakeupHandler(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
