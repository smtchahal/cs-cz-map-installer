import sys

from PySide import QtGui

from .mainwindow import MainWindow

QtGui.QApplication.setApplicationName('CS:CZ Map Installer')
QtGui.QApplication.setApplicationVersion('0.1.1')

def run():
    app = QtGui.QApplication(sys.argv)
    ex = MainWindow()
    return app.exec_()
