#!/usr/bin/python3
# -*- coding: utf-8 -*-
# shindo.py
# Functions to calculate JMA instrumental shindo scale
# from acceleration data stored in 3-D NumPy ndarray
# (c) 2021 @RR_Inyo
# Released under the MIT license
# https://opensource.org/licenses/mit-license.php

import numpy as np

def _filter(A: np.ndarray, Ts: float) -> None:
    """
    @brief Apply filter to the accleration spectra
    @param A 3-D acceleration frequency-domain spectra, N-S, E-W, and U-D
    @param Ts Sampling period
    """
    N = len(A)
    k = np.arange(N)
    f = k / (N * Ts * 2)

    # Periodic-effect filter
    epsilon = 0.0001  # To prevent division by zero
    W_pe = np.sqrt(1 / (f + epsilon))

    # High-cut filter
    x = f / 10
    W_hc = 1 / np.sqrt( \
             1 + 0.694 * x**2 + 0.241 * x**4 + 0.0557 * x**6 \
             + 0.009664 * x**8 + 0.00134 * x**10 + 0.000155 * x**12 \
    )

    # Low-cut filter
    W_lc = np.sqrt(1 - np.exp(-(f / 0.5)**3))

    # Apply filter
    A[:,0] *= (W_pe * W_hc * W_lc)
    A[:,1] *= (W_pe * W_hc * W_lc)
    A[:,2] *= (W_pe * W_hc * W_lc)

def _search_aval(a: np.ndarray, Ts: float) -> float:
    """
    @brief Search for the a value
    @param a 3-D acceleration time-domain data in [gal], N-S, E-W, and U-D
    @param Ts Sampling period
    @return The a value found
    """
    aval = 2000.0            # Initial value of search [gal]
    T_ref = 0.3              # Time where acceleration is above the a value
    epsilon = T_ref * 0.001  # Acceptable error
    while True:
        T_above_aval = np.count_nonzero(a >= aval) * Ts

        # Too high
        if T_above_aval < T_ref - epsilon:
            aval -= aval / 2
            continue

        # Too low
        if T_above_aval > T_ref + epsilon:
            aval += aval / 2
            continue

        # The a value found
        break
    return aval

def getShindo(a: np.ndarray, Ts: float) -> float:
    """
    @brief Calculates JMA shindo scale from acceleration data as ndarray 
    @param a 3-D acceleration time-domain data in [gal], N-S, E-W, and U-D
    @param Ts Sampling period
    @return Calculated instrumental shindo scale
    """

    # Perform FFT
    A = np.fft.rfft(a, axis = 0)

    # Apply filter defined by JMA
    _filter(A, Ts)

    # Perform inverse FFT
    afil = np.fft.irfft(A, axis = 0)
    afil_total = np.sqrt(np.sum(afil**2, axis = 1))

    # Search for the a value
    aval = _search_aval(afil_total, Ts)

    # Calculate JMA instrumental seismic intensity
    I_raw = 2 * np.log10(aval) + 0.94
    I = np.floor(np.round(I_raw, decimals = 2) * 10) / 10

    return I

def getShindoName(I: float, lang: str = 'jp') -> str:
    """
    @brief Convert instrumental shindo scale to a string
    @param I JMA instrumental shindo scale
    @param lang Language ('jp' or 'en')
    """
    if I < 0.5:
        return '0'
    elif 0.5 <= I < 1.5:
        return '1'
    elif 1.5 <= I < 2.5:
        return '2'
    elif 2.5 <= I < 3.5:
        return '3'
    elif 3.5 <= I < 4.5:
        return '4'
    elif 4.5 <= I < 5.0:
        if lang == 'jp':
            return '5弱'
        else:
            return '5-'
    elif 5.0 <= I < 5.5:
        if lang == 'jp':
            return '5強'
        else:
            return '5+'
    elif 5.5 <= I < 6.0:
        if lang == 'jp':
            return '6弱'
        else:
            return '6-'
    elif 6.0 <= I < 6.5:
        if lang == 'jp':
            return '6強'
        else:
            return '6+'
    elif I >= 6.5:
        return '7'

# Test bench
# Downloading acceleration data from the JMA website
# Example chosen here is an earthquake observed in Yonago, Tottori
# at 13:30 on October 6th, 2000
# Calculation process and results are explained in
# https://www.data.jma.go.jp/svd/eqev/data/kyoshin/kaisetsu/calc_sindo.htm
if __name__ == '__main__':

    import sys
    import time

    # Download seismic record data
    # Data format is explaind on the JMA website
    if len(sys.argv) < 2:
        file = 'https://www.data.jma.go.jp/svd/eqev/data/kyoshin/jishin/001006_tottori-seibu/dat/AA06EA01.csv'
    else:
        file = sys.argv[1]

    kwargs = {'delimiter': ',', 'skiprows': 7, 'usecols': [0, 1, 2], 'encoding': 'sjis'}
    a = np.loadtxt(file, **kwargs)

    a_total = np.sqrt(a[:,0]**2 + a[:,1]**2 + a[:,2]**2)
    Ts = 0.01

    # Show message
    print('Calculation test for an earthquake data downloaded from the JMA website')
    print(f'Data URL: {file}')
    print(f'Max. north-south accel.: {np.max(np.abs(a[:,0])):.2f} gal')
    print(f'Max. east-west accel.: {np.max(np.abs(a[:,1])):.2f} gal')
    print(f'Max. up-down accel.: {np.max(np.abs(a[:,2])):.2f} gal')
    print(f'Max. total accel.: {np.max(np.abs(a_total)):.2f} gal')

    # Calculate JMA insrumental shindo scale
    print('Calculating...')
    t0 = time.perf_counter()
    I = getShindo(a, Ts)
    t1 = time.perf_counter() - t0
    print(f'JMA instrumental seismic intensity (shindo): {I}')
    print(f'JMA shindo in Japanese: 震度{getShindoName(I)}')
    print(f'Time needed to calculate shindo: {t1 * 1e6:.2f} microsec')

    print('Done!')
