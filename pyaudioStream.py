# -*- coding: utf-8 -*-
"""
Arquivo .py criado para manipular o sinal de entrada do microfone e alimentar
os mostradores do MNPS)

author: @leonardojacomussi
"""

from numpy import float32, empty, transpose, frombuffer, log2,loadtxt, mean,\
                  angle, linspace, sqrt, log10, fft, where, sin, cos, array
from standards import ponderacaoA, ponderacaoC, ponderacaoZ,\
                            impulse_level, fast_level, slow_level
from pyfilterbank import FractionalOctaveFilterbank as FOF
from pytta import SignalObj
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
                    
        -> device: [in]
                   vetor de número inteiro correspondente aos dispositivo
                   que realizará a leitura. A lista de dispositivos pode ser 
                   obtida pelo package pytta com o método pytta.list_devices().
                   
                   
        -> samplingRate: taxa de amostragem do dispositivo ADC, dada em Hertz.
                         Exemplo: 44100.
                         
        -> inputChannels: número inteiro correspondente ao canal de entrada
                          do dispositivo utilizado.
                          
        -> timeConstant: número inteiro ou decimal correspondente a pon-
                         deração temporal do mostrador de dados.
                         
                         Normalmente são tomados os seguintes valores:
                             0.125 (modo FAST), 1.000 (modo SLOW) ou 0.035 (modo
                             IMPULSE).
                      
        -> Freqweighting: Ponderação na frequência. Podem ser escolhidas as curvas
                          de ponderação A, C e Z.
                   
        -> duration: se o template for "frequencyAnalyser" é o tempo de registro
                     da medição, se o template for "reverberationTime" é o tempo
                     efetivo do sinal de excitação (considerando que há o tempo
                     de silêncio no final e no início do sinal (startMargin e
                     stopMargin)).
    """
    def __init__(self, device  =  default.device,
                 samplingRate  =  default.samplingRate,
                 inputChannels =  default.inputChannels,
                 timeConstant  =  default.timeConstant,
                 Freqweighting =  'Z',
                 duration      =  5.0,
                 template      =  'stand-by'):
        self.device        = device
        self.samplingRate  = samplingRate
        self.inputChannels = inputChannels
        self.timeConstant  = timeConstant
        self.Freqweighting = Freqweighting
        self.duration      = duration + 1
        self.numSamples    = int(self.duration*self.samplingRate)
        self.fftDegree     = log2(self.numSamples)
        self.template      = template
        self.timeSNR       = 5
        self.pause         = False
        self.stop          = False
        self.rec           = False
        # Filtro de frequências Pyfilterbank
        self.pyfilterbank = FOF(sample_rate = default.samplingRate,\
                                order       = 10,\
                                nth_oct     = 3,\
                                norm_freq   = 1000.0,\
                                start_band  = -17,\
                                end_band    = 13,\
                                filterfun   = 'cffi')
        if self.Freqweighting == 'A':
            self.pondFreq = ponderacaoA(self.pyfilterbank.center_frequencies)
            self.pondFreq = 10*log10(sum(10**(self.pondFreq/10)))
        elif self.Freqweighting == 'C':
            self.pondFreq = ponderacaoC(self.pyfilterbank.center_frequencies)
            self.pondFreq = 10*log10(sum(10**(self.pondFreq/10)))
        else:
            self.pondFreq = 0
        
        self.freqs = array([20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200,\
                            250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000,\
                            2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500,\
                            16000, 20000])
        
        # Variáveis da stream
        self.ResultKey    = False
        self.frames       = int(self.samplingRate * self.timeConstant)
        self.framesRead   = 0
        self.p            = pyaudio.PyAudio()
        self.globalLevel  = None
        self.Level        = None
        self.idMax        = None
        self.inData       = None
        self.FC           = float()
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
        if self.template == 'calibration' or self.template == 'frequencyAnalyser':
            self.rec = True
            self.recData = empty((len(self.inputChannels), self.numSamples),\
                                 dtype=float32)
        else:
            pass
        self.stream=self.p.open(format             = pyaudio.paFloat32,
                                channels           = self.inputChannels[0],
                                input_device_index = self.device[0],
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
            self.thread=threading.Thread(target=self.Record)
            self.thread.start()
            
        elif self.template == 'calibration':
            self.thread=threading.Thread(target=self.Calibration)
            self.thread.start()
            
        else:
            self.thread=threading.Thread(target=self.standby)
            self.thread.start()
        
    def standby(self):
        '''
        Stream definida para letura e cálculo do nível de pressão sonora global,
        sem registrar o sinal medido.
        '''
        try:
            # Coleta dados da stream Pyaudio
            self.inData = frombuffer(self.stream.read(self.frames,\
                                    exception_on_overflow=False), dtype=float32)
            # Aplica fator de calibração
            self.inData = self.inData * self.FCalibration
            # Cálcula níveis globais e por bandas
            self.globalLevel = 10*log10(rms(self.inData)**2 /\
                                        default.refPressure**2) - self.pondFreq
            # Teste
                # print('NPS: ', self.globalLevel)
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
        Stream definida para letura e cálculo do nível de pressão sonora global,
        registrando o sinal medido.
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
                self.recData[:, self.framesRead : self.frames + self.framesRead] = self.inData[:]
                # Cálcula níveis globais e por bandas
                self.globalLevel = 10*log10(rms(self.inData)**2 /\
                                            default.refPressure**2) - self.pondFreq
                # # Teste
                # print('NPS: ', self.globalLevel)
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
            
    def Calibration(self):
        '''
        Stream definida para letura de áudio, e cálculo do nível de pressão
        sonora em bandas estreita detectando o maior nível e sua respectiva
        frequência para realizar a calibração, registrando o sinal medido.
        '''
        try:
            # Coleta dados da stream Pyaudio
            self.inData = frombuffer(self.stream.read(self.frames,\
                                            exception_on_overflow=False), dtype=float32)
            # Salvo concateno os blocos de sinais adquiridos em um vetor
            self.recData[0, self.framesRead : self.frames + self.framesRead] = self.inData[:]
            # Cálcula espectro em banda e estreita e vetor de frequências
            self.freqSignal, self.freqVector = getSpectrum(data = self.inData,\
                                                   samplingRate = self.samplingRate)
            self.Level = 20*log10(abs(self.freqSignal)*self.FCalibration/default.refPressure)
            self.idMax = where(self.Level == self.Level.max())[0][0]
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
        a influência da sensibilidade do microfone Dayton Audio iMM-6 e resposta
        em frequência do conversor analógico-digital C-Media CM6206.
        '''
        cutData  = self.recData[:, self.samplingRate:-1]
        recData = SignalObj(signalArray  = cutData,\
                            domain       = 'time',\
                            samplingRate = self.samplingRate)
        freqVector = recData.freqVector
        freqSignal = recData.freqSignal
        MagfreqSignal = 20*log10(abs(freqSignal))[:,0]
        micData = loadtxt(fname='microphoneFRF.txt')
        micFreq = micData[:,0]
        micMag = micData[:,1]
        # Carregando dados do ADC
        adcData = loadtxt(fname='adcFRF.txt')
        adcFreq = adcData[:,0]
        adcMag  = adcData[:,1]
        # Interpolação da resposta do microfone
        interpMic = interpolate.interp1d(micFreq, micMag, fill_value='extrapolate')
        micCorr = interpMic(freqVector)
        # Interpolacao da resposta do adc
        interpADC = interpolate.interp1d(adcFreq, adcMag, fill_value='extrapolate')
        acdCorr   = interpADC(freqVector)
        # Aplica correção na magnitude
        correctedMagfreqSignal = MagfreqSignal - micCorr - acdCorr
        # Retorna ao vetor de amplitude complexa com magnitude e fase
        correctedfreqSignal = 10**(correctedMagfreqSignal/20)
        r = correctedfreqSignal
        teta = angle(freqSignal)[:,0]
        correctedfreqSignal = r*(cos(teta) + sin(teta)*1j)
        # Transforma em SignalObj para obter o sinal no tempo (ifft)
        correctedFRF = SignalObj(signalArray = correctedfreqSignal,\
                                  domain      = 'freq',\
                                samplingRate = self.samplingRate)
        self.correctedData = transpose(correctedFRF.timeSignal)
        self.Result()
    
    # def correctionSpectral(self):
    #     self.correctedData = self.recData[:, self.samplingRate:-1]
    #     self.Result()
    
    def Result(self):
        '''
        Método que realiza o processamento do resultado final para ser salvo.
        '''
        if self.template == 'frequencyAnalyser':
            globalLevel, self.Level = getBandLevel(data = self.correctedData[0],\
                                            pyfilterbank = self.pyfilterbank,
                                            fc           = self.freqs, 
                                            pondFreq     = self.Freqweighting)
            del globalLevel
            self.globalLevel = 10*log10(rms(self.correctedData[0])**2 /\
                                        default.refPressure**2) + self.pondFreq
            self.impulseLevel = impulse_level(data = self.correctedData[0,:],\
                                              fs=self.samplingRate)
            self.impulseLevel[1][:] += self.pondFreq
            self.impulseLevelGlobal = 10*log10(mean(10**(self.impulseLevel[1][:]/10)))
            self.fastLevel = fast_level(data=self.correctedData[0,:], fs=self.samplingRate)
            self.fastLevel[1][:] += self.pondFreq
            self.fastLevelGlobal = 10*log10(mean(10**(self.fastLevel[1][:]/10)))
            self.slowLevel = slow_level(data=self.correctedData[0,:], fs=self.samplingRate)
            self.slowLevel[1][:] += self.pondFreq
            self.slowLevelGlobal = 10*log10(mean(10**(self.slowLevel[1][:]/10)))
            self.ResultKey = True
            # print('Result: '+ self.template)
        elif self.template == 'calibration':
            self.freqSignal, self.freqVector = getSpectrum(self.correctedData[0,:],\
                                                    samplingRate=self.samplingRate)
            a = where(self.freqVector >= 900)[0][0]   # 900 Hz
            b = where(self.freqVector <= 1100)[0][-1] # 1000 Hz
            self.Sensitivity = abs(self.freqSignal[a:b]).max()
            self.FC = 1/self.Sensitivity
            self.Level = 20*log10(abs(self.freqSignal)*self.FC/20e-06)
            self.idMax = where(self.Level == self.Level.max())[0][0]
            self.Sensitivity = round(self.Sensitivity, 2)
            self.correcao = abs(20*log10(self.Sensitivity)) -\
                      abs(20*log10(self.FCalibration))
            self.correcao = round(self.correcao, 2)
            self.FCfreq = where(abs(self.freqSignal) == abs(self.freqSignal).max())[0][0]
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
        self.thread._stop()
        self.thread._delete()

def rms(data):
    '''
    Função que realiza a média quadrática da pressão sonora
    
    Parâmetro de entrada:
        -> data: Sinal medido pelo microfone, dado em Pascal
        
    Parâmetro de saída:
        -> RMS
    '''
    return sqrt((abs(data)**2.0).mean())

def getBandLevel(data, pyfilterbank, fc, pondFreq):
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

# %% Mainloop
'''Permite executar rotina para fins de testes'''
if __name__=="__main__":
    test=pyaudioStream(device     = 1,
                    samplingRate  = 44100,
                    inputChannels = [1],
                    timeConstant  = 0.125,
                    Freqweighting = 'A',
                    duration      = 5,
                    template      = 'frequencyAnalyser')
    test.streamStart()