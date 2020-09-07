from PyQt5.QtChart import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class chartWidget(QChartView):
    seriesChanged = pyqtSignal(QLineSeries)

    def __init__(self, parent=None, title=None, XTitle=None, yTitle=None):
        QChartView.__init__(self, parent)

        self.XTitle = XTitle
        self.YTitle = yTitle

        self.old_series = None
        self.axisX = None
        self.axisY = None
        self._series = QLineSeries()

        self._chart = QChart()
        
        self._chart.setAnimationOptions(QChart.SeriesAnimations)
        self._chart.legend().setVisible(False)
        
        self._chart.addSeries(self._series)
        
        self.updateSeries()

        self._chart.setTitle(title)

        self.setChart(self._chart)
        self.setRenderHint(QPainter.Antialiasing)
        self.setMinimumSize(300, 300)

    def update(self, *__args):
        if self.old_series is not None:
            self._chart.removeSeries(self.old_series)
        self._chart.addSeries(self._series)
        self.updateSeries()

    def updateSeries(self):
        if self.axisX is not None:
            self._chart.removeAxis(self.axisX)
        self.axisX = QDateTimeAxis()
        self.axisX.setTickCount(self.calculateTick())
        self.axisX.setFormat("d MMMM hh:mm")
        self.axisX.setTitleText(self.XTitle)
        self._chart.addAxis(self.axisX, Qt.AlignBottom)
        
        if self.axisY is not None:
            self._chart.removeAxis(self.axisY)
        self.axisY = QValueAxis()
        self.axisY.setLabelFormat("%i")
        self.axisY.setTitleText(self.YTitle)
        self._chart.addAxis(self.axisY, Qt.AlignLeft)
        
        self._series.attachAxis(self.axisX)
        self._series.attachAxis(self.axisY)

    def series(self):
        return self._series

    def resizeEvent(self, event):
        self.updateSeries()
        QChartView.resizeEvent(self, event)

    def calculateTick(self):
        width = self.frameGeometry().width()
        return int(round((width * 3) / 376))
        
    @pyqtSlot(QLineSeries)
    def setSeries(self, series):
        self.old_series = self._series
        self._series = series
        self.seriesChanged.emit(series)
        self.update()

    series = pyqtProperty(QLineSeries, series, setSeries)
