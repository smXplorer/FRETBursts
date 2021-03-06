#
# FRETBursts - A single-molecule FRET burst analysis toolkit.
#
# Copyright (C) 2014 Antonino Ingargiola <tritemio@gmail.com>
#
"""
Functions to fit the FRET peak using different algorithms.

This module provides a standard interface for different fitting techniques.
"""

import numpy as np
from scipy.stats import binom, expon
from scipy.optimize import minimize_scalar, leastsq

import fit.gaussian_fitting as gf


def sim_nd_na(E,N=1000, size_mean=100):
    """Simulate an exponential-size burst distribution with binomial (nd,na)
    """
    nt = np.ceil(expon.rvs(scale=size_mean, size=N)).astype(int)
    na = binom.rvs(nt, E)
    nd = nt - na
    return nd, na


def log_likelihood_binom(E, nd, na):
    """Likelihood function for (nd,na) to be from a binom with p=E (no BG)."""
    return -(np.log(binom.pmf(na, na+nd, E))).sum()

def fit_E_binom(nd, na, noprint=False, method='c', **kwargs):
    """Fit the E with MLE using binomial distribution.
    method  ('a','b', or 'c') choose how to handle negative (nd,na) values.
    """
    assert method in ['a', 'b', 'c']
    nd, na = np.round(nd).astype(int), np.round(na).astype(int)

    # The binomial distribution can not handle negative values
    # so we must find a way to "remove" the negativa values
    # a. remove bursts with neg. values, but we can skew the fit
    # b. remove bursts with nd < nd[na<0].max(), but few bursts left
    # c. remove bursts with na+nd < max(nd[na<0].max(),na[nd<0].max())
    #    giving a bit more bursts
    # NOTE: b and c have corner cases in which there are neg. bursts left
    pos_bursts = (nd>=0)*(na>=0)
    if (-pos_bursts).any():
        if not noprint: print "WARNING: Discarding negative burst sizes."
        if method == 'a':
            # a. remove bursts with neg. values
            nd, na = nd[pos_bursts], na[pos_bursts]
        elif method == 'b':
            # b. Cut all the part with na<0 to have a less skewed estimation
            if (na < 0).any():
                nd_min = nd[na<0].max()
                nd, na = nd[nd>nd_min], na[nd>nd_min]
        elif method == 'c':
            # c. remove bursts with na+nd < max(nd[na<0].max(),na[nd<0].max())
            nt_min = 0
            if (na < 0).any():
                nt_min = nd[na<0].max()
            if (nd < 0).any():
                nt_min = max([na[nd<0].max(), nt_min])
            nd, na = nd[nd+na>nt_min], na[nd+na>nt_min]

        if not noprint: print " - Bursts left:", nd.size
        assert (nd>=0).all() and (na>=0).all()
    min_kwargs = dict(bounds=(0,1), method='bounded',
            options={'disp':1, 'xtol': 1e-6})
    min_kwargs.update(**kwargs)
    res = minimize_scalar(log_likelihood_binom, args=(nd,na), **min_kwargs)
    return res.x


def log_likelihood_poisson_nt(E, nd, na, bg_a):
    """Likelihood function for na extracted from Poisson. nd, na BG corrected.
    """
    k = 1.*E/(1-E)
    logP = 0
    nt = nd + na
    for nti, nai, bg_ai in zip(nt, na, bg_a):
        lam_ai = k*(nti)/(1+k) + bg_ai
        logP += (nai+bg_ai)*np.log(lam_ai) - lam_ai
    return -logP

def log_likelihood_poisson_na(E, nd, na, bg_a):
    """Likelihood function for na extracted from Poisson. nd, na BG corrected.
    """
    k = 1.*E/(1-E)
    logP = 0
    for ndi, nai, bg_ai in zip(nd, na, bg_a):
        lam_ai = k*ndi + bg_ai
        logP += (nai+bg_ai)*np.log(lam_ai) - lam_ai
    return -logP

def log_likelihood_poisson_nd(E, nd, na, bg_d):
    """Likelihood function for nd extracted from Poisson. nd, na BG corrected.
    """
    k = 1.*E/(1-E)
    logP = 0
    for ndi, nai, bg_di in zip(nd, na, bg_d):
        lam_di = (1./k)*nai + bg_di
        logP += (ndi+bg_di)*np.log(lam_di) - lam_di
    return -logP

def fit_E_poisson_nt(nd, na, bg_a, **kwargs):
    """Fit the E using MLE with na extracted from a Poisson.
    """
    min_kwargs = dict(bounds=(-0.1,1.1), method='bounded',
            options={'disp':1, 'xtol': 1e-6})
    min_kwargs.update(**kwargs)
    res = minimize_scalar(log_likelihood_poisson_nt, args=(nd, na, bg_a),
            **min_kwargs)
    E = res.x
    return E

def fit_E_poisson_na(nd, na, bg_a, **kwargs):
    """Fit the E using MLE with na extracted from a Poisson.
    """
    min_kwargs = dict(bounds=(-0.1,1.1), method='bounded',
            options={'disp':1, 'xtol': 1e-6})
    min_kwargs.update(**kwargs)
    res = minimize_scalar(log_likelihood_poisson_na, args=(nd, na, bg_a),
            **min_kwargs)
    E = res.x
    return E

def fit_E_poisson_nd(nd, na, bg_d, **kwargs):
    """Fit the E using MLE with nd extracted from a Poisson.
    """
    min_kwargs = dict(bounds=(-0.1,1.1), method='bounded',
            options={'disp':1, 'xtol': 1e-6})
    min_kwargs.update(**kwargs)
    res = minimize_scalar(log_likelihood_poisson_nd, args=(nd, na, bg_d),
            **min_kwargs)
    E = res.x
    return E

def fit_E_hist(nd, na, gamma=1., **kwargs):
    """Fit E using the histogram curve-fit (see gaussian_fit_hist).
    You can specify `weights` that will be passed to the `histogram` function.
    """
    E = na/(na + gamma*nd)
    if 'weights' in kwargs:
        w = get_weights(nd, na, weights=kwargs['weights'])
        kwargs.update(weights=w)
    E_mu, E_sig = gf.gaussian_fit_hist(E, mu0=0.5, sigma0=0.1, **kwargs)
    return E_mu

def fit_E_cdf(nd, na, gamma=1., **kwargs):
    """Fit E using the CDF curve-fit (see gaussian_fit_cdf).
    No weights are possible with this method.
    """
    E = na/(na + gamma*nd)
    E_mu, E_sig = gf.gaussian_fit_cdf(E, mu0=0.5, sigma0=0.1, **kwargs)
    return E_mu

def get_dist_euclid(nd, na, E_fit=None, slope=None):
    """Returns the euclidean distance of (nd,na) from a fit line.
    The fit line is specified by `slope` or by `E_fit`. Intercept is always 0.
    """
    if slope is None:
        try:
            slope = E_fit/(1-E_fit)
        except TypeError:
            # this happens if E_fit is None
            raise ValueError('One among `E_fit` or `slope` must be not None.')

    # For each burst (nd,na) find the closest point on the fitted line
    nd_l = (slope*na + nd)/(slope**2+1)
    na_l = slope*nd_l
    distances = np.sqrt((nd-nd_l)**2 + (na-na_l)**2)
    return distances

def get_weights(nd, na, weights, naa=0, gamma=1.):
    """Return burst weigths computed according to different criteria.

    `nd`, `na`: background corrected donor and acceptor ph. per burst
    `weights`: (string) type of weights (if None returns uniform weights).
                see source for all the possible weights.
    """
    nt = nd*gamma + na + naa
    if weights is None:           # all weights the same
        weights = np.ones(nd.size)
    elif weights is 'size':       # weight = burst size (with gamma)
        weights = nt
    elif weights is 'size_min':   # weight = burst size - min(burst size)
        weights = nt - nt.min() + 1
    elif weights is 'size2':      # weight = (burst size)^2
        weights = nt**2
    elif weights is 'sqrt':       # weigth = sqrt(burst size)
        weights = np.sqrt(nt)
    elif weights is 'inv_size':   # weight = 1/(burst size)
        weights = 1./(nt)
    elif weights is 'inv_sqrt':   # weight = 1/sqrt(burst size)
        weights = 1./np.sqrt(nt)
    elif weights is 'cum_size':   # weight = CDF_of_burst_sizes(burst size)
        ecdf = [np.sort(nt), 1.*np.arange(1, nt.size+1)/nt.size]
        weights = np.interp(nt, ecdf[0], ecdf[1], left=0, right=1)
    elif weights is 'cum_size2':   # weight = CDF_of_burst_sizes(burst size)^2
        ecdf = [np.sort(nt), 1.*np.arange(1, nt.size+1)/nt.size]
        weights = np.interp(nt, ecdf[0], ecdf[1]**2, left=0, right=1)
    else:
        raise ValueError
    assert weights.size == nd.size
    return weights


def fit_E_slope(nd, na, weights=None, gamma=1.):
    """Fit E with a least-squares fitting of slope on (nd,na) plane."""
    weights = get_weights(nd, na, weights=weights, gamma=gamma)
    #err_fun = lambda k, x, y, w: (y - k*x)*w
    err_fun = lambda k, x, y, w: w*get_dist_euclid(nd=x, na=y, slope=k)
    res = leastsq(err_fun, x0=1, args=(nd, na, weights))
    #print res
    return res[0][0]/(res[0][0]+1)

def fit_E_E_size(nd, na, weights=None, gamma=1., gamma_correct=False):
    """Fit the E with least-square minimization of errors on burst E values."""
    weights = get_weights(nd, na, weights=weights, gamma=gamma)
    if gamma_correct:
        err_fun = lambda E_fit, d, a, w: (E_fit - 1.*a/(gamma*d+a))*w
    else:
        err_fun = lambda E_fit, d, a, w: (E_fit - 1.*a/(d+a))*w
    res = leastsq(err_fun, x0=0.5, args=(nd, na, weights))
    return res[0][0]

def fit_E_m(nd, na, weights=None, gamma=1., gamma_correct=False):
    """Fit the E with a weighted mean of burst E values."""
    weights = get_weights(nd, na, weights=weights, gamma=gamma)
    if gamma_correct:
        E = na/(na + gamma*nd)
    else:
        E = na/(na + nd)
    E_fit = np.dot(E, weights)/weights.sum()
    return E_fit



