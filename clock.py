import sys, os
import csv
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import *
import math
import time, datetime

import simpleaudio as sa

def printMinuteSecondDelta(delta):
    s = delta.total_seconds()

    if s>=0:
        return '{min:02d}:{sec:02d}'.format(min=int(s % 3600) // 60, sec=int(s % 60))
    else:
        s = -s
        return '-{min:02d}:{sec:02d}'.format(min=int(s % 3600) // 60, sec=int(s % 60))

labelFontCoeff = 15
countDownFontCoeff = 20
logoSizeCoeff = 5


class App(QWidget):
    def __init__(self, states):
        super().__init__()
        self.title = 'FPT clock'
        self.state = 0
        self.states = states

        self.setWindowTitle(self.title)
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor(255,255,255))
        self.setPalette(p)

        # Title of the state
        self.label = QLabel()
        self.label.setText(self.states[self.state]['name'])
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont('Arial', self.frameGeometry().height()/labelFontCoeff))

        self.c = None
        # Initialize the clock
        self.m = AnalogClock(self.states[self.state]['duration'], parent=self, sound=self.states[self.state]['sound'])
        self.m.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.m.show()

        # Right layout
        self.countDown = QLabel()
        self.countDown.setFont(QFont('Arial', self.frameGeometry().height()/countDownFontCoeff))

        self.rightLayout = QVBoxLayout()

        self.rightLayout.addWidget(self.label)
        self.rightLayout.addWidget(self.m)
        self.rightLayout.addWidget(self.countDown)

        # Left layout
        self.leftLayout = QVBoxLayout()
        self.logoSFP = QLabel()
        self.logoFPT = QLabel()

        if hasattr(sys, "_MEIPASS"):  # For PyInstaller
            SFPFile = os.path.join(sys._MEIPASS, 'SFP.png')
            FPTFile = os.path.join(sys._MEIPASS, 'LOGO.png')
        else:
            SFPFile = 'SFP.png'
            FPTFile = 'LOGO.png'

        self.pixmapSFP = QPixmap(SFPFile)
        self.logoSFP.setPixmap(self.pixmapSFP)
        self.logoSFP.setMinimumSize(1, 1)
        self.logoSFP.installEventFilter(self)

        self.pixmapFPT = QPixmap(FPTFile)
        self.logoFPT.setPixmap(self.pixmapSFP)
        self.logoFPT.setMinimumSize(1, 1)
        self.logoFPT.installEventFilter(self)

        self.logoSFP.setMinimumWidth(self.frameGeometry().width()/logoSizeCoeff)
        self.logoFPT.setMinimumWidth(self.frameGeometry().width()/logoSizeCoeff)

        self.leftLayout.addWidget(self.logoSFP)
        self.leftLayout.addWidget(self.logoFPT)

        # Complete layout
        self.fullLayout = QHBoxLayout()
        self.fullLayout.addLayout(self.leftLayout)
        self.fullLayout.addLayout(self.rightLayout)
        self.setLayout(self.fullLayout)

        self.childWindow = ClockControls(self)  # Clock controls
        self.childWindow.generateList(states)

        # Start at first event
        self.setEvent(0)

    def openClockWindow(self):
        if self.c==None:
            self.c = HelpClock(parent=self)
            self.c.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.c.show()
            self.c.countDown.setText("00:00")
            self.c.etape.setText(self.states[self.state]['name'])


    def eventFilter(self, source, event):
        if (source is self.logoSFP and event.type() == QEvent.Resize):
            # re-scale the pixmap when the label resizes
            self.logoSFP.setPixmap(self.pixmapSFP.scaled(
                self.logoSFP.size(), Qt.KeepAspectRatio,
                Qt.SmoothTransformation))
        if (source is self.logoFPT and event.type() == QEvent.Resize):
            # re-scale the pixmap when the label resizes
            self.logoFPT.setPixmap(self.pixmapFPT.scaled(
                self.logoFPT.size(), Qt.KeepAspectRatio,
                Qt.SmoothTransformation))
        return super(QWidget, self).eventFilter(source, event)


    def setEvent(self, i):
        if i<0:
            self.childWindow.end(0)
        elif i <= len(self.states) - 1:
            self.state = i
            print('Stepping to state {}'.format(
                self.states[self.state]['name']))

            self.m.reset(self.states[self.state]['duration'],sound=self.states[self.state]['sound'])

            # Change the label for the state name
            self.label.setText(self.states[self.state]['name'])
            if self.c!=None:
                self.c.etape.setText(self.states[self.state]['name'])
            # Update the list
            self.childWindow.list.setCurrentItem(self.childWindow.statesList[self.state])

            self.update()
        else:
            self.childWindow.end(0)
            #self.close()

    def stepEvent(self):
        i = self.state
        self.setEvent(i+1)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_N:
            self.stepEvent()
        if e.key() == Qt.Key_B:
            self.setEvent(self.state-1)
        if e.key() == Qt.Key_P:
            self.childWindow.switchPause()
        if e.key() == Qt.Key_M:
            self.m.addMinute()
        if e.key() == Qt.Key_R:
            self.m.addMinute(-1)
        if e.key() == Qt.Key_E:
            self.childWindow.end()
        if e.key() == Qt.Key_W:
            self.zeromove()

    def zeromove(self):
        self.move(0,0)
        self.childWindow.move(0,0)

    def resizeEvent(self, event):
        self.label.setFont(QFont('Arial', self.frameGeometry().height()/labelFontCoeff))
        self.countDown.setFont(QFont('Arial', self.frameGeometry().height()/countDownFontCoeff))

        self.logoSFP.setMinimumWidth(self.frameGeometry().width()/logoSizeCoeff)
        self.logoFPT.setMinimumWidth(self.frameGeometry().width()/logoSizeCoeff)


class AnalogClock(QWidget):

    def __init__(self, duration, parent=None,sound=0):
        super().__init__(parent)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(10)
        self.startPause = datetime.datetime.now()

        self.elapsedTimeClock = datetime.timedelta()
        self.datestart = datetime.datetime.now()

        self.duration = duration
        self.paused = True
        self.overtime = False

        self.sound = sound
        self.stimerOn = False
        self.stimer = sa.WaveObject.from_wave_file("timer.wav")
        self.stimerPlay = None

        self.parent = parent

        self.setMinimumSize(500, 500)

    def paintEvent(self, event):
        side = int(min(self.width(), self.height()) * 0.8 / 2)
        if not(self.paused):
            self.elapsedTimeClock = (datetime.datetime.now() - self.datestart)
        self.elapsedTime = self.elapsedTimeClock.total_seconds()

        if 9.5<(self.duration-self.elapsedTime)<10 and not self.stimerOn and self.sound:
            self.stimerOn = True
            self.stimerPlay = self.stimer.play()


        # Create and start a QPainter
        self.painter = QPainter()

        self.painter.begin(self)
        self.painter.setRenderHint(QPainter.Antialiasing)

        # Put the origin at the center
        self.painter.translate(self.width() / 2, self.height() / 2)

        # Setup pen and brush
        self.painter.setPen(Qt.NoPen)
        self.painter.setBrush(QColor(0, 200, 0))

        # Do the actual painting
        self.painter.save()
        currentAngle = - 2 * math.pi * self.elapsedTime / self.duration
        if not(abs(currentAngle) > 2 * math.pi):
            self.painter.drawPie(-side, -side, 2 * side, 2 * side, 90 * 16,
                                 currentAngle * (360 / (2 * math.pi)) * 16)

            tr = printMinuteSecondDelta(datetime.timedelta(seconds=self.duration) - self.elapsedTimeClock)
            self.parent.countDown.setText('Time remaining : ' + tr)
            self.parent.childWindow.countDown.setText(tr)
            if self.parent.c!=None:
                self.parent.c.countDown.setText(tr)

        elif 4 * math.pi > abs(currentAngle) > 2 * math.pi:
            self.overtime = True
            self.painter.drawPie(-side, -side, 2 * side,
                                 2 * side, 90 * 16, 360 * 16)
            self.painter.setBrush(QColor(200, 0, 0))
            self.painter.drawPie(-side, -side, 2 * side, 2 * side, 90 * 16,
                                 (currentAngle + 2 * math.pi) *
                                 (360 / (2 * math.pi)) * 16)

            tr = printMinuteSecondDelta(datetime.timedelta(seconds=self.duration) - self.elapsedTimeClock)
            self.parent.countDown.setText('Overtime : ' + tr)
            self.parent.childWindow.countDown.setText(tr)
            if self.parent.c != None:
                self.parent.c.countDown.setText(tr)
                self.parent.c.styleOvertime()


        else:
            self.painter.setBrush(QColor(200, 0, 0))
            self.painter.drawPie(-side, -side, 2 * side,
                                 2 * side, 90 * 16, 360 * 16)

            tr = printMinuteSecondDelta(datetime.timedelta(seconds=self.duration) - self.elapsedTimeClock)
            self.parent.countDown.setText('Overtime : ' + tr)
            self.parent.childWindow.countDown.setText(tr)
            if self.parent.c != None:
                self.parent.c.countDown.setText(tr)
                self.parent.c.styleOvertime()

        self.painter.setPen(QColor(0, 0, 0))
        self.painter.setBrush(Qt.NoBrush)
        self.painter.drawLine(QPoint(0, 0), QPoint(
            -side * math.cos(math.pi / 2 - currentAngle),
            -side * math.sin(math.pi / 2 - currentAngle)))
        self.painter.drawArc(-side, -side, 2 * side,
                             2 * side, 90 * 16, 360 * 16)
        self.painter.restore()

        self.painter.end()

    def switchPause(self,paused=None):
        if paused!=None: self.paused = not paused
        if self.paused:
            self.paused = False
            # Act as if there was no pause
            self.datestart += (datetime.datetime.now() - self.startPause)
        else:
            self.paused = True
            if self.stimerPlay != None: self.stimerPlay.stop()
            self.startPause = datetime.datetime.now()

    def reset(self, duration,sound=0):
        self.overtime = False
        self.duration = duration
        self.datestart = datetime.datetime.now()

        self.sound = sound
        if self.stimerPlay!=None: self.stimerPlay.stop()
        self.stimerPlay = None
        self.stimerOn = False

        if self.paused:
            self.startPause = datetime.datetime.now()

        self.elapsedTimeClock = datetime.timedelta()
        self.datestart = datetime.datetime.now()
        if self.parent.c != None:
            self.parent.c.styleNormal()

    def addMinute(self,min=1):
        self.duration += 60*min
        if self.duration<=0:
            self.duration += 60*abs(min)
            self.addMinute(min/2)
        else:
            if self.stimerPlay!=None: self.stimerPlay.stop()
            self.stimerPlay = None
            self.stimerOn = False


class ClockControls(QDialog):
    def __init__(self, parent,):
        QDialog.__init__(self, parent)#.WindowStaysOnTopHint)
        self.title = 'FPT clock controls'
        self.state = 0
        self.setWindowTitle(self.title)
        self.parent = parent

        self.countDown = QLabel()
        self.countDown.setFont(QFont('Arial', 20))
        self.countDown.setAlignment(Qt.AlignCenter)

        self.list = QListWidget()
        self.nextButton = QPushButton()
        self.nextButton.setText('Next (N)')
        self.pauseButton = QPushButton()
        self.pauseButton.setText('Start (P)')
        self.moreTime = QPushButton()
        self.moreTime.setText('Add 1 minute (M)')
        self.endButton = QPushButton()
        self.endButton.setText('Next and Stop (E)')
        self.clockWindow = QPushButton()
        self.clockWindow.setText('Help clock window')

        self.vLayout = QVBoxLayout()
        self.vLayout.addWidget(self.countDown)
        self.vLayout.addWidget(self.list)
        self.vLayout.addWidget(self.nextButton)
        self.vLayout.addWidget(self.pauseButton)
        self.vLayout.addWidget(self.moreTime)
        self.vLayout.addWidget(self.endButton)
        self.vLayout.addWidget(self.clockWindow)
        self.setLayout(self.vLayout)

        self.list.currentItemChanged.connect(self.changeState)
        self.pauseButton.clicked.connect(self.switchPause)
        self.nextButton.clicked.connect(self.parent.stepEvent)
        self.moreTime.clicked.connect(self.parent.m.addMinute)
        self.endButton.clicked.connect(self.end)
        self.clockWindow.clicked.connect(self.parent.openClockWindow)

    def generateList(self, states):
        self.statesList = []
        for state in states:
            item = QListWidgetItem('{} (duration : {} s)'.format(
                state['name'].replace('<br/>',''), state['duration']))
            self.statesList.append(item)
            self.list.addItem(item)

    def switchPause(self):
        if self.parent.m.paused:
            self.pauseButton.setText('Pause again (P)')
            if self.parent.c != None: self.parent.c.styleNormal()
        else:
            self.pauseButton.setText('Start again (P)')
            if self.parent.c != None: self.parent.c.stylePause()
        self.parent.m.switchPause()

    def end(self,state=None):
        self.pauseButton.setText('Start (P)')
        self.parent.m.switchPause(True)
        if state==None:
            self.parent.stepEvent()
        else:
            self.parent.setEvent(state)

    def changeState(self, curr):
        new_state = self.statesList.index(curr)
        self.parent.setEvent(new_state)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_N:
            self.parent.stepEvent()
        if e.key() == Qt.Key_B:
            self.parent.setEvent(self.parent.state-1)
        if e.key() == Qt.Key_P:
            self.switchPause()
        if e.key() == Qt.Key_M:
            self.parent.m.addMinute()
        if e.key() == Qt.Key_R:
            self.parent.m.addMinute(-1)
        if e.key() == Qt.Key_E:
            self.end()
        if e.key() == Qt.Key_W:
            self.parent.zeromove()

class HelpClock(QDialog):
    def __init__(self, parent,):
        QDialog.__init__(self, None)#,Qt.WindowStaysOnTopHint)


        self.title = 'Clock window'
        self.setWindowTitle(self.title)
        self.setFixedSize(180, 100)
        self.move(0,0)
        flags = Qt.WindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowFlags(flags)

        self.parent = parent

        self.countDown = QLabel()
        self.countDown.setFont(QFont('Arial', 20))

        self.countDown.setAlignment(Qt.AlignCenter)

        self.etape = QLabel()
        self.etape.setFont(QFont('Arial', 12))
        self.etape.setAlignment(Qt.AlignCenter)

        self.vLayout = QVBoxLayout()
        self.vLayout.addWidget(self.countDown)
        self.vLayout.addWidget(self.etape)
        self.setLayout(self.vLayout)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.oldPos)
        # print(delta)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()


    def keyPressEvent(self, e):
        if e.key() == Qt.Key_N:
            self.parent.stepEvent()
        if e.key() == Qt.Key_B:
            self.parent.setEvent(self.parent.state-1)
        if e.key() == Qt.Key_P:
            self.parent.childWindow.switchPause()
        if e.key() == Qt.Key_M:
            self.parent.m.addMinute()
        if e.key() == Qt.Key_R:
            self.parent.m.addMinute(-1)
        if e.key() == Qt.Key_E:
            self.parent.childWindow.end()
        if e.key() == Qt.Key_Q:
            self.parent.c = None
            self.close()

    def stylePause(self):
        self.countDown.setStyleSheet('font-weight: bold')

    def styleNormal(self):
        self.countDown.setStyleSheet('')

    def styleOvertime(self):
        self.countDown.setStyleSheet('font-weight: bold; color: red')

if __name__ == '__main__':
    if hasattr(sys, "_MEIPASS"):  # For PyInstaller
        statesFile = os.path.join(sys._MEIPASS, 'states.csv')
    else:
        statesFile = 'states.csv'

    states = []
    with open(statesFile, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in reader:
            states.append({'name': row[0], 'duration': int(row[1])*60, 'sound':int(row[2])})

    app = QApplication(sys.argv)
    ex = App(states)
    ex.show()
    ex.childWindow.show()
    sys.exit(app.exec_())
