"""
This module contains the MainWindow class responsible for rendering
the main window of the application.
"""

import sys
import os
import logging

from PySide import QtGui
from PySide.QtGui import QMessageBox

from .dialogs import ErrorDialog
from . import mapinstaller

LOGGING_FORMAT = ("[%(asctime)s] %(levelname)s "
                "[%(name)s.%(funcName)s:%(lineno)d] %(message)s")
logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)

class MainWindow(QtGui.QMainWindow):
    """
    The MainWindow class, responsible for rendering the main window of the
    application
    """

    def __init__(self):
        """Initialize class"""
        super().__init__()

        self.appname = QtGui.QApplication.applicationName()
        self.initUI()

    def initUI(self):
        """Set up the window"""
        self.createMenus()
        centralWidget = QtGui.QWidget()

        mapPath = QtGui.QLabel('Map folder:')
        self.mapPathEdit = QtGui.QLineEdit()
        mapPathButton = QtGui.QPushButton('Select')
        mapPathButton.clicked.connect(self.mapPathSelect)

        gamePath = QtGui.QLabel('Game path:')
        self.gamePathEdit = QtGui.QLineEdit()
        gamePathButton = QtGui.QPushButton('Select')
        gamePathButton.clicked.connect(self.gamePathSelect)

        game = QtGui.QLabel('Game:')
        self.gameDropDown = QtGui.QComboBox()
        self.gameDropDown.addItem('Condition Zero')
        self.gameDropDown.addItem('Counter Strike')

        installButton = QtGui.QPushButton('&Install map')
        installButton.clicked.connect(self.installAction)

        layout = QtGui.QGridLayout()
        layout.setSpacing(10)

        layout.addWidget(mapPath, 0, 0)
        layout.addWidget(self.mapPathEdit, 0, 1)
        layout.addWidget(mapPathButton, 0, 2)

        layout.addWidget(gamePath, 1, 0)
        layout.addWidget(self.gamePathEdit, 1, 1)
        layout.addWidget(gamePathButton, 1, 2)

        layout.addWidget(game, 2, 0)
        layout.addWidget(self.gameDropDown, 2, 1)
        layout.addWidget(installButton, 2, 2)

        centralWidget.setLayout(layout)

        self.prefillPaths()
        self.setCentralWidget(centralWidget)
        self.setFixedSize(500, 0)
        self.setWindowTitle(self.appname)
        self.show()

    def installMapProgress(self, mapPath, gamePath, gameType, replace=False):
        """Install map, showing a dialog box when finished"""
        try:
            mapinstaller.install_map(mapPath, gamePath, gameType, replace=replace)
            self.dialog = QMessageBox()
            self.dialog.setIcon(QMessageBox.Information)
            self.dialog.setWindowTitle('Success')
            self.dialog.setText('Installing map finished successfully.')
            self.dialog.exec_()
        except mapinstaller.SameDirectoryError:
            self.dialog = ErrorDialog('Entered map path and game path refer'
                ' to the same directory.')
            self.dialog.exec_()
        except mapinstaller.InvalidGameDirectoryError:
            self.dialog = ErrorDialog(('Given game directory is not a valid {0}'
            ' installation ("{0}" not found).').format(gameType))
            self.dialog.exec_()
        except mapinstaller.InvalidMapDirectoryError:
            self.dialog = ErrorDialog('Invalid map directory.')
            self.dialog.exec_()
        except PermissionError:
            self.dialog = ErrorDialog('No permission to write to {} directory,'
                    ' did you run the application as administrator?'.format(gameType))
            self.dialog.exec_()
        except Exception as e:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            logging.exception('Uncaught exception occured')
            self.dialog = ErrorDialog(message)
            self.dialog.exec_()

    def installAction(self):
        """The handler for the "Install Map" click button"""
        gamePath = self.gamePathEdit.text()
        mapPath = self.mapPathEdit.text()
        game = self.gameDropDown.currentText()
        gameIndex = self.gameDropDown.currentIndex()

        gameType = 'czero'
        if gameIndex == 0:
            gameType = 'czero'
        elif gameIndex == 1:
            gameType = 'cstrike'

        if not os.path.isdir(gamePath) or not os.path.isdir(mapPath):
            self.dialog = ErrorDialog('Please enter a valid directory path')
            self.dialog.exec_()
            return

        try:
            comparison = mapinstaller.compare_dirs(mapPath, gamePath, gameType)
            if comparison is not None:
                file1 = comparison[0]
                file2 = comparison[1]

                self.dialog = QMessageBox()

                replaceButton = self.dialog.addButton('Replace',
                    QMessageBox.YesRole)
                skipButton = self.dialog.addButton('Skip',
                    QMessageBox.NoRole)
                cancelButton = self.dialog.addButton(QMessageBox.Cancel)
                self.dialog.setIcon(QMessageBox.Question)
                self.dialog.setWindowTitle('Replace files?')
                text = ('Some files in {0} overlap with files in {1}'
                        '\nDo you want to replace these files in {0}'
                        ' or skip them?')
                self.dialog.setText(text.format(gamePath, mapPath))
                self.dialog.exec_()
                clicked = self.dialog.clickedButton()
                if clicked == replaceButton:
                    self.installMapProgress(mapPath, gamePath, gameType,
                        replace=True)
                elif clicked == skipButton:
                    self.installMapProgress(mapPath, gamePath, gameType)
                elif clicked == cancelButton:
                    self.dialog = QMessageBox()
                    self.dialog.setIcon(QMessageBox.Warning)
                    self.dialog.setWindowTitle('Canceled')
                    self.dialog.setText('Operation canceled')
                    self.dialog.exec_()
                    return
            else:
                self.installMapProgress(mapPath, gamePath, gameType)
        except mapinstaller.SameDirectoryError:
            self.dialog = ErrorDialog('Entered map path and game path refer'
                ' to the same directory.')
            self.dialog.exec_()

    def prefillPaths(self):
        """
        Pre-fill gamePath and mapPath with values found from
        mapinstaller.get_game_path()
        """
        if sys.platform.startswith('linux') or sys.platform == 'darwin':
            # Linux and OS/X
            home = os.path.expanduser('~')
            paths = (home + '/.wine/drive_c/Program Files (x86)',
                    home + '/.wine/drive_c/Program Files',
                    home)
            self.mapPathEdit.setText(home)
            self.gamePathEdit.setText(mapinstaller.get_game_path(paths) or '')

        elif sys.platform == 'win32':
            # Windows
            drives = mapinstaller.get_win_drives()
            paths = []
            for drive in drives:
                paths.append(drive + r'\Program Files (x86)')
                paths.append(drive + r'\Program Files')
                paths.append(drive)
            self.mapPathEdit.setText(drives[0] + '\\')
            self.gamePathEdit.setText(mapinstaller.get_game_path(paths) or '')

    def mapPathSelect(self):
        """Handle click on Select Map Path button"""
        directoryPath = QtGui.QFileDialog.getExistingDirectory(self,
            'Select map directory', self.mapPathEdit.text())
        if directoryPath:
            self.mapPathEdit.setText(directoryPath)

    def gamePathSelect(self):
        """Handle click on Select Game Path button"""
        directoryPath = QtGui.QFileDialog.getExistingDirectory(self,
            'Select game directory', self.gamePathEdit.text())
        if directoryPath:
            self.gamePathEdit.setText(directoryPath)

    def createMenus(self):
        """Create menus in MainWindow"""
        # Create menubar
        menubar = self.menuBar()

        # Actions
        exitAction = QtGui.QAction('&Exit', self)
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        aboutAction = QtGui.QAction('&About ' + self.appname, self)
        aboutAction.setStatusTip('About ' + self.appname)
        aboutAction.triggered.connect(self.launchAboutDialog)

        # Menus
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)

        helpMenu = menubar.addMenu('&Help')
        helpMenu.addAction(aboutAction)

    def launchAboutDialog(self):
        """Launch the About dialog"""
        appName = QtGui.QApplication.applicationName()
        appVersion = QtGui.QApplication.applicationVersion()
        title = 'About {}'.format(appName)
        text = '''<p style="font-size: 16px; font-weight: bold;">
                {0}
                </p>
                <p>Version {1}</p>
                <p>
                {0} was made by
                <a href="https://github.com/smtchahal">Sumit Chahal</a>.
                It is available under the MIT License (see
                <a
                href="https://github.com/smtchahal/cs-cz-map-installer/blob/master/LICENSE">full
                licensing terms</a>). Source code is available on
                <a
                href="https://github.com/smtchahal/cs-cz-map-installer">GitHub</a>.
                </p>
                <p>
                {0} uses <a
                href="https://pypi.python.org/pypi/PySide/1.2.4">PySide
                1.2.4</a>.
                '''.format(appName, appVersion)
        QMessageBox.about(self, title, text)
        #self.dialog = AboutDialog()
        #self.dialog.exec_()
