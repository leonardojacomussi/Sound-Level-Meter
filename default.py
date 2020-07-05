# -*- coding: utf-8 -*-

# %% Configurações do Medidor
'''
############################################################
device[in, out]

        in -> dispositivo de entrada de áudio
        out -> dispositivo de saída de áudio
        
Para verificar os dispositivos de áudio conectados execute:
    
import pytta
pytta.list_devices()
############################################################
'''
device = [1, 3]
# device = [4]

# Canal de entrada (apenas 1 (um) canal de gravação)
inputChannels = [1]

# Canais de saída
outChannels = [1,2]

# Taxa de amostragem: [Hz]
samplingRate = 44100

#%% Constantantes padrão

# Frequência mínima de análise: [Hz]
freqMin = 20

# Frequência máxima de análise: [Hz]
freqMax = 20000

# Fração de banda de oitavas (1/3 de oitava): [-]
fraction = 3

# Margem de silêncio no início do sinal: [s]
startMargin = 0.2

# Margem de silêncio no final do sinal: [s]
stopMargin = 5

# Pressão sonora de referência (zero dB): [Pa]
refPressure = 2e-05

# Ponderação temporal (Fast) [s]
timeConstant = 0.125

# Tempo de duração da medição [s]
duration = 60

# Velocidade do som [m/s]
c0 = 343

# Método de medição de respostas impulsivas
method = 'sweepExponencial'

# Margem de silêncio no início do sinal de excitação [s]
startMargin = 0.2

# Margem de silêncio no final do sinal de excitação [s]
stopMargin = 1.5

# Ponderação em frequência
Freqweighting = 'Z'