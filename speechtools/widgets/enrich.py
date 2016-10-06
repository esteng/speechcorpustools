
import re
import math
from collections import OrderedDict

from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb import CorpusContext

from .base import RadioSelectWidget, BaseSummaryWidget

from .lexicon import StressToneSelectWidget, WordSelectWidget

from .inventory import PhoneSelectWidget, PhoneSubsetSelectWidget, RegexPhoneSelectWidget

class BaseDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super(BaseDialog, self).__init__(parent)

        layout = QtWidgets.QVBoxLayout()

        aclayout = QtWidgets.QHBoxLayout()

        self.acceptButton = QtWidgets.QPushButton('Encode')
        self.acceptButton.clicked.connect(self.accept)
        self.cancelButton = QtWidgets.QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.reject)

        aclayout.addWidget(self.acceptButton)
        aclayout.addWidget(self.cancelButton)

        layout.addLayout(aclayout)

        self.setLayout(layout)

    def validate(self):
        return True

    def accept(self):
        if self.validate():
            super(BaseDialog, self).accept()

class EncodePauseDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodePauseDialog, self).__init__(parent)

        layout = QtWidgets.QFormLayout()

        self.wordSelect = WordSelectWidget(config)

        layout.addRow(self.wordSelect)

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Encode non-speech elements')

    def value(self):
        return self.wordSelect.value()

class EncodeUtteranceDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodeUtteranceDialog, self).__init__(parent)

        layout = QtWidgets.QFormLayout()

        self.minPauseEdit = QtWidgets.QLineEdit()
        self.minPauseEdit.setText('0')

        self.minUttEdit = QtWidgets.QLineEdit()
        self.minUttEdit.setText('0')

        layout.addRow('Minimum duration of pause between utterances (seconds)', self.minPauseEdit)
        layout.addRow('Minimum duration of utterances (seconds)', self.minUttEdit)

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Encode utterances')

    def validate(self):
        try:
            val = self.value()
        except ValueError:
            reply = QtWidgets.QMessageBox.critical(self,
                    "Invalid information",
                    'Please make sure that the durations are properly specified.')
            return False
        if val[0] > 10 or val[1] > 10:
            reply = QtWidgets.QMessageBox.warning(self, "Long duration",
            'Are you sure that durations are specified in seconds?',
            buttons = QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.Cancel:
                return False
        return True


    def value(self):
        return float(self.minPauseEdit.text()), float(self.minUttEdit.text())

class EncodeSpeechRateDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodeSpeechRateDialog, self).__init__(parent)

        layout = QtWidgets.QFormLayout()

        self.subsetSelect = PhoneSubsetSelectWidget(config)

        layout.addRow('Select set of phones to count', self.subsetSelect)

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Encode speech rate')

    def value(self):
        return self.subsetSelect.value()

class EncodeUtterancePositionDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodeUtterancePositionDialog, self).__init__(parent)

        self.setWindowTitle('Encode utterance positions')

class AnalyzeAcousticsDialog(BaseDialog):
    def __init__(self, config, parent):
        super(AnalyzeAcousticsDialog, self).__init__(parent)

        self.setWindowTitle('Analyze acoustics')

        layout = QtWidgets.QFormLayout()

        self.acousticsWidget = RadioSelectWidget('Acoustics to encode',
                                            OrderedDict([
                                            ('Pitch (REAPER)','pitch'),
                                            #('Formants (LPC)','formants'),
                                            ]))

        layout.addRow(self.acousticsWidget)

        self.layout().insertLayout(0, layout)

    def value(self):
        return self.acousticsWidget.value()

class EncodeSyllabicsDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodeSyllabicsDialog, self).__init__(parent)
        layout = QtWidgets.QFormLayout()

        self.phoneSelect = PhoneSelectWidget(config)
        for i in range(self.phoneSelect.selectWidget.count()):
            item = self.phoneSelect.selectWidget.item(i)
            for v in ['a','e','i','o','u']:
                if v in item.text().lower():
                    index = self.phoneSelect.selectWidget.model().index(i,0)
                    self.phoneSelect.selectWidget.selectionModel().select(index, QtCore.QItemSelectionModel.Select)
                    break

        layout.addRow('Syllabic segments', self.phoneSelect)

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Encode syllabic segments')
    def value(self):
        return self.phoneSelect.value()

class EncodeSyllablesDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodeSyllablesDialog, self).__init__(parent)

        layout = QtWidgets.QFormLayout()

        self.algorithmWidget = RadioSelectWidget('Syllabification algorithm',
                                            OrderedDict([
                                            #('Probabilistic onsets and codas (language-independent)','probabilistic'),
                                            ('Max attested onset (language-independent)','maxonset'),]))

        layout.addRow(self.algorithmWidget)

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Encode syllables')

    def value(self):
        return self.algorithmWidget.value()

class EncodePhoneSubsetDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodePhoneSubsetDialog, self).__init__(parent)

        layout = QtWidgets.QFormLayout()

        self.labelEdit = QtWidgets.QLineEdit()

        layout.addRow('Class label', self.labelEdit)

        self.phoneSelect = PhoneSelectWidget(config)

        layout.addRow('Segments', self.phoneSelect)

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Encode phone subsets')

    def value(self):
        return self.labelEdit.text(), self.phoneSelect.value()

class EnrichLexiconDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EnrichLexiconDialog, self).__init__(parent)

        layout = QtWidgets.QFormLayout()

        self.caseCheck = QtWidgets.QCheckBox()

        layout.addRow('Case sensitive', self.caseCheck)

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Enrich lexicon')
        self.path = None

    def accept(self):
        self.path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select lexicon", filter = "CSV (*.txt  *.csv)")
        if not self.path:
            return
        QtWidgets.QDialog.accept(self)

    def value(self):
        return self.path, self.caseCheck.isChecked()

class EnrichFeaturesDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EnrichFeaturesDialog, self).__init__(parent)

        layout = QtWidgets.QFormLayout()

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Enrich phones with features')
        self.path = None

    def accept(self):
        self.path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select feature file", filter = "CSV (*.txt  *.csv)")
        if not self.path:
            return
        QtWidgets.QDialog.accept(self)

    def value(self):
        return self.path

class AnnotationTypeSelect(QtWidgets.QComboBox):
    def __init__(self, hierarchy, subsets = False):
        super(AnnotationTypeSelect, self).__init__()
        self.hierarchy = hierarchy
        self.subsets = subsets
        self.baseAnnotation = None
        self.generateItems()

    def setBase(self, base):
        self.baseAnnotation = base
        self.generateItems()

    def generateItems(self):
        self.clear()
        if self.baseAnnotation is None:
            toiter = self.hierarchy.highest_to_lowest[:-1]
        else:
            toiter = self.hierarchy.get_lower_types(self.baseAnnotation)
        for at in toiter:
            self.addItem(at)
            if self.subsets:
                subs = []
                if at in self.hierarchy.subset_types:
                    subs += self.hierarchy.subset_types[at]
                if at in self.hierarchy.subset_tokens:
                    subs += self.hierarchy.subset_tokens[at]

                for s in sorted(subs):
                    self.addItem(' - '.join([at, s]))

class EncodeHierarchicalPropertiesDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodeHierarchicalPropertiesDialog, self).__init__(parent)
        with CorpusContext(config) as c:
            hierarchy = c.hierarchy
        layout = QtWidgets.QFormLayout()

        self.higherSelect = AnnotationTypeSelect(hierarchy)
        self.higherSelect.currentIndexChanged.connect(self.updateBase)
        self.higherSelect.currentIndexChanged.connect(self.updateName)
        self.lowerSelect = AnnotationTypeSelect(hierarchy, subsets = True)
        self.lowerSelect.currentIndexChanged.connect(self.updateName)

        self.typeSelect = QtWidgets.QComboBox()
        self.typeSelect.addItem('count')
        self.typeSelect.addItem('rate')
        self.typeSelect.addItem('position')
        self.typeSelect.currentIndexChanged.connect(self.updateName)

        self.nameEdit = QtWidgets.QLineEdit()
        self.updateBase()
        self.updateName()

        layout.addRow('Higher annotation', self.higherSelect)
        layout.addRow('Lower annotation', self.lowerSelect)
        layout.addRow('Type of property', self.typeSelect)
        layout.addRow('Name of property', self.nameEdit)

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Enrich hierarchical annotations')

    def updateBase(self):
        self.lowerSelect.setBase(self.higherSelect.currentText())

    def updateName(self):
        lower, subset = self.splitLower()
        if subset is not None:
            lower = subset
        to_build = [self.typeSelect.currentText().title(), 'of', lower,
                    'in', self.higherSelect.currentText()]
        self.nameEdit.setText('_'.join(to_build))

    def validate(self):
        if self.nameEdit.text() == '':
            reply = QtWidgets.QMessageBox.critical(self,
                    "Missing information", 'Please make sure a name for the new property is specified.')
            return False
        ## FIXME add check for whether the name of the property already exists
        return True

    def splitLower(self):
        lower_text = self.lowerSelect.currentText()
        if ' - ' in lower_text:
            lower, subset = lower_text.split(' - ')
        else:
            lower = lower_text
            subset = None
        return lower, subset

    def value(self):
        lower, subset = self.splitLower()
        return {'higher': self.higherSelect.currentText(), 'type':self.typeSelect.currentText(),
                'lower': lower, 'subset': subset, 'name': self.nameEdit.text()}

class EncodeLabel(QtWidgets.QWidget):
    toEncode = QtCore.pyqtSignal(str)
    def __init__(self, annotation_type, parent = None):
        super(EncodeLabel, self).__init__(parent)
        self.acousticsPressed = False
        self.optionsDict = {'non-speech element':( lambda : self.toEncode.emit('pause')),
                            'utterance': (lambda: self.toEncode.emit('utterances')),
                            'syllabic': (lambda : self.toEncode.emit('syllabics')), 
                            'syllable': (lambda : self.toEncode.emit('syllables')),
                            'hierarchical': (lambda: self.toEncode.emit('hierarchical')),
                            'lexicon' : (lambda: self.toEncode.emit('lexical')),
                            'phonological inventory' : (lambda : self.toEncode.emit('phonological')),
                            'speakers' : (lambda: self.toEncode.emit('speaker')),
                            'subset': (lambda: self.toEncode.emit('subset')),
                            'stress/tone' : (lambda: self.toEncode.emit('stress/tone')),
                            'relativized' : (lambda: self.toEncode.emit('relativized')),
                            'acoustics' : (lambda: self.toEncode.emit('acoustics'))}
                            

        self.annotation_type = annotation_type
        self.init_buttons()
        layout = QtWidgets.QVBoxLayout()
    
        self.enrichButton.setEnabled(True)

        self.enrichButton.clicked.connect(self.optionsDict[self.annotation_type])


        layout.addWidget(self.enrichButton)

        self.setLayout(layout)

    def init_buttons(self):
        self.enrichButton = QtWidgets.QPushButton()
        self.enrichButton.setText('Encode \n{}'.format(self.annotation_type))
        if self.annotation_type in ['non-speech element', 'utterance', 'syllable']:
            self.enrichButton.setText((self.enrichButton.text()+'s').replace('non-speech elements','pauses'))
        if self.annotation_type == 'relativized':
            self.enrichButton.setText('Encode \nrelativized measures')
        if self.annotation_type in ['lexicon', 'phonological inventory', 'speakers']:
            self.enrichButton.setText('Enrich \n{}'.format(self.annotation_type))
        if self.annotation_type == 'subset':
            self.enrichButton.setText('Encode \nphone subsets (classes)')
        if self.annotation_type == 'syllabic':
            self.enrichButton.setText('Encode \nsyllabic segs')
        if self.annotation_type == 'hierarchical':
            self.enrichButton.setText('Encode \nhierarchical properties')
        if self.annotation_type == 'acoustics':
            self.enrichButton.setText('Analyze \nacoustics')
        self.enrichButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)


    def updateOptions(self, config):
        if config is not None:
            self.enrichButton.setEnabled(True)
            self.enrichButton.setStyleSheet('background-color: None')
            with CorpusContext(config) as c:
                word = False
                try:
                    word = getattr(c, c.word_name)
                except:
                    word = False
                if c.hierarchy.has_token_subset(c.word_name, self.annotation_type.replace('non-speech element', 'pause')) \
                        or c.hierarchy.has_type_subset(c.phone_name, self.annotation_type) \
                        or c.hierarchy.has_token_property(self.annotation_type,'begin'): 
                    self.enrichButton.setStyleSheet('background-color: rgb(0,250,154)') 
                    self.enrichButton.setText(self.enrichButton.text().replace('Encode', 'Re-encode').replace('Analyze', 'Re-analyze'))
                pitch = False
                if self.annotation_type == 'acoustics' and pitch:
                    self.enrichButton.setStyleSheet('background-color: rgb(0,250,154)') 
                    self.enrichButton.setText(self.enrichButton.text().replace('Encode', 'Re-encode').replace('Analyze', 'Re-analyze'))
                if self.annotation_type == 'acoustics' and \
                            not c.hierarchy.has_token_property('utterance','begin'):
                            self.resetFeatures()
                if self.annotation_type not in [c.phone_name, c.word_name]:
                    if self.annotation_type == 'stress/tone' and \
                            not c.hierarchy.has_type_property('syllable','label'):
                            self.resetFeatures()
                    if self.annotation_type == 'utterance' and \
                            not c.hierarchy.has_token_subset(c.word_name, 'pause'):
                            self.resetFeatures()
                    if self.annotation_type == 'syllabic' and \
                            not c.hierarchy.has_token_subset(c.word_name, 'pause'):
                            self.resetFeatures()
                    if self.annotation_type == 'syllable' and \
                            not c.hierarchy.has_token_subset(c.word_name, 'pause'):
                            self.resetFeatures()
                    if self.annotation_type == 'syllable' and \
                            not c.hierarchy.has_type_subset(c.phone_name, 'syllabic'):
                            self.resetFeatures()
                    if self.annotation_type == 'syllable' and \
                            not c.hierarchy.has_token_property('syllable','begin'):
                            self.resetFeatures(True)
                    if self.annotation_type == 'non-speech element' and \
                            not c.hierarchy.has_token_subset(c.word_name, 'pause'):
                            self.resetFeatures(True)
                else:
                    self.enrichButton.setEnabled(True)

        else:
            self.enrichButton.setEnabled(False)
            self.enrichButton.setStyleSheet('background-color: None')

    def resetFeatures(self, pause = False):
        if pause:
            self.enrichButton.setEnabled(True)

        else:
            self.enrichButton.setEnabled(False)
        self.enrichButton.setStyleSheet('background-color: None')
        self.enrichButton.setText(self.enrichButton.text().replace('Re-encode', 'Encode').replace('Re-analyze', 'Analyze'))


class PropertySummaryWidget(QtWidgets.QWidget):
    def __init__(self, property_name, parent = None):
        super(PropertySummaryWidget, self).__init__(parent)

        layout = QtWidgets.QFormLayout()

        layout.addRow(QtWidgets.QLabel(property_name))

        self.setLayout(layout)

class AnnotationSummaryWidget(BaseSummaryWidget):
    def __init__(self, parent = None):
        super(AnnotationSummaryWidget, self).__init__(parent)

        superLayout = QtWidgets.QVBoxLayout()

        self.layout = QtWidgets.QGridLayout()

        mainWidget = QtWidgets.QWidget()

        mainWidget.setSizePolicy(QtWidgets.QSizePolicy.Preferred,QtWidgets.QSizePolicy.Preferred)
        mainWidget.setLayout(self.layout)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(mainWidget)
        scroll.setMinimumHeight(10)
        scroll.setSizePolicy(QtWidgets.QSizePolicy.Preferred,QtWidgets.QSizePolicy.Preferred)
        policy = scroll.sizePolicy()
        policy.setVerticalStretch(1)
        scroll.setSizePolicy(policy)
        superLayout.addWidget(scroll)

        self.unknownWidget = QtWidgets.QLabel('Please connect to a server and select a corpus.')

        self.setLayout(superLayout)

    def updateConfig(self, config):
        
        while self.layout.count():
            item = self.layout.takeAt(0) 
            if item is not None:
                w = item.widget()
                w.setParent(None)
                if w != self.unknownWidget:
                    w.deleteLater()
        
        if config is not None:
            with CorpusContext(config) as c:
                i =0
                for i,annotation_type in enumerate(sorted(c.hierarchy.annotation_types, key = lambda x : x[1])):
                    w = PropertySummaryWidget(annotation_type.upper()+ ":")
                    self.layout.addWidget(w,i,0)

                    props = sorted(c.hierarchy.token_properties[annotation_type] | c.hierarchy.type_properties[annotation_type])
                    skipped =0
                    for j,p in enumerate(props):
                        if p[0] == 'id':
                            skipped +=1
                            continue  
                        w = PropertySummaryWidget(p[0])
                        self.layout.addWidget(w, i,j+1-skipped)
                w = PropertySummaryWidget('SPEAKER:')
                i+=1
                self.layout.addWidget(w,i,0)
                props = sorted(c.hierarchy.speaker_properties)
                for k,p in enumerate(props, 1):
                    if p[0] == 'id':
                        continue
                    w = PropertySummaryWidget(p[0])
                    self.layout.addWidget(w,i,k)
              

class EnrichmentWidget(QtWidgets.QWidget):
    toEncode = QtCore.pyqtSignal(str)
    def __init__(self, annotation_type, parent = None):
        super(EnrichmentWidget, self).__init__(parent)
        self.annotation_type = annotation_type

        layout = QtWidgets.QHBoxLayout()

        self.label = EncodeLabel(self.annotation_type)

        self.label.toEncode.connect(self.toEncode.emit)

        layout.addWidget(self.label)

        self.setLayout(layout)

    def updateConfig(self, config):
        self.label.updateOptions(config)

class ExtraEnrichmentWidget(BaseSummaryWidget):
    toEncode = QtCore.pyqtSignal(str)
    def __init__(self, parent = None):
        super(ExtraEnrichmentWidget,self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.mainLayout = QtWidgets.QGridLayout()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0,0,0,0)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)

        mainWidget = QtWidgets.QWidget()

        mainWidget.setSizePolicy(QtWidgets.QSizePolicy.Preferred,QtWidgets.QSizePolicy.Preferred)
        mainWidget.setLayout(self.mainLayout)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(mainWidget)
        scroll.setMinimumHeight(10)
        scroll.setSizePolicy(QtWidgets.QSizePolicy.Preferred,QtWidgets.QSizePolicy.Preferred)
        policy = scroll.sizePolicy()
        policy.setVerticalStretch(1)
        scroll.setSizePolicy(policy)
        layout.addWidget(scroll)

        lexical = EnrichmentWidget('lexicon')
        lexlab = QtWidgets.QLabel()
        lexlab.setText('Lexical properties:')
        lexical.toEncode.connect(self.toEncode.emit) 

        self.mainLayout.addWidget(lexlab, 0,0,  QtCore.Qt.AlignCenter)
        self.mainLayout.addWidget(lexical, 1, 0, QtCore.Qt.AlignCenter)

        phonlab = QtWidgets.QLabel()
        phonlab.setText('Phonological properties:')
        phon = EnrichmentWidget('phonological inventory')
        classes = EnrichmentWidget('subset')
        phon.toEncode.connect(self.toEncode.emit) 
        classes.toEncode.connect(self.toEncode.emit) 

        self.mainLayout.addWidget(phonlab, 2,0, QtCore.Qt.AlignCenter)
        self.mainLayout.addWidget(phon, 3, 0, QtCore.Qt.AlignCenter)
        self.mainLayout.addWidget(classes, 4, 0, QtCore.Qt.AlignCenter)

        syllab = QtWidgets.QLabel()
        syllab.setText('Syllabic properties:')
        stress = EnrichmentWidget('stress/tone')
        print(self.config, " is config")
        stress.toEncode.connect(self.toEncode.emit) 

        self.mainLayout.addWidget(syllab, 5, 0, QtCore.Qt.AlignCenter)
        self.mainLayout.addWidget(stress, 6,0, QtCore.Qt.AlignCenter)

        otherlab = QtWidgets.QLabel()
        otherlab.setText('Combined properties:')
        hierarchical = EnrichmentWidget('hierarchical')
        relativized = EnrichmentWidget('relativized')
        speaker = EnrichmentWidget('speakers')
        hierarchical.toEncode.connect(self.toEncode.emit) 
        relativized.toEncode.connect(self.toEncode.emit) 
        speaker.toEncode.connect(self.toEncode.emit) 

        self.mainLayout.addWidget(otherlab,7,0, QtCore.Qt.AlignCenter)
        self.mainLayout.addWidget(hierarchical,8,0, QtCore.Qt.AlignCenter)
        self.mainLayout.addWidget(relativized,9,0, QtCore.Qt.AlignCenter)
        self.mainLayout.addWidget(speaker,10,0, QtCore.Qt.AlignCenter)

        self.helpButton= QtWidgets.QPushButton('Help')
        self.mainLayout.addWidget(self.helpButton, 11,0,QtCore.Qt.AlignCenter)

        self.setLayout(layout)

        self.refresh()

    def refresh(self):
        for i in range(self.mainLayout.count()):
            try:

                self.mainLayout.itemAt(i).widget().updateConfig(self.config)
            except AttributeError:
                continue 

        
class EnrichmentSummaryWidget(BaseSummaryWidget):
    toEncode = QtCore.pyqtSignal(str)
    def __init__(self, parent = None):
        super(EnrichmentSummaryWidget, self).__init__(parent)


        layout = QtWidgets.QVBoxLayout()
        self.mainLayout = QtWidgets.QGridLayout()
        self.mainLayout.setSpacing(0)
        #self.mainLayout.setContentsMargins(0,0,0,0)
        #self.mainLayout.setAlignment(QtCore.Qt.AlignTop)

        mainWidget = QtWidgets.QWidget()

        mainWidget.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
        mainWidget.setLayout(self.mainLayout)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(mainWidget)
        scroll.setMinimumHeight(10)
        scroll.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
        policy = scroll.sizePolicy()
        policy.setVerticalStretch(1)
        scroll.setSizePolicy(policy)
        layout.addWidget(scroll)

        self.percentLabel = QtWidgets.QLabel()

        self.percentInt = 0

        self.syllabic, self.syllable, self.pause, self.utterance = False, False, False, False
        
        self.percentLabel.setText("{}% Enriched".format(self.percentInt))



        #for k in ['utterance', 'word', 'syllable', 'phone']:
        #    self.mainLayout.addWidget(EnrichmentWidget(k))

        pauseWidget = EnrichmentWidget('non-speech element')
        utteranceEnrich = EnrichmentWidget('utterance')
        syllabicEnrich = EnrichmentWidget('syllabic')
        syllableEnrich = EnrichmentWidget('syllable')
        acousticsEncode = EnrichmentWidget('acoustics')

        pauseWidget.toEncode.connect(self.toEncode.emit)
        utteranceEnrich.toEncode.connect(self.toEncode.emit)
        syllabicEnrich.toEncode.connect(self.toEncode.emit)
        syllableEnrich.toEncode.connect(self.toEncode.emit) 
        acousticsEncode.toEncode.connect(self.toEncode.emit)

        layout0 = QtWidgets.QVBoxLayout()
        #line = QtCore.QLine(0,0,0,-1)

        painter = QtGui.QPainter()
        painter.drawLine(0,0,10,10)
        
        layout0.addWidget(pauseWidget)

        view = QtWidgets.QGraphicsView()
        scene = QtWidgets.QGraphicsScene()
        line = QtWidgets.QGraphicsLineItem(0,0,0,-10)

        scene.addItem(line)
        view.setScene(scene)

        self.helpButton = QtWidgets.QPushButton('help')
        #self.mainLayout.addWidget(view,0,0)
        self.mainLayout.addWidget(pauseWidget, 0, 1, QtCore.Qt.AlignCenter)        
        self.mainLayout.addWidget(utteranceEnrich , 1, 0, QtCore.Qt.AlignCenter)

        self.mainLayout.addWidget(syllabicEnrich,1, 2, QtCore.Qt.AlignCenter)
        self.mainLayout.addWidget(syllableEnrich,2,2, QtCore.Qt.AlignCenter)
        self.mainLayout.addWidget(self.percentLabel, 0,2, QtCore.Qt.AlignCenter)
        self.mainLayout.addWidget(acousticsEncode, 2,0, QtCore.Qt.AlignCenter)
        self.mainLayout.addWidget(self.helpButton, 3, 1, QtCore.Qt.AlignCenter)
        
        self.setLayout(layout)

    def refresh(self):

        for i in range(self.mainLayout.count()):
            try:        
                self.mainLayout.itemAt(i).widget().updateConfig(self.config)
            except AttributeError:
                continue
            
            if self.config is not None:
                with CorpusContext(self.config) as c:
                    if c.hierarchy.has_type_subset(c.phone_name, 'syllabic') and not self.syllabic:
                        self.percentInt +=25
                        self.syllabic = True
                    if c.hierarchy.has_token_subset(c.word_name, 'pause') and not self.pause:
                        self.percentInt +=25
                        self.pause = True
                    if c.hierarchy.has_token_property('utterance', 'begin') and not self.utterance:
                        self.percentInt +=25
                        self.utterance = True
                    if c.hierarchy.has_token_property('syllable','begin') and not self.syllable:
                        self.percentInt +=25
                        self.syllable = True
        self.percentLabel.setText("{}% Enriched".format(self.percentInt))

    def resetPercent(self):
        self.percentInt = 0
        self.percentLabel.setText("0% Enriched")
        self.syllabic, self.syllable, self.pause, self.utterance = False, False, False, False


class EncodeStressDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodeStressDialog, self).__init__(parent)

        self.config = config
        layout = QtWidgets.QFormLayout()
        self.stressTone = RadioSelectWidget('Type of enrichment',OrderedDict([('Tone','tone'),('Stress','stress')]))
        self.stressToneSelectWidget = StressToneSelectWidget(config)

        self.stressToneSelectWidget.vowelRegexWidget.regexEdit.setText("^[a-z][a-z0-9][a-z0-9]?[a-z0-9]?")
        self.stressToneSelectWidget.regexWidget.regexEdit.setText("_T[0-9]$")
        self.stressToneSelectWidget.regexWidget.testButton.clicked.connect(self.testRegex)
        layout.addRow(self.stressTone)

        self.stressTone.optionChanged.connect(self.change_view)

        layout.addRow(self.stressToneSelectWidget)


        self.resetButton = QtWidgets.QPushButton()
        self.resetButton.setText('Reset')
        self.resetButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
        self.resetButton.clicked.connect(self.reset)

        layout.addRow(self.resetButton)
        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Encode stress')

    def change_view(self, text):
        if text == 'stress':
            self.stressToneSelectWidget.vowelRegexWidget.regexEdit.setText("^[A-Z][A-Z]")
            self.stressToneSelectWidget.regexWidget.regexEdit.setText('[0-2]$')
        elif text == 'tone':
            self.stressToneSelectWidget.vowelRegexWidget.regexEdit.setText("^[a-z][a-z0-9][a-z0-9]?[a-z0-9]?")
            self.stressToneSelectWidget.regexWidget.regexEdit.setText("_T[0-9]$")

    def testRegex(self):
        if isinstance(self.layout().itemAt(0),QtWidgets.QHBoxLayout):
            self.layout().itemAt(0).setParent(None)
        newLayout = QtWidgets.QHBoxLayout()

        allphones = []

        with CorpusContext(self.config) as c:
        #   q = c.query_graph(c.phone).filter(c.phone.label.regex(self.stressToneSelectWidget.combo_value()))
            statement = "MATCH (n:phone_type:{corpus}) return n.label as label".format(corpus = c.corpus_name)


            results = c.execute_cypher(statement)
            #for c in results.cursors:
            for label in results:
                    #phone_label = item[0].properties['label']
                phone_label = label['label']
                r = re.search(self.stressToneSelectWidget.regexWidget.regexEdit.text(), phone_label)
                    #s = re.search(self.stressToneSelectWidget.vowelRegexWidget.regexEdit.text(), phone_label)
                if r is not None:
                    index = r.start(0)

                    allphones.append((phone_label,index))
            allphones =set(allphones)
            allphones=list(allphones)
            data = OrderedDict([
            ('stripped vowel', []),
            ('whole vowel', []),
            ('ending', [])])
            data.update({"whole vowel":[]})
            data.update({"stripped vowel":[]})
            data.update({"ending":[]})
            for tup in allphones:
                data['whole vowel'].append(tup[0])
                data['stripped vowel'].append(tup[0][:tup[1]])
                data['ending'].append(tup[0][tup[1]:])
            regexPhoneSelect = RegexPhoneSelectWidget(data, 3,len(allphones))

            newLayout.addWidget(regexPhoneSelect)
        self.layout().insertLayout(0, newLayout)
    def value(self):
        return (self.stressTone.value(), self.stressToneSelectWidget.value(), self.stressToneSelectWidget.combo_value())

    def reset(self):
        with CorpusContext(self.config) as c:
            c.reset_to_old_label()



class EncodeRelativizedMeasuresDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodeRelativizedMeasuresDialog, self).__init__(parent)

        layout = QtWidgets.QFormLayout()
        self.optionWidget = QtWidgets.QComboBox(self)
        self.optionWidget.addItem("Word")
        self.optionWidget.addItem("Phone")
        self.optionWidget.addItem("Speaker")
        with CorpusContext(config) as c:
            if c.hierarchy.has_type_subset(c.phone_name, 'syllabic'): 
                self.optionWidget.addItem("Syllable")
            if c.hierarchy.has_type_property('utterance','label'):
                self.optionWidget.addItem("Utterance")
        self.optionWidget.currentTextChanged.connect(self.change_view)
        layout.addWidget(self.optionWidget)

        self.radioWidget = RadioSelectWidget('Desired measure:', OrderedDict([
            ('Word Mean Duration', 'word_mean_duration'),
            ('Word Median Duration', 'word_median'),
            ('Word Standard Deviation','word_std_dev'),
            ('Baseline Duration', 'baseline_duration_word')]))
        layout.addWidget(self.radioWidget)

        self.layout().insertLayout(0, layout)

    def change_view(self, text):
        layout = QtWidgets.QFormLayout()
        self.radioWidget.setParent(None)
        if text == 'Utterance':
            self.radioWidget = RadioSelectWidget('Desired measure:', OrderedDict([
                ('Baseline Duration','baseline_duration_utterance')]))
        if text == 'Word':
            self.radioWidget = RadioSelectWidget('Desired measure:', OrderedDict([
            ('Word Mean Duration', 'word_mean_duration'),
            ('Word Median Duration', 'word_median'),
            ('Word Standard Deviation','word_std_dev'),
            ('Baseline Duration', 'baseline_duration_word')]))

        if text == 'Phone':
            self.radioWidget = RadioSelectWidget('Desired measure:', OrderedDict([('Phone Mean Duration','phone_mean'),
            ('Phone Median Duration','phone_median'),
            ('Phone Standard Deviation', 'phone_std_dev')]))
        if text == "Syllable":
            self.radioWidget = RadioSelectWidget('Desired measure:', OrderedDict([('Syllable Mean Duration', 'syllable_mean'),
            ('Syllable Median Duration', 'syllable_median'),
            ('Syllable Standard Deviation', 'syllable_std_dev'),
            ('Baseline Duration', 'baseline_duration_syllable')]))
        if text == "Speaker":
            self.radioWidget = RadioSelectWidget('Desired measure:', OrderedDict([('Mean Speech Rate', 'mean_speech_rate')]))
        self.optionWidget.setParent(None)
        layout.addWidget(self.optionWidget)
        layout.addWidget(self.radioWidget)
        self.layout().insertLayout(0, layout)




    def value(self):
        return self.radioWidget.value()

class EnrichSpeakersDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EnrichSpeakersDialog, self).__init__(parent)

        layout = QtWidgets.QFormLayout()
        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Enrich speakers from file')
        self.path = None

    def accept(self):
        self.path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select speaker file", filter = "CSV (*.txt  *.csv)")
        if not self.path:
            return
        QtWidgets.QDialog.accept(self)

    def value(self):
        return self.path   



