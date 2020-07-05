# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 22:31:03 2019

@author: Leonardo Jacomussi
"""
from numpy import log10, arange, sqrt, asarray, ones, zeros, where,\
                  flipud, floor, float32, empty
from scipy.signal import lfilter, bilinear, zpk2tf
from scipy.integrate import cumtrapz #scipy.integrate.cumtrapz
from scipy.stats import linregress #scipy.stats.linregress
from acoustics.signal import OctaveBand
from pytta import generate, SignalObj
import default

# %% IEC 61672-1:2013
REFERENCE_PRESSURE = default.refPressure

FAST = 0.125
"""FAST time-constant.
"""

SLOW = 1.000
"""SLOW time-constant.
"""

IMPULSE = 0.035
"""IMPULSE time-constant.
"""

def time_averaged_sound_level(pressure, sample_frequency, averaging_time, reference_pressure=REFERENCE_PRESSURE):
    """Time-averaged sound pressure level.
    :param pressure: Dynamic pressure.
    :param sample_frequency: Sample frequency.
    :param averaging_time: Averaging time.
    :param reference_pressure: Reference pressure.
    """
    levels = 10.0 * log10(average(pressure**2.0, sample_frequency, averaging_time) / reference_pressure**2.0)
    times = arange(levels.shape[-1]) * averaging_time
    return times, levels


def average(data, sample_frequency, averaging_time):
    """Average the sound pressure squared.
    :param data: Energetic quantity, e.g. :math:`p^2`.
    :param sample_frequency: Sample frequency.
    :param averaging_time: Averaging time.
    :returns:
    Time weighting is applied by applying a low-pass filter with one real pole at :math:`-1/\\tau`.
    .. note::
        Because :math:`f_s \\cdot t_i` is generally not an integer, samples are discarded.
        This results in a drift of samples for longer signals (e.g. 60 minutes at 44.1 kHz).
    """
    averaging_time = asarray(averaging_time)
    sample_frequency = asarray(sample_frequency)
    samples = data.shape[-1]
    n = floor(averaging_time * sample_frequency).astype(int)
    data = data[..., 0:n * (samples // n)]  # Drop the tail of the signal.
    newshape = list(data.shape[0:-1])
    newshape.extend([-1, n])
    data = data.reshape(newshape)
    #data = data.reshape((-1, n))
    return data.mean(axis=-1)


def time_weighted_sound_level(pressure, sample_frequency, integration_time, reference_pressure=REFERENCE_PRESSURE):
    """Time-weighted sound pressure level.
    :param pressure: Dynamic pressure.
    :param sample_frequency: Sample frequency.
    :param integration_time: Integration time.
    :param reference_pressure: Reference pressure.
    """
    levels = 10.0 * log10(integrate(pressure**2.0, sample_frequency, integration_time) / reference_pressure**2.0)
    times = arange(levels.shape[-1]) * integration_time
    return times, levels


def integrate(data, sample_frequency, integration_time):
    """Integrate the sound pressure squared using exponential integration.
    :param data: Energetic quantity, e.g. :math:`p^2`.
    :param sample_frequency: Sample frequency.
    :param integration_time: Integration time.
    :returns:
    Time weighting is applied by applying a low-pass filter with one real pole at :math:`-1/\\tau`.
    .. note::
        Because :math:`f_s \\cdot t_i` is generally not an integer, samples are discarded.
        This results in a drift of samples for longer signals (e.g. 60 minutes at 44.1 kHz).
    """
    integration_time = asarray(integration_time)
    sample_frequency = asarray(sample_frequency)
    samples = data.shape[-1]
    b, a = zpk2tf([1.0], [1.0, integration_time], [1.0])
    b, a = bilinear(b, a, fs=sample_frequency)
    #b, a = bilinear([1.0], [1.0, integration_time], fs=sample_frequency) # Bilinear: Analog to Digital filter.
    n = floor(integration_time * sample_frequency).astype(int)
    data = data[..., 0:n * (samples // n)]
    newshape = list(data.shape[0:-1])
    newshape.extend([-1, n])
    data = data.reshape(newshape)
    #data = data.reshape((-1, n)) # Divide in chunks over which to perform the integration.
    return lfilter(
        b, a,
        data)[..., n - 1] / integration_time  # Perform the integration. Select the final value of the integration.


def impulse(data, fs):
    """Apply impulse (I) time-weighting.
    :param data: Energetic quantity, e.g. :math:`p^2`.
    :param fs: Sample frequency.
    .. seealso:: :func:`integrate`
    """
    return integrate(data, fs, IMPULSE)

def fast(data, fs):
    """Apply fast (F) time-weighting.
    :param data: Energetic quantity, e.g. :math:`p^2`.
    :param fs: Sample frequency.
    .. seealso:: :func:`integrate`
    """
    return integrate(data, fs, FAST)


def slow(data, fs):
    """Apply slow (S) time-weighting.
    :param data: Energetic quantity, e.g. :math:`p^2`.
    :param fs: Sample frequency.
    .. seealso:: :func:`integrate`
    """
    return integrate(data, fs, SLOW)

def impulse_level(data, fs):
    """Time-weighted (FAST) sound pressure level.
    :param data: Dynamic pressure.
    :param fs: Sample frequency.
    .. seealso:: :func:`time_weighted_sound_level`
    """
    return time_weighted_sound_level(data, fs, IMPULSE)

def fast_level(data, fs):
    """Time-weighted (FAST) sound pressure level.
    :param data: Dynamic pressure.
    :param fs: Sample frequency.
    .. seealso:: :func:`time_weighted_sound_level`
    """
    return time_weighted_sound_level(data, fs, FAST)


def slow_level(data, fs):
    """Time-weighted (SLOW) sound pressure level.
    :param data: Dynamic pressure.
    :param fs: Sample frequency.
    .. seealso:: :func:`time_weighted_sound_level`
    """
    return time_weighted_sound_level(data, fs, SLOW)

def ponderacaoA(f):
    '''' 
    Filtro de ponderação A - Equacionamento disposto no Annex E da standart IEC 61672-1
    Parâmentro de entrada: f -> vetor de frequências
    Parâmetro de saída:    A -> vetor de ponderação A em dB
    '''
    fL = 10**1.5
    fA = 10**2.45
    fr = 1000
    fH = 10**3.9
    D = sqrt(0.5)
    A_1k = -1.999655535667262
    b = 1/(1-D)*( fr**2 + (fL**2*fH**2 / fr**2) - D*(fL**2+fH**2))
    c = fL**2 * fH**2
    f1 = sqrt( (-b-sqrt(b**2 - 4*c)) / 2 )
    f2 = fA * ((3 - sqrt(5)) / 2)
    f3 = fA * ((3 + sqrt(5)) / 2)
    f4 = sqrt( (-b+ sqrt(b**2 - 4*c)) / 2 )
    A = - A_1k + 20 * log10( (f4**2 * f**4) / ( ( f**2 + f1**2 ) * ( (f**2 + f2**2)**(1/2) ) * ( (f**2 + f3**2)**(1/2) ) * ( f**2 + f4**2 )))
    return A

def ponderacaoC(f):
    '''' 
    Filtro de ponderação A - Equacionamento disposto no Annex E da standart IEC 61672-1
    Parâmentro de entrada: f -> vetor de frequências
    Parâmetro de saída:    C -> vetor de ponderação C em dB
    '''
    fL = 10**1.5
    fr = 1000
    fH = 10**3.9
    D = sqrt(0.5)
    C_1k = -0.06190185672432288
    b = 1/(1-D)*( fr**2 + (fL**2*fH**2 / fr**2) - D*(fL**2+fH**2))
    c = fL**2 * fH**2
    f1 = sqrt( (-b- sqrt(b**2 - 4*c)) / 2 )
    f4 = sqrt( (-b+ sqrt(b**2 - 4*c)) / 2 )
    C = - C_1k + 20 * log10( (f4**2 * f**2) / ( (f**2 + f1**2) * (f**2 + f4**2) ) )
    return C


def ponderacaoZ(f):
    return zeros(len(f))


# %% ISO 3382-1:2009
def RT(signal, snr, samplingRate, fstart,  fstop, ffraction):
    # ht -> nomenclatura utilizada na literatura
    ht = signal.timeSignal
    # Excluindo zeros a direita
    mask = ones(len(ht), dtype=bool) 
    for i in range(ht.size):
        if ht[i] == 0:
            mask[i] = False
    ht = ht[mask,...]
    # filtro de 1/n oitavas
    fc = OctaveBand(fstart=fstart, fstop=fstop, fraction=ffraction)
    # [dB] ponto de partida para o cálculo de TR
         # init[0] --> 0.0 dB para EDT
         # init[1] --> -5.0 dB para T10
         # init[2] --> -5.0 dB para T20
         # init[3] --> -5.0 dB para T30
    init = asarray([0, -5, -5, -5])
    # [dB] decaimento necessário para cálculo de TR
        # end[0] --> -10.0 dB para EDT
        # end[1] --> -15.0 dB para T10
        # end[2] --> -25.0 dB para T20
        # end[3] --> -35.0 dB para T30
    end = asarray([-10, -15, -25, -35])
    'Filtro 1/n oitavas PyTTa'
    myFilter = generate.filter(order=8,
                            nthOct=ffraction,
                            samplingRate=signal._samplingRate,
                            minFreq=fstart,
                            maxFreq=fstop,
                            refFreq=1000,
                            base=10)
    ht = SignalObj(signalArray=ht, domain='time', samplingRate=samplingRate)
    sinal_filtrado = myFilter.filter(ht)
    TR = empty((init.size, fc.nominal.size), dtype = float32)
    for tr in range(init.size):
        for band in range(fc.nominal.size):
            # Conferindo SNR
            if snr[band] > 10:
                # Filtrando sinal
                # sinal_abs = abs(sinal_filtrado[0].timeSignal[:,band])/max(abs(ht.timeSignal))
                sinal_abs = abs(sinal_filtrado[0].timeSignal[:,band])
                
                # Integração invertida por bandas (Schroeder integration)
                ht_filtrado = flipud(sinal_abs)
                htRMS_filtrado = flipud(cumtrapz(ht_filtrado**2))
                htRMS_filtrado_dB = 10.0 * log10( htRMS_filtrado / max(htRMS_filtrado) )
                # htRMS_filtrado_dB = 10.0 * log10(htRMS_filtrado)

                # Regreção linear
                ht_init = htRMS_filtrado_dB[ abs(htRMS_filtrado_dB - init[tr]).argmin() ]
                ht_end = htRMS_filtrado_dB[ abs(htRMS_filtrado_dB - end[tr]).argmin() ]
                init_index = where( htRMS_filtrado_dB == ht_init )[0][0]
                end_index = where( htRMS_filtrado_dB == ht_end )[0][0]
                x = arange( init_index, end_index)/samplingRate
                y = htRMS_filtrado_dB[ init_index : end_index]
                slope, intercept = linregress( x, y )[0:2]
                TR[tr][band] = -60 / slope
            else:
                TR[tr][band] = 0
    result = {'EDT': TR[0][:], 'T10': TR[1][:], 'T20': TR[2][:], 'T30': TR[3][:]}
    return result