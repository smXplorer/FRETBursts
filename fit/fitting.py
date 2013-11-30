from exp_fitting import expon_fit, expon_fit_cdf
from gaussian_fitting import (
        gaussian_fit_hist, 
        gaussian_fit_pdf, 
        gaussian_fit_cdf, 
        two_gaussian_fit_EM, 
        two_gaussian_fit_cdf, 
        two_gaussian_fit_hist,
        two_gaussian_fit_hist_min,
        two_gauss_mix_pdf)

def Fit(values_mch, fitfun, **kwargs):
    """Multi-channel fit (ex. d.E, d.nt) with the fitfun (ex. gaussian_fit)."""
    return [fitfun(v, **kwargs) for v in values_mch]

