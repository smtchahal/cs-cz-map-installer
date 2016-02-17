"""
This module contains the frequently used QMessageBox classes.
"""

import sys
from PySide import QtGui
from PySide.QtGui import QMessageBox

class ErrorDialog(QMessageBox):
    """The error dialog"""

    def __init__(self, text):
        """Initialize the dialog with text"""
        super().__init__()

        #self.setGeometry(300, 300, 400, 300)
        self.setWindowTitle('Error')
        self.setIcon(QMessageBox.Critical)
        self.setText(text)
