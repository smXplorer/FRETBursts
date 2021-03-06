#
# FRETBursts - A single-molecule FRET burst analysis toolkit.
#
# Copyright (C) 2014 Antonino Ingargiola <tritemio@gmail.com>
#
"""
The module :mod:`burstsearch.burstsearchlib` provides the low-level (or core)
burst search and photon counting functions.

All the burst search functions return a 2-D array (burst array) of shape Nx6,
where N is the number of bursts. The 6 columns contain the burst data.

In order to select one or more bursts, the burst array can be indexed or
sliced along the first dimension (row wise or axis=0). The second dimension
(columns) of the burst-array should be considered opaque, and the burst-data
functions (starting with `b_`) should be used to access it (instead of the
indexing the column). Using the `b_*` functions is both clearer and less
bug-prone than using a column index.

The list of burst-data functions is: :func:`b_start`, :func:`b_end`,
:func:`b_size`, :func:`b_width`, :func:`b_istart`, :func:`b_istart`,
:func:`b_iend`, :func:`b_rate`, :func:`b_separation`. You can note that they
are more than 6 because some of them return additional quantities derived
from the burst array columns.

As an example, assume having a burst array `mburst`. To take a slice of only
the first 10 bursts you can do::

    mburst10 = mburst[:10]   # new array with burst data of the first 10 bursts

To obtain the burst start of all the bursts::

    b_start(mbursts)

To obtain the burst size (number of photons) for the 10-th to 20-th burst::

    b_size(mbursts[10:20])

"""

from __future__ import division
import numpy as np
from fretbursts.utils.misc import pprint


## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#  GLOBAL VARIABLES
#

# Define name for the 6 column indexes in the Nx6 array containing the bursts
itstart, iwidth, inum_ph, iistart, iiend, itend = 0, 1, 2, 3, 4, 5

# Quick functions for burst data (burst array)
def b_start(bursts):
    """Time of 1st ph in burst"""
    return bursts[:, itstart]

def b_end(bursts):
    """Time of last ph in burst"""
    return bursts[:, itend]

def b_width(bursts):
    """Burst width in clk cycles"""
    return bursts[:, iwidth]

def b_istart(bursts):
    """Index of 1st ph in burst"""
    return bursts[:, iistart]

def b_iend(bursts):
    """Index of last ph in burst"""
    return bursts[:, iiend]

def b_size(bursts):
    """Number of ph in the burst"""
    return bursts[:, inum_ph]

def b_ph_rate(bursts):
    """Photon rate in burst (tot size/duration)"""
    return b_size(bursts) / b_width(bursts)

def b_separation(bursts):
    """Separation between nearby bursts"""
    return b_start(bursts)[1:] - b_end(bursts)[:-1]

## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#  LOW-LEVEL BURST SEARCH FUNCTIONS
#

def bsearch_py(t, L, m, T, label='Burst search', verbose=True):
    """Sliding window burst search. Pure python implementation.

    Finds bursts in the array `t` (int64). A burst starts when the photon rate
    is above a minimum threshold, and ends when the rate falls below the same
    threshold. The rate-threshold is defined by the ratio `m`/`T` (`m` photons
    in a time interval `T`). A burst is discarded if it has less than `L`
    photons.

    Arguments:
        t (array, int64): array of timestamps on which to perform the search
        L (int): minimum number of photons in a bursts. Bursts with size
            (or counts) < L are discarded.
        m (int): number of consecutive photons used to compute the rate.
        T (float): max time separation of `m` photons to be inside a burst
        label (string): a label printed when the function is called
        verbose (bool): if False, the function does not print anything.

    Returns:
        2D array of burst data, one row per burst, shape (N, 6), type int64.
        Each row contains (in the order): time of burst start, burst duration,
        number of photons, index of start time, time of burst end.
        To extract burst information it's safer to use the utility functions
        `b_*` (i.e. :func:`b_start`, :func:`b_size`, :func:`b_width`, etc...).
    """
    if verbose: pprint('Python search (v): %s\n' % label)
    bursts = []
    in_burst = False
    above_min_rate = (t[m-1:] - t[:t.size-m+1]) <= T
    for i in xrange(t.size-m+1):
        if above_min_rate[i]:
            if not in_burst:
                i_start = i
                in_burst = True
        elif in_burst:
            # Note that i_end is the index of the last ph in the current time
            # window, while the last ph in a burst is (i_end-1).
            # Note however that the number of ph in a burst is (i_end-i_start),
            # not (i_end-1)-i_start as may erroneously appears at first glace.
            in_burst = False
            i_end = i + m - 1
            if i_end - i_start >= L:
                burst_start, burst_end = t[i_start], t[i_end-1]
                bursts.append([burst_start, burst_end-burst_start,
                    i_end-i_start, i_start, i_end-1, burst_end])
    return np.array(bursts, dtype=np.int64)


## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#  Functions to count D and A photons in bursts
#

def count_ph_in_bursts_py(bursts, mask):
    """Counts number of photons in each burst counting only photons in `mask`.

    This function takes a burst-array and a boolean mask (photon selection)
    and computes the number of photons selected by the mask.
    It is used, for example, to count donor and acceptor photons in each burst.

    This is a reference implementation. In practice the multi-channel
    is always used instead (see :func:`mch_count_ph_in_bursts_py`).

    Arguments:
        Mburst (list of 2D arrays, int64): a list of burst-arrays, one per ch.
        Mask (list of 1D boolean arrays): a list of photon masks (one per ch),
            For each channel, the boolean mask must be of the same size of the
            timestamp array used for burst search.

    Returns:
        A list of 1D arrays, each containing the number of photons in the
        photon selection mask.
    """
    num_ph = np.zeros(bursts.shape[0], dtype=np.int16)
    for i, burst in enumerate(bursts):
        # Counts photons between start and end of current `burst`
        num_ph[i] = mask[ burst[iistart] : burst[iiend]+1 ].sum()
    return num_ph

def mch_count_ph_in_bursts_py(Mburst, Mask):
    """Counts number of photons in each burst counting only photons in `Mask`.

    This multi-channel function takes a list of burst-arrays and a list of
    photon masks and compute the number of photons selected by the mask.
    It is used, for example, to count donor and acceptor photons in each burst.

    Arguments:
        Mburst (list of 2D arrays, int64): a list of burst-arrays, one per ch.
        Mask (list of 1D boolean arrays): a list of photon masks (one per ch),
            For each channel, the boolean mask must be of the same size of the
            timestamp array used for burst search.

    Returns:
        A list of 1D arrays, each containing the number of photons in the
        photon selection mask.
    """
    Num_ph = []
    for bursts, mask in zip(Mburst, Mask):
        num_ph = np.zeros(bursts.shape[0], dtype=np.int16)
        for i, burst in enumerate(bursts):
            # Counts photons between start and end of current `burst`
            num_ph[i] = mask[ burst[iistart] : burst[iiend]+1 ].sum()
            #count_ph_in_bursts(bursts, mask).astype(float)
        Num_ph.append(num_ph.astype(float))
    return Num_ph


##
#  Try to import the optimized Cython functions
#

try:
    from burstsearchlib_c import bsearch_c
    bsearch = bsearch_c
    print " - Optimized (cython) burst search loaded."
except ImportError:
    bsearch = bsearch_py
    print " - Fallback to pure python burst search."

try:
    from burstsearchlib_c import mch_count_ph_in_bursts_c
    mch_count_ph_in_bursts = mch_count_ph_in_bursts_c
    print " - Optimized (cython) photon counting loaded."
except ImportError:
    mch_count_ph_in_bursts = mch_count_ph_in_bursts_py
    print " - Fallback to pure python photon counting."

##
#  Additional functions processing burst data

def burst_and(bursts_d, bursts_a):
    """From 2 burst arrays return bursts defined as intersection (AND rule).

    The two input burst-arrays come from 2 different burst searches.
    Returns new bursts representing the overlapping bursts in the 2 inputs
    with start and stop defined as intersection (or AND) operator.

    The format of both input and output arrays is "burst-array" as returned
    by :func:`bsearch_py`.

    Arguments:
        bursts_d (array): burst-array 1
        bursts_a (array): burst array 2. The number of burst in each of the
            input array can be different.

    Returns:
        Burst-array representing the intersection (AND) of overlapping bursts.
    """
    bstart_d, bend_d = b_start(bursts_d), b_end(bursts_d)
    bstart_a, bend_a = b_start(bursts_a), b_end(bursts_a)

    bursts = []
    burst0 = np.zeros(6, dtype=np.int64)
    i_d, i_a = 0, 0
    while i_d < bursts_d.shape[0] and i_a < bursts_a.shape[0]:
        # Skip any disjoint burst
        if bend_a[i_a] < bstart_d[i_d]:
            i_a += 1
            continue
        if bend_d[i_d] < bstart_a[i_a]:
            i_d += 1
            continue

        # Assign start and stop according the AND rule
        if bstart_a[i_a] < bstart_d[i_d] < bend_a[i_a]:
            start_burst = bursts_d[i_d]
        elif bstart_d[i_d] < bstart_a[i_a] < bend_d[i_d]:
            start_burst = bursts_a[i_a]

        if bend_d[i_d] < bend_a[i_a]:
            end_burst = bursts_d[i_d]
            i_d += 1
        else:
            end_burst = bursts_a[i_a]
            i_a += 1

        burst = burst0.copy()
        burst[itstart] = start_burst[itstart]
        burst[iistart] = start_burst[iistart]
        burst[itend] = end_burst[itend]
        burst[iiend] = end_burst[iiend]

        # Compute new width and size
        burst[iwidth] = burst[itend] - burst[itstart]
        burst[inum_ph] = burst[iiend] - burst[iistart] + 1

        bursts.append(burst)

    return np.vstack(bursts)


#