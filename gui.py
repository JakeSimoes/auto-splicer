import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QGridLayout, QWidget, QListWidget, QPushButton, QAction, QLineEdit, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Auto Splicer Ver. 0.01")
        app.setStyle("Windows")
        layout = QGridLayout()
        self.fileButton = QPushButton("File")
        layout.addWidget(self.fileButton, 0, 0)
        self.keysButton = QPushButton("Keys")
        layout.addWidget(self.keysButton, 1, 0)
        self.wordBankList = QListWidget()
        self.wordBankList.addItem("Lol")
        layout.addWidget(self.wordBankList, 0, 1)
        self.wordInput = QLineEdit("Hello World")
        layout.addWidget(self.wordInput, 1, 1)
        self.playButton = QPushButton("Play")
        layout.addWidget(self.playButton, 1, 2)


        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.show()


    @pyqtSlot()
    def on_click(self):
        textboxValue = self.textbox.text()
        QMessageBox.question(self, 'Message - pythonspot.com', "You typed: " + textboxValue, QMessageBox.Ok,
                             QMessageBox.Ok)
        self.textbox.setText("")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
