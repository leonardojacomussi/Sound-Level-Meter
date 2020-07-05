# -*- coding: utf-8 -*-
#%% Set path main
import os, time
path_main = os.path.dirname(os.path.realpath('__file__'))
os.chdir('Projetos')
path_project = os.getcwd()
os.chdir(path_main)
time.sleep(.1)

#%% Packages
from UserInterface import guiMNPS, guiSetup, guiProject, guiCalib, guiSave, guiAbout
from PyQt5 import QtCore, QtGui, QtWidgets
from pyaudioStream import pyaudioStream, getBandLevel
from scipy.io import loadmat, savemat
from numpy import round as rd
from datetime import datetime
import pyqtgraph
import default
import sys

#%% Code Sound Level Meter
class MNPS(QtWidgets.QMainWindow, guiMNPS):
    def __init__(self, parent=None):
        os.chdir(path_main)
        pyqtgraph.setConfigOption('background', 'k')
        super(MNPS, self).__init__(parent)
        self.setupUi(self)
        
        #  Informações de setup e projetos
        self.cacheSetup   = loadmat('cacheSetup.mat')
        self.projectInfos = loadmat('projectInfos.mat')
        if self.cacheSetup['inTimeweighting'][0][0] == 1.0: self.inTimeweighting = 'S'
        elif self.cacheSetup['inTimeweighting'][0][0] == 0.125: self.inTimeweighting = 'F'
        else: self.inTimeweighting = 'I'
        
        #  Informações gráficas da GUI
        self.qTimer = QtCore.QTimer()
        self.qTimer.setInterval(int(self.cacheSetup['inTimeweighting'][0][0]*1000))
        self.qTimer.timeout.connect(self.standby)
        self.qTimer.start()
        self.now = datetime.now()
        self.lblDateinfo.setText(self.now.strftime("%d/%m/%Y - %H:%M:%S"))
        self._translate = QtCore.QCoreApplication.translate
        self.btnQuit.setEnabled(True)
        self.btnQuit.setIcon(QtGui.QIcon("icon/power.png"))
        self.btnPlay.setIcon(QtGui.QIcon("icon/Play.png"))
        self.btnSave.setEnabled(False)
        self.btnSave.setIcon(QtGui.QIcon("icon/Save_noclick.png"))
        self.btnDelete.setEnabled(False)
        self.btnDelete.setIcon(QtGui.QIcon("icon/Delete_noclick.png"))
        self.btnStop.setEnabled(False)
        self.btnStop.setIcon(QtGui.QIcon("icon/Stop_noclick.png"))
        self.btnPlay.clicked.connect(self.btnPlay_Action)
        self.btnStop.clicked.connect(self.btnStop_Action)
        self.btnDelete.clicked.connect(self.btnDelete_Action)
        self.btnSetup.clicked.connect(self.btnSetup_Action)
        self.btnCalibrate.clicked.connect(self.btnCalibre_Action)
        self.btnInfo.clicked.connect(self.btnInfo_Action)
        self.btnNewproject.clicked.connect(self.btnNewproject_Action)
        self.btnSave.clicked.connect(self.btnSave_Action)
        self.btnQuit.clicked.connect(self.btnQuit_Action)
        
        #  Informações da stream
        self.samplingRate = default.samplingRate
        if self.cacheSetup['template'][0] == 'frequencyAnalyser':
            self.duration = self.cacheSetup['durationMeasure'][0][0]
            self.template = 'Frequency Analysis'
        else:
            self.duration = self.cacheSetup['durationSignal'][0][0]
            self.template = 'Reverberation Time'
        self.display = pyaudioStream(device       = default.device,
                                    samplingRate  = self.samplingRate,
                                    duration      = self.duration,
                                    inputChannels = default.inputChannels,
                                    timeConstant  = self.cacheSetup['inTimeweighting'][0][0],
                                    fstart        = self.cacheSetup['freqMin'][0][0],
                                    fstop         = self.cacheSetup['freqMax'][0][0],
                                    ffraction     = self.cacheSetup['fraction'][0][0],
                                    Freqweighting = self.cacheSetup['inFreqweighting'][0],
                                    template      = 'stand-by')
        self.display.streamStart()
        
        if self.cacheSetup['template'][0] == 'frequencyAnalyser':
            self.durationInfo = self.cacheSetup['durationMeasure'][0][0]
        else:
            self.durationInfo = self.cacheSetup['durationSignal'][0][0] +\
                                self.cacheSetup['startMargin'][0][0] +\
                                self.cacheSetup['stopMargin'][0][0] +\
                                self.display.timeSNR
        self.mins, self.secs = divmod(int(self.durationInfo), 60)
        self.timeformat = '{:02d}:{:02d}'.format(self.mins, self.secs)
        self.retranslateUi(self, self.cacheSetup['inFreqweighting'][0], self.template, self.inTimeweighting)
        self.lblDurationinfo.setText(self._translate("winMNPS", self.timeformat))
        self.lblProjectinfo.setText(self._translate("winMNPS",
                                                    "<html><head/><body><p align=\"center\">"
                                                    + self.projectInfos['name'][0] + " - Measurement "
                                                    + str(self.projectInfos['numMed'][0][0]) + "</p></body></html>"))
        
        self.graphicOctave.plotItem.showGrid(False, True, 0.7)
        self.graphicOctave.plotItem.setLogMode(x=False, y=False)
        self.graphicOctave.setYRange(0,120)
        self.graphicOctave.setLabel('left', "SPL [dB]")
        self.graphicOctave.setLabel('bottom', "Frequency [Hz]")
        self.ax = self.graphicOctave.getAxis('bottom') #This is the trick  
        self.ax.setTicks([self.display.strFreq])
        # self.ax.label.rotate(-90)
        # print(self.display.strFreq)
            
    def standby(self):
        self.now = datetime.now()
        self.lblDateinfo.setText(self.now.strftime("%d/%m/%Y - %H:%M:%S"))
        if not self.display.Level is None:
            self.lcdLevel_global.setText(str(round(self.display.globalLevel, 2)).replace(".",","))
            self.graphicOctave.clear()
            self.bg = pyqtgraph.BarGraphItem(x=self.display.eixoX,height=self.display.Level,width=0.6,brush='c')
            self.graphicOctave.addItem(self.bg)
            if self.display.key == False:
                self.qTimer.stop()
    
    def Record(self):
        # self.inicio=time.time()
        self.now = datetime.now()
        self.lblDateinfo.setText(self.now.strftime("%d/%m/%Y - %H:%M:%S"))
        if not self.display.Level is None:
            if self.display.ResultKey:
                self.lblDurationinfo.setText(self._translate("winMNPS", "00:00"))
                if self.display.template == 'frequencyAnalyser':
                    self.graphicOctave.clear()
                    self.bg = pyqtgraph.BarGraphItem(x=self.display.eixoX,height=self.display.Level,width=0.6,brush='c')
                    self.graphicOctave.addItem(self.bg)
                    self.lcdLevel_global.setText(str(round(self.display.globalLevel, 2)).replace(".",","))
                    self.lcdLSmax.setText(str(round(self.display.slowLevel[1].max(), 2)).replace(".",","))
                    self.lcdLSmin.setText(str(round(self.display.slowLevel[1].min(), 2)).replace(".",","))
                    self.lcdLFmax.setText(str(round(self.display.fastLevel[1].max(), 2)).replace(".",","))
                    self.lcdLFmin.setText(str(round(self.display.fastLevel[1].min(), 2)).replace(".",","))
                    self.lcdLImax.setText(str(round(self.display.impulseLevel[1].max(), 2)).replace(".",","))
                    self.lcdLImin.setText(str(round(self.display.impulseLevel[1].min(), 2)).replace(".",","))
                else:
                    self.graphicOctave.clear()
                    self.bg = pyqtgraph.BarGraphItem(x=self.display.eixoX,height=self.display.RT['T20'],width=0.6,brush='c')
                    self.graphicOctave.setYRange(0,self.display.RT['T10'].max()+2)
                    # self.graphicOctave.setYRange(0, 30)
                    self.graphicOctave.setLabel('left', "Reverberation Time [s]")
                    self.graphicOctave.setLabel('bottom', "Frequency [Hz]")
                    self.graphicOctave.addItem(self.bg)
                    self.ax = self.graphicOctave.getAxis('bottom') #This is the trick  
                    self.ax.setTicks([self.display.strFreq])
                    self.lcdLevel_global.setText(str(round(self.display.globalLevel, 2)).replace(".",","))
                    self.lcdLSmax.setText(str(round(self.display.slowLevel[1].max(), 2)).replace(".",","))
                    self.lcdLSmin.setText(str(round(self.display.slowLevel[1].min(), 2)).replace(".",","))
                    self.lcdLFmax.setText(str(round(self.display.fastLevel[1].max(), 2)).replace(".",","))
                    self.lcdLFmin.setText(str(round(self.display.fastLevel[1].min(), 2)).replace(".",","))
                    self.lcdLImax.setText(str(round(self.display.impulseLevel[1].max(), 2)).replace(".",","))
                    self.lcdLImin.setText(str(round(self.display.impulseLevel[1].min(), 2)).replace(".",","))
            else:
                #Temporizador de medição - contagem regressiva
                self.countdown = round(self.durationInfo - self.display.framesRead/self.samplingRate, 1)
                if self.countdown > 0 or self.display.pause == False:
                    self.mins, self.secs = divmod(int(self.countdown), 60)
                    self.timeformat = '{:02d}:{:02d}'.format(self.mins, self.secs)
                    self.lblDurationinfo.setText(self._translate("winMNPS", self.timeformat ))
                self.graphicOctave.clear()
                self.bg = pyqtgraph.BarGraphItem(x=self.display.eixoX,height=self.display.Level,width=0.6,brush='c')
                self.graphicOctave.addItem(self.bg)
            
            # Ajuste do ícone btnPlay para o final da gravação
            if self.display.key==False:
                self.btnSave.setEnabled(True)
                self.btnSave.setIcon(QtGui.QIcon("icon/Save.png"))
                self.btnDelete.setEnabled(True)
                self.btnDelete.setIcon(QtGui.QIcon("icon/Delete.png"))
                self.btnPlay.setEnabled(False)
                self.btnPlay.setIcon(QtGui.QIcon("icon/Play_noclick.png"))
                self.btnStop.setEnabled(False)
                self.btnStop.setIcon(QtGui.QIcon("icon/Stop_noclick.png"))
                self.btnNewproject.setEnabled(False)
                self.btnNewproject.setIcon(QtGui.QIcon("icon/NewProject_noclick.png"))
                self.btnSetup.setEnabled(False)
                self.btnSetup.setIcon(QtGui.QIcon("icon/Setup_noclick.png"))
                self.btnCalibrate.setEnabled(False)
                self.btnCalibrate.setIcon(QtGui.QIcon("icon/Calibrate_noclick.png"))
                self.btnInfo.setEnabled(False)
                self.btnInfo.setIcon(QtGui.QIcon("icon/info_noclick.png"))
                self.qTimer.stop()
        # self.fim=time.time()
        # print('updateGUI: ', self.fim-self.inicio, '[s]')

    def btnDelete_Action(self):
        self.btnDelete.setIcon(QtGui.QIcon("icon/Delete_click.png"))
        self.return_pyaudioStream()


    def btnPlay_Action(self):
        if self.display.rec:
            self.display.pause = not self.display.pause
            if self.display.pause:
                self.btnPlay.setIcon(QtGui.QIcon("icon/Pause_click.png"))
            else:
                self.btnPlay.setIcon(QtGui.QIcon("icon/Play_click.png"))
        else:
            self.display.key=False
            if self.cacheSetup['template'][0] == 'frequencyAnalyser':
                # self.durationInfo = self.cacheSetup['durationMeasure'][0][0]
                self.duration = self.cacheSetup['durationMeasure'][0][0]
                
            if self.cacheSetup['template'][0] == 'reverberationTime':
                # self.durationInfo = self.cacheSetup['durationSignal'][0][0] +\
                #                             self.cacheSetup['startMargin'][0][0] +\
                #                             self.cacheSetup['stopMargin'][0][0]
                self.duration = self.cacheSetup['durationSignal'][0][0]
            
            self.display = pyaudioStream(device        = default.device,
                                        samplingRate   = self.samplingRate,
                                        duration       = self.duration,
                                        inputChannels  = default.inputChannels,
                                        outputChannels = default.outChannels,
                                        timeConstant   = self.cacheSetup['inTimeweighting'][0][0],
                                        fstart         = self.cacheSetup['freqMin'][0][0],
                                        fstop          = self.cacheSetup['freqMax'][0][0],
                                        ffraction      = self.cacheSetup['fraction'][0][0],
                                        Freqweighting  = self.cacheSetup['inFreqweighting'][0],
                                        method         = self.cacheSetup['method'][0],
                                        startMargin    = self.cacheSetup['startMargin'][0][0], 
                                        stopMargin     = self.cacheSetup['stopMargin'][0][0],
                                        average        = self.cacheSetup['average'][0][0],
                                        template       = self.cacheSetup['template'][0])
            self.qTimer.timeout.connect(self.Record)
            self.qTimer.start()
            self.display.streamStart()
            # Setando ícones dos botões
            self.btnPlay.setIcon(QtGui.QIcon("icon/Play_click.png"))
            self.btnStop.setEnabled(True)
            self.btnStop.setIcon(QtGui.QIcon("icon/Stop.png"))
            self.btnNewproject.setEnabled(False)
            self.btnNewproject.setIcon(QtGui.QIcon("icon/NewProject_noclick.png"))
            self.btnSetup.setEnabled(False)
            self.btnSetup.setIcon(QtGui.QIcon("icon/Setup_noclick.png"))
            self.btnCalibrate.setEnabled(False)
            self.btnCalibrate.setIcon(QtGui.QIcon("icon/Calibrate_noclick.png"))
            self.btnInfo.setEnabled(False)
            self.btnInfo.setIcon(QtGui.QIcon("icon/info_noclick.png"))
            self.btnSave.setEnabled(False)
            self.btnSave.setIcon(QtGui.QIcon("icon/Save_noclick.png"))
            self.btnDelete.setEnabled(False)
            self.btnDelete.setIcon(QtGui.QIcon("icon/Delete_noclick.png"))

    def btnCalibre_Action(self):
        self.display.key=False
        self.btnCalibrate.setIcon(QtGui.QIcon("icon/Calibrate_click.png"))
        dlgCalibration = calib()
        # dlgCalibration.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        # dlgCalibration.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        dlgCalibration.update()
        dlgCalibration.setup=False
        dlgCalibration.exec_()
        if dlgCalibration.returnDisplay:
            self.return_pyaudioStream()

    def btnStop_Action(self):
        self.btnStop.setIcon(QtGui.QIcon("icon/Stop_click.png"))
        self.btnPlay.setEnabled(False)
        self.btnPlay.setIcon(QtGui.QIcon("icon/Play_noclick.png"))
        self.btnSave.setEnabled(True)
        self.btnSave.setIcon(QtGui.QIcon("icon/Save.png"))
        self.btnDelete.setEnabled(True)
        self.btnDelete.setIcon(QtGui.QIcon("icon/Delete.png"))
        self.display.pause = False
        self.display.stop = True

    def btnSetup_Action(self):
        self.btnSetup.setIcon(QtGui.QIcon("icon/Setup_click.png"))
        self.display.key=False
        dlgSetup = setSetup()
        # dlgSetup.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        # dlgSetup.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        dlgSetup.update()
        dlgSetup.exec_()
        if dlgSetup.returnDisplay:
            self.return_pyaudioStream()

    def btnInfo_Action(self):
        self.btnInfo.setIcon(QtGui.QIcon("icon/info_click.png"))
        self.display.key=False
        dlgAbout = about()
        # dlgAbout.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        # dlgAbout.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        dlgAbout.exec_()
        if dlgAbout.returnDisplay:
            self.return_pyaudioStream()

    def btnNewproject_Action(self):
        self.btnNewproject.setIcon(QtGui.QIcon("icon/NewProject_click.png"))
        self.display.key=False
        dlgNewProject = newProject()
        # dlgNewProject.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        # dlgNewProject.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        dlgNewProject.exec_()
        if dlgNewProject.returnDisplay:
            self.return_pyaudioStream()


    def return_pyaudioStream(self):
        self.cacheSetup=loadmat('cacheSetup.mat')
        self.btnPlay.setEnabled(True)
        self.btnPlay.setIcon(QtGui.QIcon("icon/Play.png"))
        self.btnStop.setEnabled(False)
        self.btnStop.setIcon(QtGui.QIcon("icon/Stop_noclick.png"))
        self.btnNewproject.setEnabled(True)
        self.btnNewproject.setIcon(QtGui.QIcon("icon/NewProject.png"))
        self.btnSetup.setEnabled(True)
        self.btnSetup.setIcon(QtGui.QIcon("icon/Setup.png"))
        self.btnCalibrate.setEnabled(True)
        self.btnCalibrate.setIcon(QtGui.QIcon("icon/Calibrate.png"))
        self.btnInfo.setEnabled(True)
        self.btnInfo.setIcon(QtGui.QIcon("icon/info.png"))
        self.btnSave.setEnabled(False)
        self.btnSave.setIcon(QtGui.QIcon("icon/Save_noclick.png"))
        self.btnDelete.setEnabled(False)
        self.btnDelete.setIcon(QtGui.QIcon("icon/Delete_noclick.png"))
        
        if self.cacheSetup['inTimeweighting'][0][0] == 1.0: self.inTimeweighting = 'S'
        elif self.cacheSetup['inTimeweighting'][0][0] == 0.125: self.inTimeweighting = 'F'
        else: self.inTimeweighting = 'I'
        
        if self.cacheSetup['template'][0] == 'frequencyAnalyser':
            self.durationInfo = self.cacheSetup['durationMeasure'][0][0]
            self.duration = self.cacheSetup['durationMeasure'][0][0]
            self.template = 'Frequency Analysis'
        else:
            self.durationInfo = self.cacheSetup['durationSignal'][0][0] +\
                                self.cacheSetup['startMargin'][0][0] +\
                                self.cacheSetup['stopMargin'][0][0] +\
                                self.display.timeSNR
            self.duration = self.cacheSetup['durationSignal'][0][0]
            self.template = 'Reverberation Time'
            
        self.retranslateUi(self, self.cacheSetup['inFreqweighting'][0], self.template, self.inTimeweighting)
        self.mins, self.secs = divmod(int(self.durationInfo), 60)
        self.timeformat = '{:02d}:{:02d}'.format(self.mins, self.secs)
        self.lblDurationinfo.setText(self._translate("winMNPS", self.timeformat))
        self.projectInfos = loadmat('projectInfos.mat')
        self.lblProjectinfo.setText(self._translate("winMNPS",
                                                    "<html><head/><body><p align=\"center\">"
                                                    + self.projectInfos['name'][0] + " - Measurement "
                                                    + str(self.projectInfos['numMed'][0][0]) + " </p></body></html>"))

        self.display = pyaudioStream(device        = default.device,
                                    samplingRate   = self.samplingRate,
                                    duration       = self.duration,
                                    inputChannels  = default.inputChannels,
                                    outputChannels = default.outChannels,
                                    timeConstant   = self.cacheSetup['inTimeweighting'][0][0],
                                    fstart         = self.cacheSetup['freqMin'][0][0],
                                    fstop          = self.cacheSetup['freqMax'][0][0],
                                    ffraction      = self.cacheSetup['fraction'][0][0],
                                    Freqweighting  = self.cacheSetup['inFreqweighting'][0],
                                    method         = self.cacheSetup['method'][0],
                                    startMargin    = self.cacheSetup['startMargin'][0][0], 
                                    stopMargin     = self.cacheSetup['stopMargin'][0][0],
                                    average        = self.cacheSetup['average'][0][0],
                                    template       = 'stand-by')
        self.display.streamStart()
        # Configurações gráficas
        self.graphicOctave.plotItem.showGrid(False, True, 0.7)
        self.graphicOctave.plotItem.setLogMode(x=False, y=False)
        self.graphicOctave.setYRange(0,120)
        self.graphicOctave.setLabel('left', "SPL [dB]")
        self.graphicOctave.setLabel('bottom', "Frequency [Hz]")
        self.ax = self.graphicOctave.getAxis('bottom') #This is the trick  
        self.ax.setTicks([self.display.strFreq])

        '''Update nativo do Qt interval = 1s = 1000ms'''
        self.qTimer.setInterval(int(self.cacheSetup['inTimeweighting'][0][0]*1000))
        self.qTimer.timeout.connect(self.standby)
        self.qTimer.start()

    def btnSave_Action(self):
        self.btnSave.setIcon(QtGui.QIcon("icon/Save_click.png"))
        dataProject = self.projectInfos
        os.chdir(path_project)
        # pathString = path_project + dataProject['name'][0]
        os.chdir(dataProject['name'][0])
        if self.display.template == 'frequencyAnalyser':
            saveString = "Measurement " + str(dataProject['numMed'][0][0]) + " NPS.xlsx"
        else:
            saveString = "Measurement " + str(dataProject['numMed'][0][0]) + " TR.xlsx"
        
        dlgSave = save()
        dlgSave.exec_()
        if dlgSave.clicked:
            import xlsxwriter
            from datetime import datetime
            from numpy import ones, float32
            
            # Data e hora
            hoje = datetime.now()
            # Vetor de freqências
            freqStr = []
            for i in range(self.display.freqs.size):
                if self.display.freqs[i] >= 1000:
                    freqStr.append(str(self.display.freqs[i]/1000).replace(".",",")+' k')
                else:
                    freqStr.append(str(self.display.freqs[i]).replace(".",","))
            # Ponderação temporal
            if self.display.timeConstant == 0.125:   timeStr = 'Fast';    timeStrIdx = 'F'
            elif self.display.timeConstant == 0.035: timeStr = 'Impulse'; timeStrIdx = 'I'
            else:                                    timeStr = 'Slow';    timeStrIdx = 'S'
            
            if self.display.template == 'frequencyAnalyser':
                # Níveis máximos e mínimos por banda de oitava
                LevelFreq_min = ones((self.display.Level.size), dtype=float32)*1000
                LevelFreq_max = ones((self.display.Level.size), dtype=float32)*-1000
                framesRead = 0
                numSamples = self.display.correctedData.size
                countDn = numSamples - framesRead
                while framesRead <= numSamples or countDn > self.display.frames:
                      globalLevel, Level = getBandLevel(data=self.display.correctedData[0, framesRead:framesRead+self.display.frames],
                                                        pyfilterbank = self.display.pyfilterbank,
                                                        fc = self.display.freqs,  pondFreq=self.display.Freqweighting)
                      for i in range(Level.size):
                          if Level[i] < LevelFreq_min[i]:
                              LevelFreq_min[i] = round(Level[i], 2)
                          if Level[i] > LevelFreq_max[i]:
                              LevelFreq_max[i] = round(Level[i], 2)
                          framesRead += self.display.frames
                          countDn -= framesRead
            # Criando planilha de Results
            planilha = xlsxwriter.Workbook(saveString)
            bold = planilha.add_format({'bold': True})
            folhaResults = planilha.add_worksheet(name="Results")
            folhaSetup      = planilha.add_worksheet(name="Settings")
            if dlgSave.saveAll:
                folhaReferencia = planilha.add_worksheet(name="Reference signals")
            formatSection = planilha.add_format({'bold': True, 'border': 4, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#66CCFF'})
            formatInformationT = planilha.add_format({'bold': True, 'border': 4, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#CCCCCC'})
            formatInformationN = planilha.add_format({'bold': True, 'border': 4, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#99FFFF'})
            if self.display.template == 'frequencyAnalyser':
                if dlgSave.saveAll:
                    # Folha de sinais referência
                    folhaReferencia.set_column(0,1,15)
                    folhaReferencia.merge_range(0,0,0,1, 'Reference signals', formatSection)
                    folhaReferencia.write("A2", "Medição", bold)
                    folhaReferencia.write_column("A3", self.display.correctedData[0,:])
                    folhaReferencia.write("B2", "Calibração", bold)
                    folhaReferencia.write_column("B3", self.display.cacheSetup['calibRec'][0])
                # Folha de configurações do template
                folhaSetup.set_column(0,0,25,bold)
                folhaSetup.set_column(1,1,20)
                folhaSetup.merge_range(0,0,0,1, 'Measurement setup', formatSection)
                folhaSetup.write("A2", "Template", bold);                 folhaSetup.write("B2", "Frequency Analysis")
                folhaSetup.write("A3", "Frequency range", bold);          folhaSetup.write("B3", freqStr[0]+' Hz a '+freqStr[-1]+'Hz')
                folhaSetup.write("A4", "Octave band", bold);              folhaSetup.write("B4", '1/'+str(self.display.ffraction))
                folhaSetup.write("A5", "Duration", bold);                  folhaSetup.write("B5", str(self.display.duration-1).replace(".",",")+' s')
                folhaSetup.write("A6", "Frequency weighting", bold); folhaSetup.write("B6", self.display.Freqweighting)
                folhaSetup.write("A7", "Integration time", bold);      folhaSetup.write("B7", timeStr)
                folhaSetup.write("A8", "Sampling rate", bold);       folhaSetup.write("B8", str(self.display.samplingRate)+' Hz')
                folhaSetup.write("A9", "Microphone sensitivity", bold); folhaSetup.write("B9", str(self.display.cacheSetup['Sensitivity'][0][0]*1000).replace(".",",")+' mV/Pa')
                folhaSetup.write("A10", "Correction", bold);                folhaSetup.write("B10", str(self.display.cacheSetup['correcao'][0][0]).replace(".",",")+' dB')
                folhaSetup.write("A11", "Fator de ajuste", bold);         folhaSetup.write("B11", str(round(self.display.cacheSetup['calibrationFC'][0][0], 4)).replace(".",","))
                folhaSetup.write("A12", "Data", bold);                    folhaSetup.write("B12", hoje.strftime("%d/%m/%Y"))
                folhaSetup.write("A13", "Hora", bold);                    folhaSetup.write("B13", hoje.strftime("%H:%M:%S"))
                # Folha de Results 
                # Frequency Analysis
                folhaResults.merge_range(0,0,0,self.display.freqs.size, 'Frequency Analysis', formatSection)
                folhaResults.set_column(0,0,15,bold)
                folhaResults.set_row(0,15,bold)
                folhaResults.write("A2", "Frequency [Hz]")
                folhaResults.write("A3", "L"+self.display.Freqweighting+','+timeStrIdx+",Mín      [dB]")
                folhaResults.write("A4", "L"+self.display.Freqweighting+','+timeStrIdx+",Máx     [dB]")
                folhaResults.write("A5", "L"+self.display.Freqweighting+"eq,"+timeStrIdx+'          [dB]')
                for i in range(len(freqStr)):
                    folhaResults.write(1, i+1, freqStr[i])
                    folhaResults.write(2, i+1, round(LevelFreq_min[i], 2))
                    folhaResults.write(3, i+1, round(LevelFreq_max[i], 2))
                    folhaResults.write(4, i+1, round(self.display.Level[i], 2))
                # Análise temporal
                folhaResults.set_column(1,1,15)
                folhaResults.merge_range(27,0,27,self.display.freqs.size, 'Time analysis', formatSection)
                folhaResults.merge_range(28,0,29,0,'L'+self.display.Freqweighting+','+'I', formatInformationT)
                folhaResults.write("B29", 'Tempo         [s]', bold)
                folhaResults.write_row("C29", self.display.impulseLevel[0])
                folhaResults.write("B30", 'Amplitude [dB]', bold)
                folhaResults.write_row("C30", self.display.impulseLevel[1])
                folhaResults.merge_range(31,0,32,0,'L'+self.display.Freqweighting+','+'F', formatInformationT)
                folhaResults.write("B32", 'Tempo         [s]', bold)
                folhaResults.write_row("C32", self.display.fastLevel[0])
                folhaResults.write("B33", 'Amplitude [dB]', bold)
                folhaResults.write_row("C33", self.display.fastLevel[1])
                folhaResults.merge_range(34,0,35,0,'L'+self.display.Freqweighting+','+'S', formatInformationT)
                folhaResults.write("B35", 'Tempo         [s]', bold)
                folhaResults.write_row("C35", self.display.slowLevel[0])
                folhaResults.write("B36", 'Amplitude [dB]', bold)
                folhaResults.write_row("C36", self.display.slowLevel[1])
                # Gráficos em linha
                plotLineI = planilha.add_chart({'type': 'line'})
                plotLineI.add_series({
                    'name': ['Results', 28,0],
                    'categories': ['Results', 28,2,28, self.display.impulseLevel[0].size],
                    'values': ['Results', 29,2,29, self.display.impulseLevel[1].size]
                    })
                plotLineI.set_title({'name': 'Sound pressure level measured in Impulse weighting'})
                plotLineI.set_x_axis({'name': 'Time s'})
                plotLineI.set_y_axis({'name': 'L'+self.display.Freqweighting+',I dB'})
                folhaResults.insert_chart('A38', plotLineI, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})
                folhaResults.write("G38", 'L'+self.display.Freqweighting+'I,máx', formatInformationT)
                folhaResults.write("H38", 'L'+self.display.Freqweighting+'I,mín', formatInformationT)
                folhaResults.write("G39", str(round(self.display.impulseLevel[1].max(), 2)).replace(".",","), formatInformationN)
                folhaResults.write("H39", str(round(self.display.impulseLevel[1].min(), 2)).replace(".",","), formatInformationN)
                folhaResults.merge_range(39,6,39,7, 'L'+self.display.Freqweighting+'eq,I Global', formatInformationT)
                folhaResults.merge_range(40,6,40,7, str(round(self.display.impulseLevelGlobal, 1)).replace(".",","), formatInformationN)
                
                plotLineF = planilha.add_chart({'type': 'line'})
                plotLineF.add_series({
                    'name': ['Results', 31,0],
                    'categories': ['Results', 31,2,31, self.display.fastLevel[0].size],
                    'values': ['Results', 32,2,32, self.display.fastLevel[1].size]
                    })
                plotLineF.set_title({'name': 'Sound pressure level measured in Flow weighting'})
                plotLineF.set_x_axis({'name': 'Time s'})
                plotLineF.set_y_axis({'name': 'L'+self.display.Freqweighting+',F dB'})
                folhaResults.insert_chart('I38', plotLineF, {'x_offset': 33, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})
                folhaResults.write("Q38", 'L'+self.display.Freqweighting+'F,máx', formatInformationT)
                folhaResults.write("R38", 'L'+self.display.Freqweighting+'F,mín', formatInformationT)
                folhaResults.write("Q39", str(round(self.display.fastLevel[1].max(), 2)).replace(".",","), formatInformationN)
                folhaResults.write("R39", str(round(self.display.fastLevel[1].min(), 2)).replace(".",","), formatInformationN)
                folhaResults.merge_range(39,16,39,17, 'L'+self.display.Freqweighting+'eq,F Global', formatInformationT)
                folhaResults.merge_range(40,16,40,17, str(round(self.display.fastLevelGlobal, 1)).replace(".",","), formatInformationN)
                
                plotLineS = planilha.add_chart({'type': 'line'})
                plotLineS.add_series({
                    'name': ['Results', 34,0],
                    'categories': ['Results', 34,2,34, self.display.slowLevel[0].size],
                    'values': ['Results', 35,2,35, self.display.slowLevel[1].size]
                    })
                plotLineS.set_title({'name': 'Sound pressure level measured in Slow weighting'})
                plotLineS.set_x_axis({'name': 'Time s'})
                plotLineS.set_y_axis({'name': 'L'+self.display.Freqweighting+',S dB'})
                folhaResults.insert_chart('T38', plotLineS, {'x_offset': -33, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})
                folhaResults.write("AA38", 'L'+self.display.Freqweighting+'S,máx', formatInformationT)
                folhaResults.write("AB38", 'L'+self.display.Freqweighting+'S,mín', formatInformationT)
                folhaResults.write("AA39", str(round(self.display.slowLevel[1].max(), 2)).replace(".",","), formatInformationN)
                folhaResults.write("AB39", str(round(self.display.slowLevel[1].min(), 2)).replace(".",","), formatInformationN)
                folhaResults.merge_range(39,26,39,27, 'L'+self.display.Freqweighting+'eq,S Global', formatInformationT)
                folhaResults.merge_range(40,26,40,27, str(round(self.display.slowLevelGlobal, 1)).replace(".",","), formatInformationN)
                
                # Gráfico em barras
                plotOctave = planilha.add_chart({'type': 'column'})
                plotOctave.add_series({
                    'name': ['Results', 2,0],
                    'categories': ['Results', 1,1,0,self.display.freqs.size],
                    'values': ['Results', 2,1,2,self.display.freqs.size]
                    })
                plotOctave.add_series({
                    'name': ['Results', 3,0],
                    'categories': ['Results', 1,1,0,self.display.freqs.size],
                    'values': ['Results', 3,1,3,self.display.freqs.size]
                    })
                plotOctave.add_series({
                    'name': ['Results', 4,0],
                    'categories': ['Results', 1,1,0,self.display.freqs.size],
                    'values': ['Results', 4,1,4,self.display.freqs.size]
                    })
                plotOctave.set_title({'name': 'Sound pressure level measured in 1/'+str(self.display.ffraction)+' octave bands'})
                plotOctave.set_x_axis({'name': 'Frequency Hz'})
                plotOctave.set_y_axis({'name': 'L'+self.display.Freqweighting+','+timeStrIdx+' dB'})
                if self.display.ffraction == 1:
                    folhaResults.insert_chart('A7', plotOctave, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1.65, 'y_scale': 1})
                    folhaResults.merge_range(6,12,6,13, 'L'+self.display.Freqweighting+'eq,'+timeStrIdx+' Global', formatInformationT)
                    folhaResults.merge_range(7,12,7,13, str(round(self.display.globalLevel, 1)).replace(".",","), formatInformationN)
                else:
                    folhaResults.insert_chart('A7', plotOctave, {'x_offset': 0, 'y_offset': 0, 'x_scale': 2, 'y_scale': 1.4})
                    folhaResults.merge_range(6,15,6,16, 'L'+self.display.Freqweighting+'eq,'+timeStrIdx+' Global', formatInformationT)
                    folhaResults.merge_range(7,15,7,16, str(round(self.display.globalLevel, 1)).replace(".",","), formatInformationN)
            else:
                if dlgSave.saveAll:
                    # Folha de sinais referência
                    folhaReferencia.set_column(0,1,20)
                    folhaReferencia.merge_range(0,0,0,1, 'Reference signals', formatSection)
                    folhaReferencia.write("A2", "Impulsive response", bold)
                    folhaReferencia.write_column("A3", self.display.IR.timeSignal)
                    folhaReferencia.write("B2", "Calibração", bold)
                    folhaReferencia.write_column("B3", self.display.cacheSetup['calibRec'][0])
                # Folha de configurações do template
                if self.cacheSetup['method'][0] == 'pinkNoise': method = 'Pink noise'
                if self.cacheSetup['method'][0] == 'whiteNoise': method = 'White noise'
                if self.cacheSetup['method'][0] == 'sweepExponencial': method = 'Exponential Sweep'
                # Folha de configurações do template
                folhaSetup.set_column(1,1,20)
                folhaSetup.merge_range(0,0,0,1, 'Measurement setup', formatSection)
                folhaSetup.set_column(0,0,25,bold)
                folhaSetup.set_column(1,1,20)
                folhaSetup.write("A2", "Template");                 folhaSetup.write("B2", "Reverberation Time")
                folhaSetup.write("A3", "Frequency range");          folhaSetup.write("B3", freqStr[0]+' Hz to '+freqStr[-1]+'Hz')
                folhaSetup.write("A4", "Octave band");             folhaSetup.write("B4", '1/'+str(self.display.ffraction))
                folhaSetup.write("A5", "Excitement signal");       folhaSetup.write("B5", method)
                folhaSetup.write("A6", "Signal duration");         folhaSetup.write("B6", str(self.display.duration-1).replace(".",",")+' s')
                folhaSetup.write("A7", "Escape time");          folhaSetup.write("B7", str(self.display.startMargin).replace(".",",")+' s')
                folhaSetup.write("A8", "Decay time");      folhaSetup.write("B8", str(self.display.stopMargin).replace(".",",")+' s')
                folhaSetup.write("A9", "Averages");                   folhaSetup.write("B9", str(int(self.display.average+1)))
                folhaSetup.write("A10", "Integration time");      folhaSetup.write("B10", timeStr)
                # Folha de Results
                folhaResults.merge_range(0,0,0,self.display.freqs.size, 'Frequency Analysis', formatSection)
                folhaResults.set_column(0,0,25,bold)
                folhaResults.set_row(0,15,bold)
                folhaResults.write("A2", "Frequency [Hz]")
                folhaResults.write("A3", "EDT [S]")
                folhaResults.write("A4", "T10 [S]")
                folhaResults.write("A5", "T20 [S]")
                folhaResults.write("A6", "T30 [S]")
                for i in range(len(freqStr)):
                    folhaResults.write(1, i+1, freqStr[i])
                    folhaResults.write(2, i+1, round(self.display.RT['EDT'][i], 2))
                    folhaResults.write(3, i+1, round(self.display.RT['T10'][i], 2))
                    folhaResults.write(4, i+1, round(self.display.RT['T20'][i], 2))
                    folhaResults.write(5, i+1, round(self.display.RT['T30'][i], 2))
                # Gráfico em barras do TR
                plotOctave = planilha.add_chart({'type': 'column'})
                plotOctave.add_series({
                    'name': ['Results', 2,0],
                    'categories': ['Results', 1,1,0,self.display.freqs.size],
                    'values': ['Results', 2,1,2,self.display.freqs.size]
                    })
                plotOctave.add_series({
                    'name': ['Results', 3,0],
                    'categories': ['Results', 1,1,0,self.display.freqs.size],
                    'values': ['Results', 3,1,3,self.display.freqs.size]
                    })
                plotOctave.add_series({
                    'name': ['Results', 4,0],
                    'categories': ['Results', 1,1,0,self.display.freqs.size],
                    'values': ['Results', 4,1,4,self.display.freqs.size]
                    })
                plotOctave.add_series({
                    'name': ['Results', 5,0],
                    'categories': ['Results', 1,1,0,self.display.freqs.size],
                    'values': ['Results', 5,1,5,self.display.freqs.size]
                    })
                plotOctave.set_title({'name': 'Reverberation Time measured in 1/'+str(self.display.ffraction)+' octave bands'})
                plotOctave.set_x_axis({'name': 'Frequency Hz'})
                plotOctave.set_y_axis({'name': 'Tempo s'})
                
                # Relação Sinal Ruído
                folhaResults.merge_range(27,0,27,self.display.freqs.size, 'Signal-to-Noise Ratio', formatSection)
                folhaResults.set_row(0,15,bold)
                folhaResults.write("A29", "Frequency                  [Hz]")
                folhaResults.write("A30", "Impulsive response [dB]")
                folhaResults.write("A31", "Background noise         [dB]")
                folhaResults.write("A32", "SNR                                [dB]")
                for i in range(len(freqStr)):
                    folhaResults.write(28, i+1, freqStr[i])
                    folhaResults.write(29, i+1, round(self.display.Level_measuredData[i], 2))
                    folhaResults.write(30, i+1, round(self.display.Level_floorNoise[i], 2))
                    folhaResults.write(31, i+1, round(self.display.SNR[i], 2))
                    
                # Gráfico em barras da SNR
                plotSNR = planilha.add_chart({'type': 'column'})
                plotSNR.add_series({
                    'name': ['Results', 29,0],
                    'categories': ['Results', 1,1,0,self.display.freqs.size],
                    'values': ['Results', 29,1,29,self.display.freqs.size]
                    })
                plotSNR.add_series({
                    'name': ['Results', 30,0],
                    'categories': ['Results', 1,1,0,self.display.freqs.size],
                    'values': ['Results', 30,1,30,self.display.freqs.size]
                    })
                plotSNR.add_series({
                    'name': ['Results', 31,0],
                    'categories': ['Results', 1,1,0,self.display.freqs.size],
                    'values': ['Results', 31,1,31,self.display.freqs.size]
                    })
                # plotSNR.add_series({
                #     'name': ['Results', 32,0],
                #     'categories': ['Results', 1,1,0,self.display.freqs.size],
                #     'values': ['Results', 5,1,5,self.display.freqs.size]
                #     })
                plotSNR.set_title({'name': 'Relação Sinal-Ruido medido em 1/'+str(self.display.ffraction)+' de oitava'})
                plotSNR.set_x_axis({'name': 'Frequency Hz'})
                plotSNR.set_y_axis({'name': 'Amplitude dB'})
                
                if self.display.ffraction == 1:
                    folhaResults.insert_chart('A7', plotOctave, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1.65, 'y_scale': 1})
                    folhaResults.insert_chart('A33', plotSNR, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1.65, 'y_scale': 1})
                else:
                    folhaResults.insert_chart('A7', plotOctave, {'x_offset': 0, 'y_offset': 0, 'x_scale': 3, 'y_scale': 2})
                    folhaResults.insert_chart('A33', plotSNR, {'x_offset': 0, 'y_offset': 0, 'x_scale': 3, 'y_scale': 2})
            planilha.close()
            
            os.chdir(path_main)
            savemat('projectInfos.mat', {'name': dataProject['name'][0], 'numMed': dataProject['numMed'][0][0] + 1})
            self.return_pyaudioStream()
            
            
    def btnQuit_Action(self):
        self.display.key = False
        app.quit()
        self.close()

class setSetup(QtWidgets.QDialog, guiSetup):
    '''Class setSetup, criada para instânciar a interface gráfica guiSetup.py,
    onde os parâmetros de entrada do MNPS são alterados pelo usuário.'''
    def __init__(self, parent=None):
        super(setSetup, self).__init__(parent)
        self.setupUi(self)
        self.returnDisplay=False
        self.btnCancel.clicked.connect(self.btnCancel_Action)
        self.btnApply.clicked.connect(self.btnApply_Action)
        self.btnCalibrate.clicked.connect(self.btnCalibre_Action)
        self.Template={0: 'frequencyAnalyser', 1: 'reverberationTime'}
        self.Fraction={0: 1, 1: 3}
        self.Method={0: 'sweepExponencial', 1: 'whiteNoise', 2: 'pinkNoise'}
        self.Freqweighting={0: 'A', 1: 'C', 2: 'Z'}
        self.Timeweighting={0: 0.035, 1: 0.125, 2: 1.000}
        self.Timeweightingstr={0: 'Impulse', 1: 'Fast', 2: 'Slow'}
        self.cacheSetup = loadmat('cacheSetup.mat')

        '''Update nativo do Qt interval = 1s = 1000ms'''
        self.qTimer = QtCore.QTimer()
        self.qTimer.setInterval(250)
        self.qTimer.timeout.connect(self.update)
        self.qTimer.start()

        self.setMethod          = self.cacheSetup['method'][0]
        self.setTemplate        = self.cacheSetup['template'][0]
        self.setAverage         = self.cacheSetup['average'][0][0]
        self.setFreqmin         = self.cacheSetup['freqMin'][0][0]
        self.setFreqmax         = self.cacheSetup['freqMax'][0][0]
        self.setFraction        = self.cacheSetup['fraction'][0][0]
        self.setStartmargin     = self.cacheSetup['startMargin'][0][0]
        self.setStopmargin      = self.cacheSetup['stopMargin'][0][0]
        self.setDurationsignal  = self.cacheSetup['durationSignal'][0][0]
        self.setDurationmeasure = self.cacheSetup['durationMeasure'][0][0]
        self.setCorrecao        = self.cacheSetup['correcao'][0][0]
        self.setSensitivity   = self.cacheSetup['Sensitivity'][0][0]
        self.setCalibration     = self.cacheSetup['calibrationFC'][0][0]
        self.setcalibRec        = self.cacheSetup['calibRec'][0]
        self.setFreqweighting   = self.cacheSetup['inFreqweighting'][0][0]
        self.setTimeweighting   = self.cacheSetup['inTimeweighting'][0][0]
        self.minMed, self.secMed = divmod(int(self.setDurationmeasure), 60)
        
        if self.setTemplate == 'frequencyAnalyser': self.inTemplate.setCurrentIndex(0)
        if self.setTemplate == 'reverberationTime': self.inTemplate.setCurrentIndex(1)
        if self.setMethod == 'sweepExponencial': self.inMethod.setCurrentIndex(0)
        if self.setMethod == 'whiteNoise': self.inMethod.setCurrentIndex(1)
        if self.setMethod == 'pinkNoise': self.inMethod.setCurrentIndex(2)
        if self.setFraction == 1: self.inFraction.setCurrentIndex(0)
        if self.setFraction == 3: self.inFraction.setCurrentIndex(1)
        if self.setFreqweighting == 'A': self.inFreqweighting.setCurrentIndex(0)
        if self.setFreqweighting == 'C': self.inFreqweighting.setCurrentIndex(1)
        if self.setFreqweighting == 'Z': self.inFreqweighting.setCurrentIndex(2)
        if self.setTimeweighting == 0.035: self.inTimeweighting.setCurrentIndex(0)
        if self.setTimeweighting == 0.125: self.inTimeweighting.setCurrentIndex(1)
        if self.setTimeweighting == 1.000: self.inTimeweighting.setCurrentIndex(2)
        self.inDurationMeasure.setTime(QtCore.QTime(0, self.minMed, self.secMed))
        self.inDurationSignal.setValue(self.setDurationsignal)
        self.inFreqmax.setValue(self.setFreqmax)
        self.inFreqmin.setValue(self.setFreqmin)
        self.inStartmargin.setValue(self.setStartmargin)
        self.inStopmargin.setValue(self.setStopmargin)
        self.inAverage.setValue(self.setAverage)
        self.lblFTC.setText(str(self.setCorrecao).replace(".",",") + " dB")
        self.inFTC = self.setCorrecao
        global algo, mins, secs
        algo = self.inDurationMeasure
        mins = self.minMed; secs = self.secMed
        
    def update(self):
        if self.inTemplate.currentIndex() == 1:
            self.groupBox_SinalExcit.setEnabled(True)
            self.inDurationMeasure.setEnabled(False)
            self.inTimeweighting.setEnabled(False)
            self.inTimeweighting.setItemText(self.inTimeweighting.currentIndex(), "Slow")
            self.inFreqweighting.setEnabled(False)
            self.inFreqweighting.setItemText(self.inFreqweighting.currentIndex(), "Z")
        else:
            self.groupBox_SinalExcit.setEnabled(False)
            self.inDurationMeasure.setEnabled(True)
            self.inFreqweighting.setEnabled(True)
            self.inFreqweighting.setItemText(self.inFreqweighting.currentIndex(),
                                             self.Freqweighting[self.inFreqweighting.currentIndex()])
            self.inTimeweighting.setEnabled(True)
            self.inTimeweighting.setItemText(self.inTimeweighting.currentIndex(),
                                             self.Timeweightingstr[self.inTimeweighting.currentIndex()])
       
        if self.Template[self.inTemplate.currentIndex()] != self.setTemplate \
        or self.Method[self.inMethod.currentIndex()] != self.setMethod\
        or self.Freqweighting[self.inFreqweighting.currentIndex()] != self.setFreqweighting\
        or self.Timeweighting[self.inTimeweighting.currentIndex()] != self.setTimeweighting\
        or self.Fraction[self.inFraction.currentIndex()] !=  self.setFraction\
        or self.inFreqmin.value() != self.setFreqmin\
        or self.inFreqmax.value() != self.setFreqmax\
        or self.inStartmargin.value() != self.setStartmargin\
        or self.inStopmargin.value() != self.setStopmargin\
        or self.inDurationSignal.value() != self.setDurationsignal\
        or self.inDurationMeasure.time().minute() != self.minMed\
        or self.inDurationMeasure.time().second() != self.secMed\
        or self.inAverage.value() != self.setAverage\
        or self.inFTC != self.setCorrecao:
            self.btnApply.setEnabled(True)
        else:
            self.btnApply.setEnabled(False)
        # QtCore.QTimer.singleShot(250, self.update) # QUICKLY repeat

    def btnCalibre_Action(self):
        dlgCalibration = calib()
        dlgCalibration.setup=True
        dlgCalibration.update()
        dlgCalibration.exec_()
        if dlgCalibration.returnDisplay:
            self.return_pyaudioStream()
        if dlgCalibration.accept:
            self.setCorrecao      = dlgCalibration.display.correcao
            self.setSensitivity = dlgCalibration.display.Sensitivity
            self.setCalibration   = dlgCalibration.display.FC
            self.lblFTC.setText(str(self.setCorrecao).replace(".",",") + " dB")
            self.inFTC            = self.setCorrecao
            self.setcalibRec      = dlgCalibration.display.correctedData

    def btnApply_Action(self):
        self.qTimer.stop()
        if self.Template[self.inTemplate.currentIndex()] == 'reverberationTime':
            self.inFreqweighting.setCurrentIndex(2)
            self.inTimeweighting.setCurrentIndex(2)
        else:
            self.inAverage.setProperty("value", 1)
        self.setDurationmeasure = self.inDurationMeasure.time().minute()*60 + self.inDurationMeasure.time().second()
        savemat('cacheSetup.mat',
             {'template':        self.Template[self.inTemplate.currentIndex()],
              'method':          self.Method[self.inMethod.currentIndex()],
              'average':         self.inAverage.value(),
              'fraction':        self.Fraction[self.inFraction.currentIndex()],
              'freqMin':         self.inFreqmin.value(),
              'freqMax':         self.inFreqmax.value(),
              'startMargin':     self.inStartmargin.value(),
              'stopMargin':      self.inStopmargin.value(),
              'durationSignal':  self.inDurationSignal.value(),
              'durationMeasure': self.setDurationmeasure,
              'calibrationFC':   self.setCalibration,
              'inFreqweighting': self.Freqweighting[self.inFreqweighting.currentIndex()],
              'inTimeweighting': self.Timeweighting[self.inTimeweighting.currentIndex()],
              'Sensitivity':   self.setSensitivity,
              'correcao':        self.setCorrecao,
              'calibRec':        self.setcalibRec})
        self.close()
        self.returnDisplay=True
        
    def btnCancel_Action(self):
        self.qTimer.stop()
        self.close()
        self.returnDisplay=True


class calib(QtWidgets.QDialog, guiCalib):
    def __init__(self, parent=None):
        super(calib, self).__init__(parent)
        self.setupUi(self)
        self.returnDisplay = False
        self.setup         = False
        self.accept        = False
        self.duration      = 10
        self.countdown     = self.duration
        self.graphicCalibration.plotItem.showGrid(False, True, 0.7)
        self.graphicCalibration.plotItem.setLogMode(x=True, y=False)
        self.graphicCalibration.setYRange(-40,120)
        self.graphicCalibration.setXRange(1.3010299956639813,4.301029995663981, padding=0)
        self.graphicCalibration.setLabel('left', "NPS dB")
        self.graphicCalibration.setLabel('bottom', "Frequency Hz")

        '''Update nativo do Qt interval = 1s = 1000ms'''
        self.qTimer = QtCore.QTimer()
        self.qTimer.setInterval(0.2)
        self.qTimer.timeout.connect(self.update)
        
        self._translate = QtCore.QCoreApplication.translate
        self.btnCancel.clicked.connect(self.btnCancel_Action)
        self.btnCancel.setEnabled(False)
        self.btnAccept.clicked.connect(self.btnAccept_Action)
        self.btnAccept.setEnabled(False)
        self.cacheSetup         = loadmat('cacheSetup.mat')
        self.setMethod          = self.cacheSetup['method'][0]
        self.setTemplate        = self.cacheSetup['template'][0]
        self.setFreqmin         = self.cacheSetup['freqMin'][0][0]
        self.setFreqmax         = self.cacheSetup['freqMax'][0][0]
        self.setFraction        = self.cacheSetup['fraction'][0][0]
        self.setStartmargin     = self.cacheSetup['startMargin'][0][0]
        self.setStopmargin      = self.cacheSetup['stopMargin'][0][0]
        self.setDurationsignal  = self.cacheSetup['durationSignal'][0][0]
        self.setDurationmeasure = self.cacheSetup['durationMeasure'][0][0]
        self.setCalibration     = self.cacheSetup['calibrationFC'][0][0]
        self.setFreqweighting   = self.cacheSetup['inFreqweighting'][0][0]
        self.setTimeweighting   = self.cacheSetup['inTimeweighting'][0][0]
        self.setAverage         = self.cacheSetup['average'][0][0]
        self.setSensitivity   = self.cacheSetup['Sensitivity'][0][0]
        self.setCorrecao        = self.cacheSetup['correcao'][0][0]
        self.samplingRate       = default.samplingRate
        self.display            = pyaudioStream(device        = default.device,
                                                samplingRate   = self.samplingRate,
                                                duration       = self.duration,
                                                inputChannels  = default.inputChannels,
                                                outputChannels = default.outChannels,
                                                timeConstant   = 0.3,
                                                fstart         = 20,
                                                fstop          = 20000,
                                                ffraction      = 1,
                                                Freqweighting  = 'Z',
                                                average        = 1,
                                                template       = 'calibration')
        self.display.streamStart()
        
        self.lblSens.setText(self._translate("Dialog", " "))
        self.lblStrSens.setText(self._translate("Dialog", " "))
        self.lblCorr.setText(self._translate("Dialog", " "))
        self.lblStrCorr.setText(self._translate("Dialog", " "))
        self.qTimer.start()

    def update(self):
        if not self.display.Level is None:
            self.countdown = round(self.duration - self.display.framesRead/self.samplingRate, 1)
            if self.countdown > 0:
                self.mins, self.secs = divmod(int(self.countdown), 60)
                self.timeformat = '{:02d}:{:02d}'.format(self.mins, self.secs)
                self.lblDnTime.setText(self._translate("Dialog", "<html><head/><body><p align=\"center\">Performing calibration..."+\
                                                       "</p><p align=\"center\">Please wait "+self.timeformat+"</p></body></html>"))
                self.MaxLevel.setText(str(rd(self.display.Level[self.display.idMax], 2)).replace(".",","))
                self.freqMax.setText(str(rd(self.display.freqVector[self.display.idMax], 2)).replace(".",","))
            else:
                self.lblDnTime.setText(self._translate("Dialog", "<html><head/><body><p align=\"center\">Performing calibration..."+\
                                                       "</p><p align=\"center\">Please wait 00:00</p></body></html>"))
            if self.display.key:
                self.lblSens.setText(self._translate("Dialog", " "))
                self.lblStrSens.setText(self._translate("Dialog", " "))
                pen=pyqtgraph.mkPen(color='c')
                if self.display.freqVector.size == self.display.Level.size:
                    self.graphicCalibration.plot(self.display.freqVector, self.display.Level, pen=pen, clear=True)
                else:
                    pass
            else:
                self.strSens = str(self.display.Sensitivity*1000).replace(".",",")
                self.lblStrSens.setText(self._translate("Dialog", "Sensitivity"))
                self.lblSens.setText(self._translate("Dialog", self.strSens + ' mV/Pa'))
                self.strCorr = str(self.display.correcao).replace(".",",")
                self.lblStrCorr.setText(self._translate("Dialog", "Correction"))
                self.lblCorr.setText(self._translate("Dialog", str(self.strCorr) + ' dB'))
                self.MaxLevel.setText(str(round(self.display.Level[self.display.idMax], 2)).replace(".",","))
                self.freqMax.setText(str(round(self.display.freqVector[self.display.idMax], 0)).replace(".",","))
                self.btnAccept.setEnabled(True)
                self.btnCancel.setEnabled(True)
                self.qTimer.stop()

    def btnAccept_Action(self):
        savemat('cacheSetup.mat',
             {'template':        self.setTemplate,
              'method':          self.setMethod,
              'fraction':        self.setFraction,
              'freqMin':         self.setFreqmin,
              'freqMax':         self.setFreqmax,
              'startMargin':     self.setStartmargin,
              'stopMargin':      self.setStopmargin,
              'durationSignal':  self.setDurationsignal,
              'durationMeasure': self.setDurationmeasure,
              'calibrationFC':   self.display.FC,
              'inFreqweighting': self.setFreqweighting,
              'inTimeweighting': self.setTimeweighting,
              'average':         self.setAverage,
              'correcao':        self.display.correcao,
              'Sensitivity':     self.display.Sensitivity,
              'calibRec':        self.display.correctedData})

        if self.setup:
            self.accept=True
            self.close()
        else:
            self.close()
            self.returnDisplay=True

    def btnCancel_Action(self):
        if self.setup:
            self.close()
        else:
            self.close()
            self.returnDisplay=True



class about(QtWidgets.QDialog, guiAbout):
    def __init__(self, parent=None):
        super(about, self).__init__(parent)
        self.setupUi(self)
        self.btnOk.clicked.connect(self.btnOk_Action)
        self.returnDisplay=False


    def btnOk_Action(self):
        self.returnDisplay=True
        self.close()


class save(QtWidgets.QDialog, guiSave):
    def __init__(self, parent=None):
        super(save, self).__init__(parent)
        self.setupUi(self)
        self.btnSaveAll.clicked.connect(self.btnSaveAll_Action)
        self.btnNoSaveAll.clicked.connect(self.btnNoSaveAll_Action)
        self.clicked=False


    def btnSaveAll_Action(self):
        self.saveAll=True
        self.clicked=True
        self.close()
        
    def btnNoSaveAll_Action(self):
        self.saveAll=False
        self.clicked=True
        self.close()
        
        
class newProject(QtWidgets.QDialog, guiProject):
    def __init__(self, parent=None):
        super(newProject, self).__init__(parent)
        self.setupUi(self)
        os.chdir(path_project)
        self.allProjects = os.listdir(".")
        self.returnDisplay=False
        self.btnCreate.setEnabled(False)
        self.minStr = ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p",\
                        "a", "s", "d", "f", "g", "h", "j", "k", "l", "ç",\
                        "z", "x", "c", "v", "b", "n", "m"]
        self.maiStr = list(map(str.upper, self.minStr))
        self.upper = False
        self.qTimer = QtCore.QTimer()
        self.qTimer.setInterval(100)
        self.qTimer.timeout.connect(self.update)
        self.vk_a.clicked.connect(self.vk_aAction);   self.vk_b.clicked.connect(self.vk_bAction)
        self.vk_c.clicked.connect(self.vk_cAction);   self.vk_d.clicked.connect(self.vk_dAction)
        self.vk_e.clicked.connect(self.vk_eAction);   self.vk_f.clicked.connect(self.vk_fAction)
        self.vk_g.clicked.connect(self.vk_gAction);   self.vk_h.clicked.connect(self.vk_hAction)
        self.vk_i.clicked.connect(self.vk_iAction);   self.vk_j.clicked.connect(self.vk_jAction)
        self.vk_k.clicked.connect(self.vk_kAction);   self.vk_l.clicked.connect(self.vk_lAction)
        self.vk_m.clicked.connect(self.vk_mAction);   self.vk_n.clicked.connect(self.vk_nAction)
        self.vk_o.clicked.connect(self.vk_oAction);   self.vk_p.clicked.connect(self.vk_pAction)
        self.vk_q.clicked.connect(self.vk_qAction);   self.vk_r.clicked.connect(self.vk_rAction)
        self.vk_s.clicked.connect(self.vk_sAction);   self.vk_t.clicked.connect(self.vk_tAction)
        self.vk_u.clicked.connect(self.vk_uAction);   self.vk_v.clicked.connect(self.vk_vAction)
        self.vk_w.clicked.connect(self.vk_wAction);   self.vk_x.clicked.connect(self.vk_xAction)
        self.vk_y.clicked.connect(self.vk_yAction);   self.vk_z.clicked.connect(self.vk_zAction)
        self.vk_cc.clicked.connect(self.vk_ccAction); self.vk_0.clicked.connect(self.vk_0Action)
        self.vk_1.clicked.connect(self.vk_1Action);   self.vk_2.clicked.connect(self.vk_2Action)
        self.vk_3.clicked.connect(self.vk_3Action);   self.vk_4.clicked.connect(self.vk_4Action)
        self.vk_5.clicked.connect(self.vk_5Action);   self.vk_6.clicked.connect(self.vk_6Action)
        self.vk_7.clicked.connect(self.vk_7Action);   self.vk_8.clicked.connect(self.vk_8Action)
        self.vk_9.clicked.connect(self.vk_9Action)
        self.vk_underscore.clicked.connect(self.vk_underscoreAction)
        self.delAll.clicked.connect(self.delAllAction)
        self.capsLock.clicked.connect(self.btncapsLock)
        self.space.clicked.connect(self.spaceAction)
        self.backspace.clicked.connect(self.backspaceAction)
        self.btnCancel.clicked.connect(self.btnCancel_Action)
        self.btnCreate.clicked.connect(self.btnCreate_Action)
        self.qTimer.start()
        
        
    def update(self):
        if self.entryProjectname.toPlainText() == "":
            self.btnCreate.setEnabled(False)
        elif self.entryProjectname.toPlainText() in self.allProjects:
            self.btnCreate.setEnabled(False)
        else:
            self.btnCreate.setEnabled(True)
        if self.upper:
            self.vk_q.setText(self.maiStr[0]);  self.vk_w.setText(self.maiStr[1])
            self.vk_e.setText(self.maiStr[2]);  self.vk_r.setText(self.maiStr[3])
            self.vk_t.setText(self.maiStr[4]);  self.vk_y.setText(self.maiStr[5])
            self.vk_u.setText(self.maiStr[6]);  self.vk_i.setText(self.maiStr[7])
            self.vk_o.setText(self.maiStr[8]);  self.vk_p.setText(self.maiStr[9])
            self.vk_a.setText(self.maiStr[10]); self.vk_s.setText(self.maiStr[11])
            self.vk_d.setText(self.maiStr[12]); self.vk_f.setText(self.maiStr[13])
            self.vk_g.setText(self.maiStr[14]); self.vk_h.setText(self.maiStr[15])
            self.vk_j.setText(self.maiStr[16]); self.vk_k.setText(self.maiStr[17])
            self.vk_l.setText(self.maiStr[18]); self.vk_cc.setText(self.maiStr[19])
            self.vk_z.setText(self.maiStr[20]); self.vk_x.setText(self.maiStr[21])
            self.vk_c.setText(self.maiStr[22]); self.vk_v.setText(self.maiStr[23])
            self.vk_b.setText(self.maiStr[24]); self.vk_n.setText(self.maiStr[25])
            self.vk_m.setText(self.maiStr[26])
        else:
            self.vk_q.setText(self.minStr[0]);  self.vk_w.setText(self.minStr[1])
            self.vk_e.setText(self.minStr[2]);  self.vk_r.setText(self.minStr[3])
            self.vk_t.setText(self.minStr[4]);  self.vk_y.setText(self.minStr[5])
            self.vk_u.setText(self.minStr[6]);  self.vk_i.setText(self.minStr[7])
            self.vk_o.setText(self.minStr[8]);  self.vk_p.setText(self.minStr[9])
            self.vk_a.setText(self.minStr[10]); self.vk_s.setText(self.minStr[11])
            self.vk_d.setText(self.minStr[12]); self.vk_f.setText(self.minStr[13])
            self.vk_g.setText(self.minStr[14]); self.vk_h.setText(self.minStr[15])
            self.vk_j.setText(self.minStr[16]); self.vk_k.setText(self.minStr[17])
            self.vk_l.setText(self.minStr[18]); self.vk_cc.setText(self.minStr[19])
            self.vk_z.setText(self.minStr[20]); self.vk_x.setText(self.minStr[21])
            self.vk_c.setText(self.minStr[22]); self.vk_v.setText(self.minStr[23])
            self.vk_b.setText(self.minStr[24]); self.vk_n.setText(self.minStr[25])
            self.vk_m.setText(self.minStr[26])
            
    def btnCancel_Action(self):
        self.returnDisplay=True
        self.qTimer.stop()
        os.chdir(path_main)
        self.close()
    def btnCreate_Action(self):
        # print(self.entryProjectname.toPlainText())
        self.returnDisplay=True
        self.qTimer.stop()
        # self.close()
        self.close()
        # cria uma pasta com o nome do projeto dentro da pasta projetos
        os.mkdir(self.entryProjectname.toPlainText())
        os.chdir(path_main)
        savemat('projectInfos.mat',
                {'name': self.entryProjectname.toPlainText(),
                 'numMed': 1})
    def btncapsLock(self): self.upper = not self.upper
    def vk_aAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_a.text())
    def vk_bAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_b.text())
    def vk_cAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_c.text())
    def vk_dAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_d.text())
    def vk_eAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_e.text())
    def vk_fAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_f.text())
    def vk_gAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_g.text())
    def vk_hAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_h.text())
    def vk_iAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_i.text())
    def vk_jAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_j.text())
    def vk_kAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_k.text())
    def vk_lAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_l.text())
    def vk_mAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_m.text())
    def vk_nAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_n.text())
    def vk_oAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_o.text())
    def vk_pAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_p.text())
    def vk_qAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_q.text())
    def vk_rAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_r.text())
    def vk_sAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_s.text())
    def vk_tAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_t.text())
    def vk_uAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_u.text())
    def vk_vAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_v.text())
    def vk_wAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_w.text())
    def vk_xAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_x.text())
    def vk_yAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_y.text())
    def vk_zAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_z.text())
    def vk_ccAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_cc.text())
    def spaceAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + ' ')
    def backspaceAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText()[:-1])
    def vk_0Action(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_0.text())
    def vk_1Action(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_1.text())
    def vk_2Action(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_2.text())
    def vk_3Action(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_3.text())
    def vk_4Action(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_4.text())
    def vk_5Action(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_5.text())
    def vk_6Action(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_6.text())
    def vk_7Action(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_7.text())
    def vk_8Action(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_8.text())
    def vk_9Action(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_9.text())
    def vk_underscoreAction(self): self.entryProjectname.setText(self.entryProjectname.toPlainText() + '_')
    def delAllAction(self): self.entryProjectname.setText('')

# %% Mainloop
if __name__=="__main__":
    app = QtWidgets.QApplication(sys.argv)
    startMNPS = MNPS()
    startMNPS.show()
    startMNPS.standby() #start with something
    app.exec_()