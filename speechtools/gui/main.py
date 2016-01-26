import os
import pickle

from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb.config import BASE_DIR

from speechtools.corpus import CorpusContext

from speechtools.utils import update_sound_files

from .widgets import (ConnectWidget as PGConnectWidget, ViewWidget, ImportWidget, ExportWidget,
                        HelpWidget, DiscourseWidget, QueryWidget, CollapsibleWidgetPair)

sct_config_pickle_path = os.path.join(BASE_DIR, 'config')

class ConnectWidget(PGConnectWidget):
    def __init__(self, *args, **kwargs):
        super(ConnectWidget, self).__init__(*args, **kwargs)
        self.audioLookupButton = QtWidgets.QPushButton('Find local audio files')
        self.audioLookupButton.setEnabled(False)
        self.formlayout.addRow(self.audioLookupButton)

        self.audioLookupButton.clicked.connect(self.findAudio)

        self.corporaList.selectionChanged.connect(self.enableFindAudio)

    def enableFindAudio(self):
        if self.corporaList.text() is not None:
            self.audioLookupButton.setEnabled(True)
        else:
            self.audioLookupButton.setEnabled(False)

    def findAudio(self):
        if self.corporaList.text() is not None:
            directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
            if directory is None:
                return
            name = self.corporaList.text()
            host = self.hostEdit.text()
            port = self.portEdit.text()
            user = self.userEdit.text()
            password = self.passwordEdit.text()
            with CorpusContext(name, graph_host = host, graph_port = port,
                            graph_user = user, graph_password = password) as c:
                update_sound_files(c, directory)

class LeftPane(QtWidgets.QWidget):
    def __init__(self):
        super(LeftPane, self).__init__()


        self.viewWidget = ViewWidget()
        self.queryWidget = QueryWidget()

        splitter = CollapsibleWidgetPair(QtCore.Qt.Vertical, self.queryWidget, self.viewWidget, collapsible = 0)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

    def updateConfig(self, config):
        self.viewWidget.updateConfig(config)
        self.queryWidget.updateConfig(config)

    def changeDiscourse(self, discourse):
        self.viewWidget.changeDiscourse(discourse)

class RightPane(QtWidgets.QWidget):
    configUpdated = QtCore.pyqtSignal(object)
    discourseChanged = QtCore.pyqtSignal(str)
    def __init__(self):
        super(RightPane, self).__init__()


        if os.path.exists(sct_config_pickle_path):
            with open(sct_config_pickle_path, 'rb') as f:
                config = pickle.load(f)
        else:
            config = None
        self.connectWidget = ConnectWidget(config = config)
        self.connectWidget.configChanged.connect(self.configUpdated.emit)
        self.discourseWidget = DiscourseWidget()
        self.configUpdated.connect(self.discourseWidget.updateConfig)
        self.discourseWidget.discourseChanged.connect(self.discourseChanged.emit)
        self.helpWidget = HelpWidget()

        upper = QtWidgets.QTabWidget()

        upper.addTab(self.connectWidget,'Connection')
        upper.addTab(self.discourseWidget, 'Discourses')

        lower = QtWidgets.QTabWidget()

        lower.addTab(self.helpWidget, 'Help')

        splitter = CollapsibleWidgetPair(QtCore.Qt.Vertical, upper, lower)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

class MainWindow(QtWidgets.QMainWindow):
    configUpdated = QtCore.pyqtSignal(object)
    def __init__(self, app):
        super(MainWindow, self).__init__()

        self.corpusConfig = None
        #self.connectWidget = ConnectWidget(self)
        #self.connectWidget.configChanged.connect(self.updateConfig)
        #self.viewWidget = ViewWidget(self)
        #self.importWidget = ImportWidget(self)
        #self.exportWidget = ExportWidget(self)

        self.leftPane = LeftPane()
        self.configUpdated.connect(self.leftPane.updateConfig)

        self.rightPane = RightPane()
        self.rightPane.configUpdated.connect(self.updateConfig)
        self.rightPane.discourseChanged.connect(self.leftPane.changeDiscourse)

        self.leftPane.queryWidget.viewRequested.connect(self.rightPane.discourseWidget.changeView)
        self.rightPane.discourseWidget.viewRequested.connect(self.leftPane.viewWidget.discourseWidget.changeView)
        self.mainWidget = CollapsibleWidgetPair(QtCore.Qt.Horizontal, self.leftPane,self.rightPane)

        #self.mainWidget.setStretchFactor(0, 1)


        self.wrapper = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.mainWidget)
        self.wrapper.setLayout(layout)
        self.setCentralWidget(self.wrapper)

        self.status = QtWidgets.QLabel()
        self.statusBar().addWidget(self.status, stretch=1)
        self.setWindowTitle("Speech Corpus Tools")
        self.createActions()
        self.createMenus()

        self.updateStatus()

        if os.path.exists(sct_config_pickle_path):
            self.rightPane.connectWidget.connectToServer()

    def updateConfig(self, config):
        self.corpusConfig = config
        self.updateStatus()
        self.configUpdated.emit(self.corpusConfig)

    def updateStatus(self):
        if self.corpusConfig is None:
            self.status.setText('No connection')
        else:
            c_name = self.corpusConfig.corpus_name
            if not c_name:
                c_name = 'No corpus selected'
            self.status.setText('Connected to {} ({})'.format(self.corpusConfig.graph_hostname, c_name))

    def closeEvent(self, event):
        if self.corpusConfig is not None:
            with open(sct_config_pickle_path, 'wb') as f:
                pickle.dump(self.corpusConfig, f)
        super(MainWindow, self).closeEvent(event)

    def createActions(self):

        self.connectAct = QtWidgets.QAction( "Connect to corpus...",
                self,
                statusTip="Connect to a corpus", triggered=self.connect)

        self.importAct = QtWidgets.QAction( "Import a  corpus...",
                self,
                statusTip="Import a corpus", triggered=self.importCorpus)

        self.specifyAct = QtWidgets.QAction( "Add phonological features...",
                self,
                statusTip="Specify a corpus", triggered=self.specifyCorpus)

        self.exportAct = QtWidgets.QAction( "Export a  corpus...",
                self,
                statusTip="Export a corpus", triggered=self.exportCorpus)

    def createMenus(self):
        self.corpusMenu = self.menuBar().addMenu("Corpus")
        self.corpusMenu.addAction(self.connectAct)

        self.corpusMenu.addSeparator()
        self.corpusMenu.addAction(self.importAct)
        self.corpusMenu.addAction(self.specifyAct)
        self.corpusMenu.addAction(self.exportAct)

    def connect(self):
        pass

    def importCorpus(self):
        pass

    def specifyCorpus(self):
        pass

    def exportCorpus(self):
        pass
