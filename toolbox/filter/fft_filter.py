# -*- coding: utf-8 -*-
__author__ = 'SUN Shouwang'

import numpy as np
import pylab as plt


def simulate_signal():
    """
    仿真信号是两个正弦波的叠加
        第一个正弦波的周期是0.5秒，频率2Hz
        第二个正弦波的周期是1.0秒，频率1Hz
    """
    time = np.arange(0, 20, 0.02)
    w1 = np.pi*2/0.5
    phi1 = np.pi/2
    w2 = np.pi*2/1.0
    phi2 = 0
    data = np.sin(w1*time + phi1) + np.sin(w2*time + phi2)
    return {'time': time, 'data': data}


def frequency_spectrum(signal):

    nfft = len(signal['data'])
    delta_time = signal['time'][1] - signal['time'][0]
    freqs = np.fft.fftfreq(nfft, delta_time)
    freqs = freqs[freqs >= 0]
    fft_coefs = np.fft.fft(signal['data'], nfft)[0: len(freqs)]
    amplitude = np.abs(fft_coefs)
    return {'freqs': freqs, 'amplitude': amplitude}


def fft_filter(signal, stop_bands):

    nfft = len(signal['data'])
    delta_time = signal['time'][1] - signal['time'][0]
    freqs = np.fft.fftfreq(nfft, delta_time)
    fft_coefs = np.fft.fft(signal['data'], nfft)

    freqs_abs = np.abs(freqs)
    for stop_band in stop_bands:
        logic_index = (freqs_abs >= stop_band[0]) & (freqs_abs < stop_band[1])
        fft_coefs[logic_index] = 0

    return np.real(np.fft.ifft(fft_coefs, nfft))


if __name__ == '__main__':

    signal = simulate_signal()

    plt.plot(signal['time'], signal['data'])
    plt.show()

    # 第二部分：对信号进行滤波
    freq_spec = frequency_spectrum(signal)

    plt.plot(freq_spec['freqs'], freq_spec['amplitude'])
    plt.show()

    stop_bands = [(1.3, 2.2)]
    # 阻带是0.8Hz到1.2Hz，滤波的目的是把频率1Hz的正弦波从信号中剔除

    filtered_signal = fft_filter(signal, stop_bands)

    plt.plot(signal['time'], signal['data'], signal['time'], filtered_signal)
    plt.show()