# This Python file uses the following encoding: utf-8
import sys
import pandas as pd
import json
from time import sleep
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, \
                            QPushButton, QItemDelegate, QVBoxLayout, QTextEdit, QProgressBar, QHBoxLayout, QLabel, QTextBrowser,\
                                QFileDialog
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QDoubleValidator, QIcon

import BackEndEngine



class FloatDelegate(QItemDelegate):
    def __init__(self, parent=None):
        super().__init__()

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QDoubleValidator())
        return editor

class TableWidget(QTableWidget):
    def __init__(self, df):
        super().__init__()
        self.df = df
        self.setStyleSheet('font-size: 16px;')
        

        # set table dimension
        nRows, nColumns = self.df.shape
        self.setColumnCount(nColumns)
        self.setRowCount(nRows)

        self.setHorizontalHeaderLabels(list(self.df.columns.values))
        self.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    

        self.setSortingEnabled(True)
        self.setItemDelegateForColumn(1, FloatDelegate())

        # data insertion
        for i in range(self.rowCount()):
            for j in range(self.columnCount()):
                self.setItem(i, j, QTableWidgetItem(str(self.df.iloc[i, j])))

        self.cellChanged[int, int].connect(self.updateDF)  

    

    def updateDF(self, row, column):
        print(self.item(row, column), self.item(row, column).text())
        text = self.item(row, column).text()
        self.df.iloc[row, column] = text

class DFEditorWidget(QWidget):
    column_fill_mode = False

    def __init__(self):
        
        super().__init__()
        self.resize(1200, 800)

    def updateDF(self,df):
        self.__DF = df
        self.mainLayout = QVBoxLayout()

        self.table = TableWidget(self.__DF)
        self.mainLayout.addWidget(self.table)

        self.button_export = QPushButton('Export to CSV file')
        self.button_export.setStyleSheet('font-size: 24px')
        self.button_export.clicked.connect(self.export_to_csv)
        self.mainLayout.addWidget(self.button_export)     

        self.setLayout(self.mainLayout)
    
        

    def export_to_csv(self):
        name = QFileDialog.getSaveFileName(self, 'Save CSV', filter='*.csv')
        if(name[0] == ''):
            pass
        else:
            self.table.df.to_csv(name[0], index=False)
        print('CSV file exported.')













class TrainWorker(QObject):
    finished = pyqtSignal()
    def setToken(self,token):
        self.token = token
    def run(self):
        self.data = BackEndEngine.BackEndEngine(self.token).getTrainedDF()
        print("Train Finished")
        self.finished.emit()

    

class TestTrainWorker(QObject):
    finished = pyqtSignal()
    def setToken(self,token):
        self.token = token
    def run(self):
        self.data = BackEndEngine.BackEndEngine(self.token).getTestTrainedDF()        
        print("Test Train Finished")
        self.finished.emit()













class TokenInputWidget(QWidget):
    table_viewer = None
    task_ended = False 
    fun_signal = pyqtSignal()

    mainlayout = None
    token_input_box = None
    token_box_layout = None
    loading_bar = None
    button_execute = None
    

    def __setUIEnabling(self,input = False):
        self.token_input_box.setEnabled(input)
        self.button_execute.setEnabled(input)
        self.button_test.setEnabled(input)
        self.loading_bar.setVisible(not(input))
     

    def __init__(self):
        super().__init__()
        self.resize(720,200)

        
        self.mainlayout = QVBoxLayout()
        self.token_input_box = QTextEdit()
        self.token_box_layout = QHBoxLayout()
        self.button_box_layout = QVBoxLayout()
        self.loading_bar = QProgressBar()
        self.button_execute = QPushButton('Start Training')
        self.token_label = QLabel("Facebook Graph API Access Token / Long-Lived Token: ")
        self.button_test = QPushButton('Test With Scraped Data')
        self.message_label = QLabel("Message: ")
        self.message = QTextBrowser()
        
        # Set LoadingBar Properties
        self.loading_bar.setStyleSheet('''
            QProgressBar::chunk{
                background-color: #F44336;
                

            }
            QProgressBar{
                border: 2px solid #F44336;
                background-color: #222324
            }
        ''')
        self.loading_bar.setMaximum(0)
        self.loading_bar.setMinimum(0)
        self.loading_bar.setValue(0)
    
        
        
        self.loading_bar.setVisible(False)

        # Add QLabel:
        
        self.mainlayout.addWidget(self.token_label)
        # Token Input Text Edit Box
        
        self.token_box_layout.addWidget(self.token_input_box)

        # Add Start Training Button
        self.button_execute.setStyleSheet('font-size: 16px')
        self.button_execute.clicked.connect(self.train)
        self.button_box_layout.addWidget(self.button_execute)

        self.button_test.setStyleSheet('font-size: 16px')
        self.button_test.clicked.connect(self.test_train)
        self.button_box_layout.addWidget(self.button_test)

        # Add All subLayout  to mainlayout
        self.token_box_layout.addLayout(self.button_box_layout)
        self.mainlayout.addLayout(self.token_box_layout)

        # Add TextBrowser Box to display terminal output
        
        self.mainlayout.addWidget(self.loading_bar)
        self.mainlayout.addWidget(self.message_label)
        self.mainlayout.addWidget(self.message)

        self.setLayout(self.mainlayout)



        
    # mode 1: train; mode 0: test train
    def train(self):
        self.__setUIEnabling(False)
        self.message.setText("Training ...")
        self.doTrain(mode=1)
    def test_train(self):
        self.__setUIEnabling(False)
        self.message.setText("Training test-dataset...")
        self.doTrain(mode=0)
        
        
        
    def trainingAftermath(self,data):
        print("Type: data", type(data))
        if(type(data) is list):
            self.__setUIEnabling(True)
            self.message.setText(json.dumps(data[0], indent = 4))
        else:
            self.table_viewer.updateDF(self.worker.data)
            self.table_viewer.show()
            self.close()
            


    def doTrain(self, mode = 0):
        self.table_viewer = DFEditorWidget()
        self.__setUIEnabling(False)

        print("Initiating Training Process...")
        self.thread = QThread()
        if(mode == 1):
            self.worker = TrainWorker()
            self.worker.setToken(self.token_input_box.toPlainText())
            print("Entering Training Mode")
        elif mode == 0:
            self.worker = TestTrainWorker()
            self.worker.setToken(self.token_input_box.toPlainText())
            print("Entering Test mode")
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()


        self.worker.finished.connect(
            lambda: self.trainingAftermath(self.worker.data)
        )
      
        
        
        
        

        
        
    




if __name__ == '__main__':
    app = QApplication(sys.argv)
    token_input = TokenInputWidget()
    token_input.show()
    sys.exit(app.exec_() )
    
    