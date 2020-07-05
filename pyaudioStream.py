# -*- coding: utf-8 -*-
"""
Arquivo .py criado para manipular o sinal de entrada do microfone e alimentar
os gráficos e mostradores do MNPS)

author: @leonardojacomussi
"""

from numpy import float32, int32, asarray, empty, transpose, frombuffer, log2,\
                  loadtxt, angle, zeros, linspace, sqrt, log10, mean, fft,\
                  concatenate, where, sin, cos
from standards import ponderacaoA, ponderacaoC, ponderacaoZ, RT,\
                            impulse_level, fast_level, slow_level
from pyfilterbank import FractionalOctaveFilterbank as FOF
from pytta import SignalObj, generate
from acoustics import  generator
from scipy.io import loadmat
from scipy import interpolate
import threading
import pyaudio
import default
import time


class pyaudioStream(object):
    """
    A classe pyaudioStream realiza a leitura e tratamento dos dados em tempo real
    para exibir os dados no display do MNPS.
    
    Parâmetros de entrada:
        -> template: conjunto de ferramentas específicas pré-programadas para
                    o tipo de medição que deseja realizar. Podem ser escolhidos
                    entre "frequencyAnalyser" (medição de NPS com filtros de
                    bandas de oitava), "reverberationTime" (medição de tempo de
                    reverberação) e "None", quando em modo stand-by.
                    
        -> device: [in, out]
                   vetor de números inteiros correspondentes aos dispositivos
                   que realizarão a leitura. A lista de dispositivos pode ser 
                   obtida pelo package pytta com o método pytta.list_devices().
                   obs.: Caso seja fornecido apenas um dispositivo, será consi-
                   derado como dispositivo de entrada e saída.
                   
                   
        -> samplingRate: taxa de amostragem do dispositivo ADC, dada em Hertz.
                         Exemplo: 44100.
                         
        -> inputChannels: número inteiro correspondente ao canal de entrada
                          do dispositivo utilizado.
                          
        -> outputChannels: número inteiro correspondente ao canal de saída
                          do dispositivo utilizado.
                          
        -> timeConstant: número inteiro ou decimal correspondente a pon-
                         deração temporal do mostrador de dados.
                         
                         Normalmente são tomados os seguintes valores:
                             0.125 (modo FAST), 1.000 (modo SLOW) ou 0.035 (modo
                             IMPULSE).
                             
        -> fstart: frequência mínima de análise, dada em Hertz. Exemplo: 20
        
        -> fstop: frequência máxima de análise, dada em Hertz. Exemplo: 20000
        
        -> ffraction: número inteiro correspondente ao número de bandas por
                      oitava. Exemplo: se ffraction=3, tem-se 1/3, ou seja,
                      3 bandas por oitava == 1/ffraction.
                      
        -> Freqweighting: Ponderação na frequência. Podem ser escolhidas as curvas
                          de ponderação A, C e Z.
                          
        -> method: tipo de sinal de excitação. Podem ser escolhidos entre sweep
                   exponencial, ruído branco e ruído rosa.
                   
        -> duration: se o template for "frequencyAnalyser" é o tempo de registro
                     da medição, se o template for "reverberationTime" é o tempo
                     efetivo do sinal de excitação (considerando que há o tempo
                     de silêncio no final e no início do sinal (startMargin e
                     stopMargin)).
                     
        -> startMargin: tempo de silêncio no início do sinal de excitação. Neces-
                        sário devido ao pico de energia no circuito elétrico dos
                        alto-falantes ao abrir o canal do amplificador de potência.
                        
        -> stopMargin: tempo de silêncio no final do sinal de excitação. Necessá-
                       rio para captar o decaimento da energia sonora na sala.
                       
        -> average: número de medições de tempo de reverberação a serem feitas
                    para determinar a média, de acordo com a norma ISO 3382-1:2009.
    """
    def __init__(self, device  =  default.device,
                 samplingRate  =  default.samplingRate,
                 inputChannels =  default.inputChannels,
                 outputChannels=  default.outChannels,
                 timeConstant  =  default.timeConstant, 
                 fstart        =  default.freqMin, 
                 fstop         =  default.freqMax, 
                 ffraction     =  default.fraction,
                 Freqweighting =  default.Freqweighting,
                 duration      =  5.0,
                 startMargin   =  2.0,
                 stopMargin    =  6.0,
                 template      =  'stand-by',
                 method        =  str,
                 average       = None):
        self.device        = device
        self.samplingRate  = samplingRate
        self.inputChannels = inputChannels
        self.outputChannels= outputChannels
        self.timeConstant  = timeConstant
        self.fstart        = fstart
        self.fstop         = fstop
        self.ffraction     = ffraction
        self.Freqweighting = Freqweighting
        self.duration      = duration + 1
        self.numSamples    = int(self.duration*self.samplingRate)
        self.fftDegree     = log2(self.numSamples)
        self.template      = template
        self.timeSNR       = 5
        self.startMargin   = startMargin + self.timeSNR
        self.stopMargin    = stopMargin
        self.method        = method
        self.average       = average
        self.pause         = False
        self.stop          = False
        self.rec           = False
        if self.average != None:
            self.average = self.average - 1
        if len(self.device) > 1:
            self.inDevice  = self.device[0]
            self.outDevice = self.device[1]
        else:
            self.inDevice  = self.device[0]
            self.outDevice = self.device[0]
        # Filtro de frequências Pyfilterbank
        self.startBand, self.stopBand = findBand(self.fstart, self.fstop,\
                                                 self.ffraction)
        self.pyfilterbank = FOF(sample_rate = default.samplingRate,\
                                order       = 8,\
                                nth_oct     = self.ffraction,\
                                norm_freq   = 1000.0,\
                                start_band  = self.startBand,\
                                end_band    = self.stopBand,\
                                filterfun   = 'py')
        
        # Frequências nominais usadas no eixo "x" dos plots
        self.freqs = nominal_frequencies(self.pyfilterbank.center_frequencies,\
                                         self.ffraction)
        # self.freqs = self.pyfilterbank.center_frequencies
        self.eixoX = asarray(range(self.freqs.size), dtype=int32)
        self.strFreq = list()
        for idx in range (self.freqs.size):
            if idx == 0:
                f = round(self.freqs[idx], 1)
                self.strFreq.append((idx, str(f).replace(".", ",")))
            elif self.freqs[idx] == 1000:
                f = self.freqs[idx]/1000
                f = round(f, 1)
                self.strFreq.append((idx, str(f).replace(".", ",")+" k"))
            elif idx == (self.freqs.size-1):
                f = self.freqs[idx]/1000
                f = round(f, 1)
                self.strFreq.append((idx, str(f).replace(".", ",")+" k"))
            else:
                self.strFreq.append((idx, ''))
        # Variáveis da stream
        self.ResultKey    = False
        self.frames       = int(self.samplingRate * self.timeConstant)
        self.framesRead   = 0
        self.p            = pyaudio.PyAudio()
        self.Level        = None
        self.inData       = None
        self.FC           = float()
        self.idMax        = None
        self.cacheSetup   = loadmat('cacheSetup.mat')
        self.FCalibration = self.cacheSetup['calibrationFC'][0][0]
        super().__init__()
        
    def streamStart(self):
        '''
        Método que dá início a stream de áudio.
        '''
        self.inData=None
        self.Level=None
        self.key=True # False para finalizar o fluxo
        if self.template == 'reverberationTime':
            self.rec = True
            if self.method == 'sweepExponencial':
                self.vec_startMargin = zeros(int(self.startMargin*self.samplingRate),\
                                                dtype=float32)
                self.vec_stopMargin = zeros(int(self.stopMargin*self.samplingRate),\
                                                dtype=float32)
                self.excitation = generate.sweep(freqMin  = self.fstart,\
                                             freqMax      = self.fstop,\
                                             samplingRate = self.samplingRate,\
                                             fftDegree    = self.fftDegree,\
                                             startMargin  = 0,\
                                             stopMargin   = 0,\
                                             method       = 'logarithmic',\
                                             windowing    = 'hann')
                self.excitation = concatenate((self.vec_startMargin,\
                                               self.excitation.timeSignal,\
                                                 self.vec_stopMargin), axis=None)
                del self.vec_startMargin, self.vec_stopMargin
                
            if self.method == 'pinkNoise':
                self.vec_startMargin = zeros(int(self.startMargin*self.samplingRate),
                                                dtype=float32)
                self.vec_stopMargin = zeros(int(self.stopMargin*self.samplingRate),
                                                dtype=float32)
                self.excitation = generator.noise(int(self.duration*self.samplingRate),
                                                     color='pink',state=None)
                self.excitation = concatenate((self.vec_startMargin, self.excitation,\
                                                 self.vec_stopMargin), axis=None)
                self.excitation /= 10
                del self.vec_startMargin, self.vec_stopMargin
                
            if self.method == 'whiteNoise':
                self.vec_startMargin = zeros(int(self.startMargin*self.samplingRate),
                                                dtype=float32)
                self.vec_stopMargin = zeros(int(self.stopMargin*self.samplingRate),
                                                dtype=float32)
                self.excitation = generator.noise(int(self.duration*self.samplingRate),
                                                     color='white',state=None)
                self.excitation = concatenate((self.vec_startMargin, self.excitation,\
                                                 self.vec_stopMargin), axis=None)
                del self.vec_startMargin, self.vec_stopMargin
            #
            self.stream=self.p.open(format              = pyaudio.paFloat32,
                                    channels            = 1,
                                    input_device_index  = self.inDevice,
                                    output_device_index = self.outDevice,
                                    rate                = self.samplingRate, 
                                    input               = True,
                                    output              = True,
                                    frames_per_buffer  = self.frames)
            self.excitation = self.excitation/self.excitation.max()
            self.recData = empty((int(len(self.inputChannels)*(self.average+1)),\
                                  self.excitation.size), dtype=float32)
            self.countPlay = 0
        elif self.template == 'frequencyAnalyser':
            self.recData = empty((len(self.inputChannels), self.numSamples),\
                                 dtype=float32)
            self.rec = True
            self.stream=self.p.open(format             = pyaudio.paFloat32,
                                    channels           = 1,
                                    input_device_index = self.inDevice,
                                    rate               = self.samplingRate,
                                    input              = True,
                                    frames_per_buffer  = self.frames)
        elif self.template == 'calibration':
            self.recData = empty((len(self.inputChannels), self.numSamples),\
                                 dtype=float32)
            self.stream=self.p.open(format             = pyaudio.paFloat32,
                                    channels           = 1,
                                    input_device_index = self.inDevice,
                                    rate               = self.samplingRate,
                                    input              = True,
                                    frames_per_buffer  = self.frames)
        else:
            self.stream=self.p.open(format             = pyaudio.paFloat32,
                                    channels           = 1,
                                    input_device_index = self.inDevice,
                                    rate               = self.samplingRate,
                                    input              = True,
                                    frames_per_buffer  = self.frames)
            
        self.update()
        
        
    def update(self):
        '''
        Chamada de retorno que mantem a atualização da leitura de dados até que
        o método close() seja chamado.
        '''
        if self.template == 'frequencyAnalyser':
            self.thread = threading.Thread(target=self.Record)
            self.thread.start()
            
        elif self.template == 'reverberationTime':
            self.thread = threading.Thread(target=self.PlayRecord)
            self.thread.start()
            
        elif self.template == 'calibration':
            self.thread = threading.Thread(target=self.Calibration)
            self.thread.start()
            
        else:
            self.thread = threading.Thread(target=self.standby)
            self.thread.start()


        
    def standby(self):
        '''
        Stream definida para letura e cálculo do nível de pressão sonora em
        bandas e nível global, sem registrar o sinal medido.
        '''
        try:
            # Coleta dados da stream Pyaudio
            self.inData = frombuffer(self.stream.read(self.frames,\
                                exception_on_overflow=False), dtype=float32)
            # Aplica fator de calibração
            self.inData = self.inData * self.FCalibration
            # Cálcula níveis globais e por bandas
            self.globalLevel, self.Level = getBandLevel(data = self.inData,\
                                             pyfilterbank = self.pyfilterbank,\
                                             fc           = self.freqs,\
                                             pondFreq     = self.Freqweighting)
            # Teste
            # print('NPS: ', self.Level, '\n\nX: ', self.eixoX, '\n\n')
        except Exception as E:
            self.key=False
            print('\n\nDEEEEEU RUIM:\n')
            print(E)
        if self.key:
            self.update()
        else:
            self.close()
            
    def Record(self):
        '''
        Stream definida para letura e cálculo do nível de pressão sonora em
        bandas e nível global, registrando o sinal medido.
        '''
        try:
            if self.pause:
                pass
            else:
                # Coleta dados da stream Pyaudio
                self.inData = frombuffer(self.stream.read(self.frames,\
                                    exception_on_overflow=False), dtype=float32)
                # Aplica fator de calibração
                self.inData = self.inData * self.FCalibration
                # Salvo concateno os blocos de sinais adquiridos em um vetor
                self.recData[:, self.framesRead : self.frames +\
                             self.framesRead] = self.inData[:]
                # Cálcula níveis globais e por bandas
                self.globalLevel, self.Level = getBandLevel(data = self.inData,\
                                            pyfilterbank = self.pyfilterbank,
                                            fc           = self.freqs,\
                                            pondFreq     = self.Freqweighting)
                # Test
                # print('NPS: ', self.Level, '\n\nX: ', self.eixoX, '\n\n')
                
                # Condicional de parada
                self.framesRead+=self.frames
                self.countDn = self.recData.size/len(self.inputChannels) - self.framesRead
                if self.framesRead >= self.numSamples or self.countDn < self.frames or self.stop == True:
                    raise self.correctionSpectral()
        except Exception as E:
            self.key=False
            print('\n\nDEEEEEU RUIM:\n')
            print(E)
        if self.key:
            self.update()
        else:
            self.close()
            
    def PlayRecord(self):
        '''
        Stream definida para letura e reprodução de áudio, e cálculo do nível 
        de pressão sonora em bandas e nível global, registrando o sinal medido.
        '''
        try:
            if self.pause:
                pass
            else:
                self.stream.write(self.excitation[self.framesRead : self.frames +\
                                   self.framesRead], num_frames = self.frames)
                # Coleta dados da stream Pyaudio
                self.inData = frombuffer(self.stream.read(self.frames,\
                                  exception_on_overflow=False), dtype=float32)
                # Aplica fator de calibração
                self.inData = self.inData * self.FCalibration
                # Salvo concateno os blocos de sinais adquiridos em um vetor
                self.recData[self.countPlay, self.framesRead : self.frames +\
                             self.framesRead] = self.inData[:]
                # Cálcula níveis globais e por bandas
                self.globalLevel, self.Level = getBandLevel(data =self.inData,\
                                            pyfilterbank = self.pyfilterbank,\
                                            fc           = self.freqs,\
                                            pondFreq     = self.Freqweighting)
                # Teste
                # print('NPS: ', self.Level, '\n\nX: ', self.eixoX, '\n\n')
                # print('med nº ', self.countPlay+1)
                
                # Condicional de parada
                self.framesRead+=self.frames
                self.countDn = self.recData.size/(self.average+1) - self.framesRead
                if self.framesRead >= self.excitation.size or self.countDn < self.frames or self.stop == True:
                    self.framesRead=0
                    self.countPlay+=1
                    if self.countPlay>self.average:
                        raise self.correctionSpectral()
                    
        except Exception as E:
            self.key=False
            print('\n\nDEEEEEU RUIM:\n')
            print(E)
        if self.key:
            self.update()
        else:
            self.close()
            
    def Calibration(self):
        '''
        Stream definida para letura de áudio, e cálculo do nível de pressão
        sonora em bandas estreita detectando o maior nível e sua respectiva
        frequência para realizar a calibração, registrando o sinal medido.
        '''
        try:
            # Coleta dados da stream Pyaudio
            self.inData = frombuffer(self.stream.read(self.frames, exception_on_overflow=False),\
                                                                    dtype=float32)
            # Salvo concateno os blocos de sinais adquiridos em um vetor
            self.recData[0, self.framesRead : self.frames + self.framesRead] = self.inData[:]
            # Cálcula espectro em banda e estreita e vetor de frequências
            self.freqSignal, self.freqVector = getSpectrum(data         = self.inData,\
                                                           samplingRate = self.samplingRate)
            self.Level = 20*log10(abs(self.freqSignal)*self.FCalibration/default.refPressure)
            self.idMax = where(self.Level == self.Level.max())[0][0]
            # print(self.idMax)
            # Condicional de parada
            self.framesRead+=self.frames
            self.countDn = self.recData.size/len(self.inputChannels) - self.framesRead
            if self.framesRead >= self.numSamples or self.countDn < self.frames:
                raise self.correctionSpectral()
                # Teste
                # print('FC: ', self.FC, ' - ', self.freqVector[self.FCfreq], ' Hz')
        except Exception as E:
            self.key=False
            print('\n\nDEEEEEU RUIM:\n')
            print(E)
        if self.key:
            self.update()
        else:
            self.close()
    
    def correctionSpectral(self):
        '''
        Método que realiza a correção do espectro do sinal medido, retirando
        a influência da Sensitivity do microfone Dayton Audio iMM-6 e resposta
        em frequência do conversor analógico-digital C-Media CM6206.
        '''
        if (self.average+1) > 1: cutData = mean(self.recData[:, self.samplingRate:-1], axis=0)
        else:                    cutData = self.recData[:, self.samplingRate:-1]
        recData    = SignalObj(signalArray  = cutData,
                               domain       = 'time',
                               samplingRate = self.samplingRate)
        freqVector = recData.freqVector
        freqSignal = recData.freqSignal
        MagfreqSignal = 20*log10(abs(freqSignal))[:,0]
        
        # Carregando dados do microfone
        micData = loadtxt(fname='microphoneFRF.txt')
        micFreq = micData[:,0]
        micMag  = micData[:,1]
        
        # Carregando dados do ADC
        adcData = loadtxt(fname='adcFRF.txt')
        adcFreq = adcData[:,0]
        adcMag  = adcData[:,1]
        
        # Interpolacao da resposta do microfone
        interpMic = interpolate.interp1d(micFreq, micMag,\
                                         fill_value='extrapolate')
        micCorr   = interpMic(freqVector)
        
        # Interpolacao da resposta do adc
        interpADC = interpolate.interp1d(adcFreq, adcMag,\
                                         fill_value='extrapolate')
        adcCorr   = interpADC(freqVector)
        
        # Aplica correcao na magnitude
        correctedMagfreqSignal = MagfreqSignal - micCorr - adcCorr
        
        # Retorna ao vetor de amplitude complexa com magnitude e fase
        correctedfreqSignal = 10**(correctedMagfreqSignal/20)
        r    = correctedfreqSignal
        teta = angle(freqSignal)[:,0]
        correctedfreqSignal = r*(cos(teta) + sin(teta)*1j)
        
        # Transforma em SignalObj para obter o sinal no tempo (ifft)
        correctedFRF = SignalObj(signalArray  = correctedfreqSignal,
                                 domain       = 'freq',
                                 samplingRate = self.samplingRate)
        self.correctedData = transpose(correctedFRF.timeSignal)
        self.Result()
        
    
    def Result(self):
        '''
        Método que realiza o processamento do resultado final para ser salvo.
        '''
        if self.Freqweighting == 'A':
            pond = ponderacaoA(self.freqs)
            pond = 10*log10(sum(10**(pond/10)))
        elif self.Freqweighting == 'C':
            pond = ponderacaoC(self.freqs)
            pond = 10*log10(sum(10**(pond/10)))
        else: 
            pond = 0
        print(pond)
        if self.template == 'reverberationTime':
            # SNR
            cutSNR       = self.timeSNR*self.samplingRate
            floorNoise   = self.correctedData[0, 0:cutSNR]
            measuredData = self.correctedData[0, (cutSNR+1):-1]
            excitation   = self.excitation[cutSNR+self.samplingRate+1:-1] 
            trash, self.Level_floorNoise =  getBandLevel(data = floorNoise,
                                                pyfilterbank = self.pyfilterbank,
                                                fc           = self.freqs, 
                                                pondFreq     = 'Z')
            trash, self.Level_measuredData = getBandLevel(data = measuredData,\
                                                pyfilterbank = self.pyfilterbank,\
                                                fc           = self.freqs,\
                                                pondFreq     = 'Z')
            self.SNR = self.Level_measuredData - self.Level_floorNoise
            print(self.SNR)
            if self.method == 'sweepExponencial':
                self.correctedData = measuredData
                self.excitation = excitation
                complete = self.excitation.size - self.correctedData.size
                if complete > 0:
                    complete = zeros((1, complete), dtype=float32)
                    print(complete)
                    self.correctedData = concatenate((self.correctedData, complete),\
                                                     axis=None)
                inputSignal  = SignalObj(signalArray  = transpose(self.excitation),
                                         domain       ='time',
                                         samplingRate = self.samplingRate)
                outputSignal = SignalObj(signalArray  = transpose(self.correctedData),
                                         domain       ='time',
                                         samplingRate = self.samplingRate)
                self.IR = outputSignal/inputSignal
                # pMax = where(abs(self.IR.timeSignal)**2 == abs(self.IR.timeSignal).max()**2)[0][0]
                pMax=0
                self.IR = SignalObj(signalArray  = self.IR.timeSignal[pMax:-1],\
                                    domain       = 'time',\
                                    samplingRate = self.samplingRate)
            if self.method == 'pinkNoise' or self.method == 'whiteNoise':
                pCut = int((self.startMargin + self.duration + 0.2) * self.samplingRate)
                self.correctedData = self.correctedData[0, pCut:-1]
                pMax = where(abs(self.correctedData)**2 == abs(self.correctedData).max()**2)[0][0]
                self.IR = self.correctedData[pMax:-1]
                self.IR = SignalObj(signalArray  = self.IR,\
                                    domain       = 'time',\
                                    samplingRate = self.samplingRate)
            self.RT = RT(signal       = self.IR, snr = self.SNR,\
                         samplingRate = self.samplingRate,\
                         fstart       = self.fstart,\
                         fstop        = self.fstop,\
                         ffraction    = self.ffraction)
            # print(self.RT['T10'])
            self.impulseLevel = impulse_level(data = self.correctedData,\
                                              fs   = self.samplingRate)
            self.impulseLevel[1][:] += pond
            self.fastLevel = fast_level(data = self.correctedData,\
                                        fs   = self.samplingRate)
            self.fastLevel[1][:] += pond
            self.slowLevel = slow_level(data = self.correctedData,\
                                        fs   = self.samplingRate)
            self.slowLevel[1][:] += pond
            self.ResultKey = True
            
        elif self.template == 'frequencyAnalyser':
            globalLevel, self.Level =\
                            getBandLevel(data = self.correctedData[0],\
                                pyfilterbank  = self.pyfilterbank,\
                                fc            = self.freqs,\
                                pondFreq      = self.Freqweighting)
            del globalLevel
            self.globalLevel = 10*log10(rms(self.correctedData[0])**2 / \
                                        default.refPressure**2) + pond
            self.impulseLevel = impulse_level(data = self.correctedData[0,:],\
                                              fs   = self.samplingRate)
            self.impulseLevel[1][:] += pond
            self.impulseLevelGlobal = 10*log10(mean(10**(self.impulseLevel[1][:]/10)))
            self.fastLevel = fast_level(data = self.correctedData[0,:],\
                                        fs   = self.samplingRate)
            self.fastLevel[1][:] += pond
            self.fastLevelGlobal = 10*log10(mean(10**(self.fastLevel[1][:]/10)))
            self.slowLevel = slow_level(data = self.correctedData[0,:],\
                                        fs   = self.samplingRate)
            self.slowLevel[1][:] += pond
            self.slowLevelGlobal = 10*log10(mean(10**(self.slowLevel[1][:]/10)))
            self.ResultKey = True
            # print('Result: '+ self.template)
        elif self.template == 'calibration':
            self.freqSignal, self.freqVector = getSpectrum(self.correctedData[0,:],\
                                                    samplingRate=self.samplingRate)
            self.Sensitivity = abs(self.freqSignal).max()
            self.FC = 1/self.Sensitivity
            self.Level = 20*log10(abs(self.freqSignal)*self.FC/20e-06)
            self.idMax = where(self.Level == self.Level.max())[0][0]
            self.Sensitivity = round(self.Sensitivity, 2)
            self.correcao = abs(10*log10(self.Sensitivity)) -\
                abs(10*log10(self.FCalibration))
            self.correcao = round(self.correcao, 2)
            # print('Result: '+ self.template)
        raise self.close()
    
    def close(self):
        """Fecha a Stream e encerra o fluxo do threading."""
        # print("\n -- comando close() acionado")
        self.stream.close()
        self.key=False #the threads should self-close
        while(self.thread.isAlive()): #wait for all threads to close
            time.sleep(.1)
        self.stream.stop_stream()
        self.p.terminate()
        self.thread1._stop()
        self.thread1._delete()
        self.thread2._stop()
        self.thread2._delete()


def getBandLevel(data, pyfilterbank, fc, pondFreq):
#    inicio=time.time()
    '''
    Função que recebe os dados medidos em [Pa], filtragem pelo package
    pyfilterbank separando em bandas de oitava ou terço de oitava e calcula o
    NPS global e por bandas.
    
    Parâmetros de entrada:
        -> data: Sinal medido pelo microfone, dado em Pascal.
        -> pyfilterbank: instância do filtro declarada anteriormente.
        -> pondFreq: ponderação em frequência(A, C e Z).
                      
    Parâmetros de saída:
        -> globalLevel: NPS global do sinal medido.
        -> Level: vetor de NPS por bandas de frequência. 
    '''
    dataFilt = pyfilterbank.filter(x=data,states=None)
    Level = empty((len(dataFilt[0][0,:])), dtype=float32)
    for idx in range(len(dataFilt[0][0,:])):
        Level[idx] = 10*log10(rms(dataFilt[0][:,idx])**2/default.refPressure**2)
    
    if pondFreq == 'A':
        pond = ponderacaoA(fc)
    elif pondFreq == 'C':
        pond = ponderacaoC(fc)
    else:
        pond = ponderacaoZ(fc)
    Level = Level + pond
    globalLevel = 10*log10(sum(10**(Level/10)))
    return globalLevel, Level[:int(len(Level))]
        
def getSpectrum(data, samplingRate):
    '''
    Função que realiza a transforma da Fourier, retornando os vetores de ampli-
    tude complexa e frequência para exibir na tela de calibração.
    
    Parâmetros de entrada:
        -> data: Sinal medido pelo microfone, dado em Pascal
        -> samplingRate: taxa de amostragem
        
    Parâmetros de saída:
        -> freqSignal: vetor de frequências
        -> freqSignal: vetor de amplitude complexa
    '''
    numSamples = len(data)
    freqSignal = fft.rfft(data, axis=0, norm=None)
    freqSignal /= 2**0.5
    freqSignal /= len(freqSignal)
    freqVector = linspace(0, (numSamples - 1) *
                               samplingRate /
                               (2*numSamples),
                               (int(numSamples/2)+1)
                               if numSamples % 2 == 0
                               else int((numSamples+1)/2))
    return freqSignal, freqVector

def rms(data):
    '''
    Função que realiza a média quadrática da pressão sonora
    
    Parâmetro de entrada:
        -> data: Sinal medido pelo microfone, dado em Pascal
        
    Parâmetro de saída:
        -> RMS
    '''
    return sqrt((abs(data)**2.0).mean())

    
def findBand(fstart, fstop, fraction):
    '''
    Função que encontra as frequências em ordem com referência em  1 kHz (item 0).
    
    Parâmetro de entrada:
        -> fstart: frequência mínima em Hertz
        -> fsttop: frequência máxima em Hertz
        -> fraction: fração
        
    Parâmetro de saída:
        -> fstart: frequência mínima em ordem com referência em 1 kHz (item 0)
        -> fsttop: frequência máxima em ordem com referência em 1 kHz (item 0)
    '''
    from numpy import array
    index_freq_third  = array([-17, -16, -15, -14, -13, -12, -11, -10, -9, -8,
                               -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6,
                               7, 8, 9, 10, 11, 12, 13])
    center_freq_third = array([20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160,
                               200, 250, 315, 400, 500, 630, 800, 1000, 1250,
                               1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000,
                               10000, 12500, 16000, 20000])
    index_freq_octave = array([-5, -4, -3, -2, -1, 0, 1, 2, 3, 4])
    center_freq_octave = array([31.5, 63, 125, 250, 500, 1000, 2000, 4000,
                                8000, 16000])
    
    
    if fraction == 3:
        lengthBand = center_freq_third.size
        band = center_freq_third
        index_freq = index_freq_third
    else:
        lengthBand = center_freq_octave.size
        band = center_freq_octave
        index_freq = index_freq_octave
    
    for i in range(lengthBand):
        fi = 2**(-1/(2*fraction)) * band[i]
        fs = 2**(1/(2*fraction)) * band[i]
        if fstart >= fi and fstart <= fs:
            start_band = i
        if fstop >= fi and fstop <= fs:
            end_band = i
    if fstart <=31.5: start_band = 0
    return index_freq[start_band], index_freq[end_band]

def nominal_frequencies(center_frequencies, fraction):
    '''
    Função que encontra as frequências nominais para o filtro pyfilerbank.
    
    Parâmetro de entrada:
        -> fstart: frequência mínima em Hertz
        -> fsttop: frequência máxima em Hertz
        -> fraction: fração
        
    Parâmetro de saída:
        -> fstart: frequência nominais.
    '''
    from numpy import array, argmin
    if fraction ==3:
        standardized_nominal_frequencies = array([20, 25, 31.5, 40, 50, 63, 80,
                                                  100, 125, 160, 200,
                               250, 315, 400, 500, 630, 800, 1000, 1250, 1600,
                               2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000,
                               12500, 16000, 20000])
    else:
        standardized_nominal_frequencies = array([31.5, 63, 125, 250, 500, 1000,
                                                  2000, 4000, 8000, 16000]) 
    # result = empty((1, center_frequencies.size), dtype=float32)
    result = center_frequencies
    idx = 0
    for f in center_frequencies:
        dist = sqrt((standardized_nominal_frequencies - f)**2)
        result[idx] = standardized_nominal_frequencies[argmin(dist)]
        idx+=1
    return result

# %% Mainloop
'''Permite executar rotina para fins de testes'''
if __name__=="__main__":
    test=pyaudioStream(device     = [1,3],
                    samplingRate  = 44100,
                    inputChannels = [1],
                    outputChannels= [1,2],
                    timeConstant  = 1,
                    fstart        = 20,
                    fstop         = 20000,
                    ffraction     = 3,
                    Freqweighting = 'A',
                    duration      = 5,
                    startMargin   = 0,
                    stopMargin    = 1,
                    method        = 'sweepExponencial',
                    average       = 1,
                    template      = 'frequencyAnalyser')
    test.streamStart()