# encoding: utf-8
#
# FRETBursts - A single-molecule FRET burst analysis toolkit.
#
# Copyright (C) 2014 Antonino Ingargiola <tritemio@gmail.com>
#
"""
This module defines all the plotting functions for the `Data` object.

The main plot function is `dplot()` that takes, as parameters, a `Data()`
object and a 1-ch-plot-function and creates a subplot for each channel.

The 1-ch plot functions are usually called through `dplot` but can also be
called directly to make a single channel plot.

The 1-ch plot functions names all start with the plot type (`timetrace`,
`ratetrace`, `hist` or `scatter`).

**Example 1** - Plot the timetrace for all ch::

    dplot(d, timetrace, scroll=True)

**Example 2** - Plot a FRET histogramm for each ch with a fit overlay::

    dplot(d, hist_fret, show_model=True)

"""

from __future__ import division
import warnings

# Numeric imports
import numpy as np
from numpy import arange, r_
from matplotlib.mlab import normpdf
from scipy.stats import erlang
from scipy.interpolate import UnivariateSpline

# Graphics imports
import matplotlib.pyplot as plt
from matplotlib.pyplot import (plot, hist, xlabel, ylabel, grid, title, legend,
                               gca, gcf)
from matplotlib.patches import Rectangle, Ellipse
from matplotlib.collections import PatchCollection

# Local imports
from ph_sel import Ph_sel
import burstlib as bl
import burstlib_ext as bext
import background as bg
from utils.misc import clk_to_s, pprint
from scroll_gui import ScrollingToolQT
import gui_selection as gs


params = {
        'font.size': 12,
        'legend.fontsize': 11,
        }
plt.rcParams.update(params)


##
# Globals
#
blue = '#0055d4'
green = '#2ca02c'
red = "#e74c3c" # '#E41A1C'
purple = "#9b59b6"

_ph_sel_color_dict = {Ph_sel('all'): blue, Ph_sel(Dex='Dem'): green,
                      Ph_sel(Dex='Aem'): red, Ph_sel(Aex='Aem'): purple,
                      Ph_sel(Aex='Dem'): 'c', }
_ph_sel_label_dict = {Ph_sel('all'): 'All-ph', Ph_sel(Dex='Dem'): 'DexDem',
                      Ph_sel(Dex='Aem'): 'DexAem', Ph_sel(Aex='Aem'): 'AexAem',
                      Ph_sel(Aex='Dem'): 'AexDem'}

# Global store for plot status
_plot_status = {}

# Global store for GUI handlers
gui_status = {'first_plot_in_figure': True}


##
#  Utility functions
#
def _normalize_kwargs(kwargs, kind='patch'):
    """Convert matplotlib keywords from short to long form."""
    if kind == 'line2d':
        long_names = dict(c='color', ls='linestyle', lw='linewidth',
                          mec='markeredgecolor', mew='markeredgewidth',
                          mfc='markerfacecolor', ms='markersize',)
    elif kind == 'patch':
        long_names = dict(c='color', ls='linestyle', lw='linewidth',
                          ec='edgecolor', fc='facecolor',)
    for short_name in long_names:
        if short_name in kwargs:
            kwargs[long_names[short_name]] = kwargs.pop(short_name)
    return kwargs

def bsavefig(d, s):
    """Save current figure with name in `d`, appending the string `s`."""
    plt.savefig(d.Name()+s)

##
#  Multi-channel plot functions
#

def mch_plot_bg(d, **kwargs):
    """Plot background vs channel for DA, D and A photons."""
    plot(r_[1:d.nch+1],[b.mean()*1e-3 for b in d.bg], lw=2, color='b',
            label=' T', **kwargs)
    plot(r_[1:d.nch+1],[b.mean()*1e-3 for b in d.bg_dd], color='g', lw=2,
            label=' D', **kwargs)
    plot(r_[1:d.nch+1],[b.mean()*1e-3 for b in d.bg_ad], color='r', lw=2,
            label=' A', **kwargs)
    xlabel("CH"); ylabel("kcps"); grid(True); legend(loc='best')
    title(d.name())

def mch_plot_bg_ratio(d):
    """Plot ratio of A over D background vs channel."""
    plot(r_[1:d.nch+1],[ba.mean()/bd.mean() for bd,ba in zip(d.bg_dd,d.bg_ad)],
            color='g', lw=2, label='A/D')
    xlabel("CH"); ylabel("BG Ratio A/D"); grid(True)
    title("BG Ratio A/D "+d.name())

def mch_plot_bsize(d):
    """Plot mean burst size vs channel."""
    CH = np.arange(1, d.nch+1)
    plot(CH, [b.mean() for b in d.nt], color='b', lw=2, label=' T')
    plot(CH, [b.mean() for b in d.nd], color='g', lw=2, label=' D')
    plot(CH, [b.mean() for b in d.na], color='r', lw=2, label=' A')
    xlabel("CH"); ylabel("Mean burst size")
    grid(True)
    legend(loc='best')
    title(d.name())


##
#  ALEX alternation period plots
#
def plot_alternation_hist(d, bins=100, **kwargs):
    plt.figure()
    ph_times_t, det_t, period = d.ph_times_t, d.det_t, d.alex_period
    d_ch, a_ch = d.det_donor_accept
    d_em_t = (det_t == d_ch)
    kwargs.update(bins=bins, alpha=0.2)
    hist(ph_times_t[d_em_t] % period, color='g', label='D', **kwargs)
    hist(ph_times_t[~d_em_t] % period, color='r', label='A', **kwargs)

    if d.D_ON[0] < d.D_ON[1]:
        plt.axvspan(d.D_ON[0], d.D_ON[1], color='g', alpha=0.1)
    else:
        plt.axvspan(0,d.D_ON[1], color='g', alpha=0.1)
        plt.axvspan(d.D_ON[0], period, color='g', alpha=0.1)

    if d.A_ON[0] < d.A_ON[1]:
        plt.axvspan(d.A_ON[0], d.A_ON[1], color='r', alpha=0.1)
    else:
        plt.axvspan(0, d.A_ON[1], color='r', alpha=0.1)
        plt.axvspan(d.A_ON[0], period, color='r', alpha=0.1)

    legend(loc='best')

def plot_alternation_hist_nsalex(d):
    nanotimes_d = d.nanotimes_t[d.det_t == d.det_donor_accept[0]]
    nanotimes_a = d.nanotimes_t[d.det_t == d.det_donor_accept[1]]
    hist(nanotimes_d, bins=np.arange(4096), histtype='step', lw=1.2,
         alpha=0.5, color='g', label='Donor')
    hist(nanotimes_a, bins=np.arange(4096), histtype='step', lw=1.2,
         alpha=0.5, color='r', label='Acceptor')
    plt.yscale('log')
    plt.axvspan(d.D_ON[0], d.D_ON[1], color='g', alpha=0.1)
    plt.axvspan(d.A_ON[0], d.A_ON[1], color='r', alpha=0.1)


## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
##  Multi-channel plots
## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

##
#  Timetrace plots
#
def _plot_bursts(d, i, t_max_clk, pmax=1e3, pmin=0, color="#999999"):
    """Highlights bursts in a timetrace plot."""
    b = d.mburst[i]
    if np.size(b) == 0: return
    pprint("CH %d burst..." % (i+1))
    bs = b[bl.b_start(b) < t_max_clk]
    start = bl.b_start(bs)*d.clk_p
    end = bl.b_end(bs)*d.clk_p
    R = []
    width = end-start
    ax = gca()
    for s,w in zip(start,width):
        r = Rectangle(xy=(s,pmin), height=pmax-pmin, width=w)
        r.set_clip_box(ax.bbox); r.set_zorder(0)
        R.append(r)
    ax.add_artist(PatchCollection(R, lw=0, color=color))
    pprint("[DONE]\n")

def _plot_rate_th(d, i, F, ph_sel, invert=False, scale=1,
                  plot_style_={}, rate_th_style={}):
    """Plots background_rate*F as a function of time.

    `plot_style_` is the style of a timetrace/ratetrace plot used as starting
    style. Linestyle and label are changed. Finally, `rate_th_style` is
    applied and can override any style property.

    If rate_th_style_['label'] is 'auto' the label is generated from
    plot_style_['label'] and F.
    """
    if F is None:
        F = d.F if F in d else 6

    rate_th_style_ = dict(plot_style_)
    rate_th_style_.update(linestyle='--', label='auto')
    rate_th_style_.update(_normalize_kwargs(rate_th_style, kind='line2d'))
    if rate_th_style_['label'] is 'auto':
        rate_th_style_['label'] = 'bg_rate*%d %s' % \
                                    (F, plot_style_['label'])
    x_rate = np.hstack(d.Ph_p[i])*d.clk_p
    y_rate = F*np.hstack([(rate, rate) for rate in d.bg_from(ph_sel)[i]])
    y_rate *= scale
    if invert:
        y_rate *= -1
    plot(x_rate, y_rate, **rate_th_style_)

def _gui_timetrace_burst_sel(d, fig, ax):
    """Add GUI burst selector via mouse click to the current plot."""
    global gui_status
    if gui_status['first_plot_in_figure']:
        gui_status['burst_sel'] = gs.MultiAxPointSelection(fig, ax, d)
    else:
        gui_status['burst_sel'].ax_list.append(ax)

def _gui_timetrace_scroll(fig):
    """Add GUI to scroll a timetrace wi a slider."""
    global gui_status
    if gui_status['first_plot_in_figure']:
        gui_status['scroll_gui'] = ScrollingToolQT(fig)


def timetrace_single(d, i=0, binwidth=1e-3, bins=None, tmin=0, tmax=200,
                     ph_sel=Ph_sel('all'), invert=False, bursts=False,
                     burst_picker=True, scroll=False, cache_bins=True,
                     plot_style={}, show_rate_th=True, F=None,
                     rate_th_style={}, set_ax_limits=True,
                     burst_color='#BBBBBB'):
    """Plot the timetrace (histogram) of timestamps for a photon selection.

    See :func:`timetrace` to plot multiple photon selections (i.e.
    Donor and Acceptor photons) in one step.
    """
    if tmax is None or tmax < 0:
        tmax = d.time_max()

    def _get_cache():
        return (timetrace_single.bins, timetrace_single.x,
                timetrace_single.binwidth,
                timetrace_single.tmin, timetrace_single.tmax)

    def _set_cache(bins, x, binwidth, tmin, tmax):
        cache = dict(bins=bins, x=x, binwidth=binwidth, tmin=tmin, tmax=tmax)
        for name, value in cache.items():
            setattr(timetrace_single, name, value)

    def _del_cache():
        names = ['bins', 'x', 'binwidth', 'tmin', 'tmax']
        for name in names:
            delattr(timetrace_single, name)

    def _has_cache():
        return hasattr(timetrace_single, 'bins')

    def _has_cache_for(binwidth, tmin, tmax):
        if _has_cache():
            return (binwidth, tmin, tmax) == _get_cache()[2:]
        return False

    # If cache_bins is False delete any previously saved attribute
    if not cache_bins and _has_cache:
        _del_cache()

    tmin_clk, tmax_clk = tmin/d.clk_p, tmax/d.clk_p
    binwidth_clk = binwidth/d.clk_p

    # If bins is not passed try to use the
    if bins is None:
        if cache_bins and _has_cache_for(binwidth, tmin, tmax):
            bins, x = timetrace_single.bins, timetrace_single.x
        else:
            bins = np.arange(tmin_clk, tmax_clk + 1, binwidth_clk)
            x = bins[:-1]*d.clk_p + 0.5*binwidth
            if cache_bins:
                _set_cache(bins, x, binwidth, tmin, tmax)

    # Compute histogram
    ph_times = d.get_ph_times(i, ph_sel=ph_sel)
    timetrace, _ = np.histogram(ph_times, bins=bins)
    if invert:
        timetrace *= -1

    # Plot bursts
    if bursts:
        t_max_clk = int(tmax/d.clk_p)
        print burst_color
        _plot_bursts(d, i, t_max_clk, pmax=500, pmin=-500, color=burst_color)

    # Plot timetrace
    plot_style_ = dict(linestyle='-', linewidth=1.2, marker=None)
    if ph_sel in _ph_sel_color_dict:
        plot_style_['color'] = _ph_sel_color_dict[ph_sel]
        plot_style_['label'] = _ph_sel_label_dict[ph_sel]
    else:
        plot_style_['label'] = str(ph_sel)
    plot_style_.update(_normalize_kwargs(plot_style, kind='line2d'))
    plot(x, timetrace, **plot_style_)

    # Plot burst-search rate-threshold
    if show_rate_th and 'bg' in d:
        _plot_rate_th(d, i, F=F, ph_sel=ph_sel, invert=invert,
                      scale=binwidth, plot_style_=plot_style_,
                      rate_th_style=rate_th_style)

    xlabel('Time (s)'); ylabel('# ph')
    if burst_picker:
        _gui_timetrace_burst_sel(d, gcf(), gca())
    if scroll:
        _gui_timetrace_scroll(gcf())

    if set_ax_limits:
        plt.xlim(tmin, tmin + 1)
        if not invert:
            plt.ylim(ymax=100)
        else:
            plt.ylim(ymin=-100)
        _plot_status['timetrace_single'] = {'autoscale': False}


def timetrace(d, i=0, binwidth=1e-3, bins=None, tmin=0, tmax=200,
              bursts=False, burst_picker=True, scroll=False,
              show_rate_th=True, F=None, rate_th_style={'label': None},
              show_aa=True, legend=False, set_ax_limits=True,
              burst_color='#BBBBBB',
              #dd_plot_style={}, ad_plot_style={}, aa_plot_style={}
              ):
    """Plot the timetraces (histogram) of photon timestamps.
    """
    # Plot bursts
    if bursts:
        t_max_clk = int(tmax/d.clk_p)
        _plot_bursts(d, i, t_max_clk, pmax=500, pmin=-500, color=burst_color)

    # Plot multiple timetraces
    ph_sel_list = [Ph_sel(Dex='Dem'), Ph_sel(Dex='Aem')]
    invert_list = [False, True]
    burst_picker_list = [burst_picker, False]
    scroll_list = [scroll, False]
    if d.ALEX and show_aa:
         ph_sel_list.append(Ph_sel(Aex='Aem'))
         invert_list.append(True)
         burst_picker_list.append(False)
         scroll_list.append(False)

    for ix, (ph_sel, invert) in enumerate(zip(ph_sel_list, invert_list)):
        if not bl.mask_empty(d.get_ph_mask(i, ph_sel=ph_sel)):
            timetrace_single(d, i, binwidth=binwidth, bins=bins, tmin=tmin,
                    tmax=tmax, ph_sel=ph_sel, invert=invert, bursts=False,
                    burst_picker=burst_picker_list[ix],
                    scroll=scroll_list[ix], cache_bins=True,
                    show_rate_th=show_rate_th, F=F,
                    rate_th_style=rate_th_style, set_ax_limits=set_ax_limits)
    if legend:
        plt.legend(loc='best', fancybox=True)


def ratetrace_single(d, i=0, m=None, max_num_ph=1e6, tmin=0, tmax=200,
                     ph_sel=Ph_sel('all'), invert=False, bursts=False,
                     burst_picker=True, scroll=False, plot_style={},
                     show_rate_th=True,  F=None, rate_th_style={},
                     set_ax_limits=True, burst_color='#BBBBBB'):
    """Plot the ratetrace of timestamps for a photon selection.

    See :func:`ratetrace` to plot multiple photon selections (i.e.
    Donor and Acceptor photons) in one step.
    """
    if tmax is None or tmax < 0:
        tmax = d.time_max()

    if m is None:
        m = d.m if m in d else 10

    # Plot bursts
    if bursts:
        t_max_clk = int(tmax/d.clk_p)
        _plot_bursts(d, i, t_max_clk, pmax=500, pmin=-500, color=burst_color)

    # Compute ratetrace
    tmin_clk, tmax_clk = tmin/d.clk_p, tmax/d.clk_p
    ph_times = d.get_ph_times(i, ph_sel=ph_sel)
    iph1 = np.searchsorted(ph_times, tmin_clk)
    iph2 = np.searchsorted(ph_times, tmax_clk)
    if iph2 - iph1 > max_num_ph:
        iph2 = iph1 + max_num_ph
        tmax = ph_times[iph2]*d.clk_p
        warnings.warn(('Max number of photons reached in ratetrace_single().'
                       '\n    tmax is reduced to %ds. To plot a wider '
                       'time range increase `max_num_ph`.') % tmax,
                      UserWarning)
    ph_times = ph_times[iph1:iph2]
    rates = 1e-3*bl.ph_rate(m, ph_times)/d.clk_p
    if invert:
        rates *= -1
    times = bl.ph_rate_t(m, ph_times)*d.clk_p

    # Plot ratetrace
    plot_style_ = dict(linestyle='-', linewidth=1.2, marker=None)
    if ph_sel in _ph_sel_color_dict:
        plot_style_['color'] = _ph_sel_color_dict[ph_sel]
        plot_style_['label'] = _ph_sel_label_dict[ph_sel]
    plot_style_.update(_normalize_kwargs(plot_style, kind='line2d'))
    plot(times, rates, **plot_style_)

    # Plot burst-search rate-threshold
    if show_rate_th and 'bg' in d:
        _plot_rate_th(d, i, F=F, scale=1e-3, ph_sel=ph_sel, invert=invert,
                      plot_style_=plot_style_, rate_th_style=rate_th_style)

    xlabel('Time (s)'); ylabel('Rate (kcps)')
    if burst_picker:
        _gui_timetrace_burst_sel(d, gcf(), gca())
    if scroll:
        _gui_timetrace_scroll(gcf())

    if set_ax_limits:
        plt.xlim(tmin, tmin + 1)
        if not invert:
            plt.ylim(ymax=100)
        else:
            plt.ylim(ymin=-100)
        _plot_status['ratetrace_single'] = {'autoscale': False}


def ratetrace(d, i=0, m=None, max_num_ph=1e6, tmin=0, tmax=200,
              bursts=False, burst_picker=True, scroll=False,
              show_rate_th=True, F=None, rate_th_style={'label': None},
              show_aa=True, legend=False, set_ax_limits=True,
              #dd_plot_style={}, ad_plot_style={}, aa_plot_style={}
              burst_color='#BBBBBB'):
    """Plot the ratetraces of photon timestamps.
    """
    # Plot bursts
    if bursts:
        t_max_clk = int(tmax/d.clk_p)
        _plot_bursts(d, i, t_max_clk, pmax=500, pmin=-500, color=burst_color)

    # Plot multiple timetraces
    ph_sel_list = [Ph_sel(Dex='Dem'), Ph_sel(Dex='Aem')]
    invert_list = [False, True]
    burst_picker_list = [burst_picker, False]
    scroll_list = [scroll, False]
    if d.ALEX and show_aa:
         ph_sel_list.append(Ph_sel(Aex='Aem'))
         invert_list.append(True)
         burst_picker_list.append(False)
         scroll_list.append(False)

    for ix, (ph_sel, invert) in enumerate(zip(ph_sel_list, invert_list)):
        if not bl.mask_empty(d.get_ph_mask(i, ph_sel=ph_sel)):
            ratetrace_single(d, i, m=m, max_num_ph=max_num_ph, tmin=tmin,
                    tmax=tmax, ph_sel=ph_sel, invert=invert, bursts=False,
                    burst_picker=burst_picker_list[ix],
                    scroll=scroll_list[ix],
                    show_rate_th=show_rate_th, F=F,
                    rate_th_style=rate_th_style, set_ax_limits=set_ax_limits)
    if legend:
        plt.legend(loc='best', fancybox=True)


def sort_burst_sizes(sizes, levels=np.arange(1, 102, 20)):
    """Return a list of masks that split `sizes` in levels.
    Used by timetrace_fret to select burst based on size groups.
    """
    masks = []
    for level1, level2 in zip(levels[:-1], levels[1:]):
        masks.append((sizes >= level1)*(sizes < level2))
    masks.append(sizes >= level2)
    return masks

def timetrace_fret(d, i=0, gamma=1., **kwargs):
    """Timetrace of burst FRET vs time. Uses `plot`."""
    b = d.mburst[i]
    bsizes = bl.select_bursts.get_burst_size(d, ich=i, gamma=gamma)

    style_kwargs = dict(marker='o', mew=0.5, color='b', mec='grey',
                        alpha=0.4, ls='')
    style_kwargs.update(**kwargs)

    t, E = bl.b_start(b)*d.clk_p, d.E[i]
    levels = sort_burst_sizes(bsizes)
    for ilev, level in enumerate(levels):
        plt.plot(t[level], E[level], ms=np.sqrt((ilev+1)*15),
                 **style_kwargs)
    plt.plot(bl.b_start(b)*d.clk_p, d.E[i], '-k', alpha=0.1, lw=1)
    xlabel('Time (s)'); ylabel('E')
    _gui_timetrace_burst_sel(d, i, timetrace_fret, gcf(), gca())

def timetrace_fret_scatter(d, i=0, gamma=1., **kwargs):
    """Timetrace of burst FRET vs time. Uses `scatter` (slow)."""
    b = d.mburst[i]
    bsizes = bl.select_bursts.get_burst_size(d, ich=i, gamma=gamma)

    style_kwargs = dict(s=bsizes, marker='o', alpha=0.5)
    style_kwargs.update(**kwargs)
    plt.scatter(bl.b_start(b)*d.clk_p, d.E[i], **style_kwargs)
    xlabel('Time (s)'); ylabel('E')

def timetrace_bg(d, i=0, nolegend=False, ncol=3):
    """Timetrace of background rates."""
    t = arange(d.bg[i].size)*d.bg_time_s
    plot(t, 1e-3*d.bg[i], 'k', lw=2, label="T: %d cps" % d.rate_m[i])
    plot(t, 1e-3*d.bg_dd[i], 'g', lw=2, label="DD: %d cps" % d.rate_dd[i])
    plot(t, 1e-3*d.bg_ad[i], 'r', lw=2, label="AD: %d cps" % d.rate_ad[i])
    if d.ALEX:
        plot(t, 1e-3*d.bg_aa[i], 'm', lw=2, label="AA: %d cps" % d.rate_aa[i])
    if not nolegend:
        legend(loc='best', frameon=False, ncol=ncol)
    xlabel("Time (s)"); ylabel("BG rate (kcps)"); grid(True)
    plt.ylim(ymin=0)

def timetrace_b_rate(d, i=0):
    """Timetrace of bursts-per-second in each period."""
    t = arange(d.bg[i].size)*d.bg_time_s
    b_rate = r_[[(d.bp[i] == p).sum() for p in xrange(d.bp[i].max()+1)]]
    b_rate /= d.bg_time_s
    if t.size == b_rate.size+1:
        t = t[:-1] # assuming last period without bursts
    else:
        assert t.size == b_rate.size
    plot(t, b_rate, lw=2, label="CH%d" % (i+1))
    legend(loc='best', fancybox=True, frameon=False, ncol=3)
    xlabel("Time (s)"); ylabel("Burst per second"); grid(True)
    plt.ylim(ymin=0)

def time_ph(d, i=0, num_ph=1e4, ph_istart=0):
    """Plot 'num_ph' ph starting at 'ph_istart' marking burst start/end.
    TODO: Update to use the new matplotlib eventplot.
    """
    b = d.mburst[i]
    SLICE = slice(ph_istart, ph_istart+num_ph)
    ph_d = d.ph_times_m[i][SLICE][~d.A_em[i][SLICE]]
    ph_a = d.ph_times_m[i][SLICE][d.A_em[i][SLICE]]

    BSLICE = (bl.b_end(b) < ph_a[-1])
    start, end = bl.b_start(b[BSLICE]), bl.b_end(b[BSLICE])

    u = d.clk_p # time scale
    plt.vlines(ph_d*u, 0, 1, color='k', alpha=0.02)
    plt.vlines(ph_a*u, 0, 1, color='k', alpha=0.02)
    plt.vlines(start*u, -0.5, 1.5, lw=3, color='g', alpha=0.5)
    plt.vlines(end*u, -0.5, 1.5, lw=3, color='r', alpha=0.5)
    xlabel("Time (s)")


##
#  Histogram plots
#

def _get_fit_E_text(d, pylab=True):
    """Return a formatted string for fitted E."""
    delta = (d.E_fit.max()-d.E_fit.min())*100
    fit_text = r'\langle{E}_{fit}\rangle = %.3f \qquad ' % d.E_fit.mean()
    fit_text += r'\Delta E_{fit} = %.2f \%%' % delta
    if pylab: fit_text = r'$'+fit_text+r'$'
    return fit_text

def _fitted_E_plot(d, i=0, F=1, no_E=False, ax=None, show_model=True,
                   verbose=False, two_gauss_model=False, lw=2.5, color='k',
                   alpha=0.5, fillcolor=None):
    """Plot a fitted model overlay on a FRET histogram."""
    if ax is None:
        ax2 = gca()
    else:
        ax2 = plt.twinx(ax=ax)
        ax2.grid(False)

    if d.fit_E_curve and show_model:
        x = r_[-0.2:1.21:0.002]
        y = d.fit_E_model(x, d.fit_E_res[i, :])
        scale = F*d.fit_E_model_F[i]
        if two_gauss_model:
            assert d.fit_E_res.shape[1] > 2
            if d.fit_E_res.shape[1] == 5:
                m1, s1, m2, s2, a1 =  d.fit_E_res[i, :]
                a2 = (1-a1)
            elif d.fit_E_res.shape[1] == 6:
                m1, s1, a1, m2, s2, a2 =  d.fit_E_res[i, :]
            y1 = a1*normpdf(x, m1, s1)
            y2 = a2*normpdf(x, m2, s2)
            ax2.plot(x, scale*y1, ls='--', lw=lw, alpha=alpha, color=color)
            ax2.plot(x, scale*y2, ls='--', lw=lw, alpha=alpha, color=color)
        if fillcolor == None:
            ax2.plot(x, scale*y, lw=lw, alpha=alpha, color=color)
        else:
            ax2.fill_between(x, scale*y, lw=lw, alpha=alpha, edgecolor=color,
                             facecolor=fillcolor, zorder=10)
        if verbose:
            print 'Fit Integral:', np.trapz(scale*y, x)

    ax2.axvline(d.E_fit[i], lw=3, color='r', ls='--', alpha=0.6)
    xtext = 0.6 if d.E_fit[i] < 0.6 else 0.2
    if d.nch > 1 and not no_E:
        ax2.text(xtext, 0.81,"CH%d: $E_{fit} = %.3f$" % \
                (i+1, d.E_fit[i]),
                transform = gca().transAxes, fontsize=16,
                bbox=dict(boxstyle='round', facecolor='#dedede', alpha=0.5))


def hist_width(d, i=0, bins=r_[0:10:0.025], yscale='log', density=True,
               **kwargs):
    b = d.mburst[i]
    histog, bins = np.histogram(bl.b_width(b)*d.clk_p*1e3, bins=bins,
                                density=density)
    #bins *= d.clk_p  # (ms)
    bins = bins[:-1]#+(bins[1]-bins[0])/2.
    plot_style = dict(color='red', lw=2)
    plot_style.update(**kwargs)
    plot(bins, histog, **plot_style)
    gca().set_yscale(yscale)
    #fill_between(bins,0,histog,color='red', alpha=0.5)
    xlabel('Burst width (ms)'); ylabel('# Burst')
    plt.xlim(xmin=0); plt.ylim(ymin=0)

def hist_size(d, i=0, vmax=600, binw=4, bins=None,
              which='all', gamma=1, add_naa=False,
              yscale='log', legend=True, plot_style={}):
    """Plot histogram of burst sizes.

    Parameters:
        d (Data): Data object
        i (int): channel index
        vmax (int/float): histogram max
        binw (int/float): histogram bin width
        bins (array or None): array of bin edges. If not NOne overrides `binw`
        which (string): which counts to consider. 'all' all-photon size
            computed with `d.burst_sizes()`; 'nd', 'na', 'naa' get counts from
            `d.nd`, `d.na`, `d.naa` (respectively Dex-Dem, Dex-Aem, Aex-Aem).
        yscale (string): 'log' or 'linear', sets the plot y scale.
        legend (bool): if True add legend to plot
        plot_style (dict): dict of matplotlib line style passed to `plot`.
    """
    valid_which = ["all", "nd", "na", "naa"]
    assert which in valid_which
    if which == 'all':
        size = d.burst_sizes_ich(ich=i, gamma=gamma, add_naa=add_naa)
        label = 'nd + na'
        if gamma != 1:
            label = "%.2f %s" % (gamma, label)
        if add_naa:
            label += " + naa"
    else:
        size = d[which][i]
        label = which

    colors = ['k', 'g', 'r', 'orange']
    colors_dict = {k: c for k, c in zip(valid_which, colors)}

    if bins is None:
        bins = np.arange(0, vmax+binw, binw)
    counts, bins = np.histogram(size, bins=bins)
    x = bins[:-1] + 0.5*(bins[1] + bins[0])
    plot_style_ = dict(linewidth=2, color=colors_dict[which])
    plot_style_.update(_normalize_kwargs(plot_style, kind='line2d'))
    plot(x, counts, label=label, **plot_style_)

    gca().set_yscale(yscale)
    xlabel('# Ph.'); ylabel('# Bursts')
    if legend: gca().legend(loc='best')

def hist_size_all(d, i=0, **kwargs):
    """Plot burst sizes for all the combinations of photons.

    Calls :func:`hist_size` multiple times with different `which` parameters.
    """
    fields = ['all', 'nd', 'na']
    if d.ALEX:
        fields.append('naa')
    for which in fields:
        hist_size(d, i, which=which, **kwargs)

def hist_burst_data(d, i=0, data_name='E', ax=None, binwidth=0.03, bins=None,
            vertical=False, pdf=False, hist_style='bar',
            weights=None, gamma=1., add_naa=False,            # weights args
            show_fit_stats=False, show_fit_value=False, fit_from='kde',
            show_kde=False, bandwidth=0.03, show_kde_peak=False,  # kde args
            show_model=False, show_model_peaks=True,
            hist_bar_style={}, hist_plot_style={}, model_plot_style={},
            kde_plot_style={}, verbose=False):
    """Plot burst_data histogram and KDE.

    When `bins` is not None it overrides `binwidth`.

    Histograms and KDE can be plotted on any Data variable after burst search.
    To show a model, a model must be fitted first by calling
    d.E_fitter.fit_histogram(). To show the KDE peaks position, they must be
    computed first with d.E_fitter.find_kde_max().
    """
    assert data_name in d
    fitter_name = data_name + '_fitter'

    if ax is None:
        ax = gca()
    pline = ax.axhline if vertical else ax.axvline
    bar = ax.barh if vertical else ax.bar
    xlabel, ylabel = ax.set_xlabel, ax.set_ylabel
    xlim, ylim = ax.set_xlim, ax.set_ylim
    if vertical:
        xlabel, ylabel = ylabel, xlabel
        xlim, ylim = ylim, xlim
    weights_tuple = (weights, float(gamma), add_naa)
    if not hasattr(d, fitter_name) or d.burst_weights != weights_tuple:
        if hasattr(d, fitter_name):
            print ' - Overwriting the old %s object with the new weights.' %\
                    fitter_name
            if verbose:
                print '   Old weights:', d.burst_weights
                print '   New weights:', weights_tuple
        bext.bursts_fitter(d, burst_data=data_name, weights=weights,
                           gamma=gamma, add_naa=add_naa)

    fitter = d[fitter_name]
    fitter.histogram(binwidth=binwidth, bins=bins, verbose=verbose)
    if pdf:
        ylabel('PDF')
        hist_vals = fitter.hist_pdf[i]
    else:
        ylabel('# Bursts')
        hist_vals = fitter.hist_counts[i]
    xlabel(data_name)
    if data_name in ['E', 'S']:
        xlim(-0.19, 1.19)

    hist_bar_style_ = dict(facecolor='#80b3ff', edgecolor='#5f8dd3',
                           linewidth=1.5, alpha=0.7, label='E Histogram')
    hist_bar_style_.update(**_normalize_kwargs(hist_bar_style))

    hist_plot_style_ = dict(linestyle='-', marker='o', markersize=6,
                            linewidth=2, alpha=0.6, label='E Histogram')
    hist_plot_style_.update(**_normalize_kwargs(hist_plot_style,
                                                kind='line2d'))
    if hist_style == 'bar':
        bar(fitter.hist_bins[:-1], hist_vals, fitter.hist_binwidth,
            **hist_bar_style_)
    else:
        if vertical:
            ax.plot(hist_vals, fitter.hist_axis, **hist_plot_style_)
        else:
            ax.plot(fitter.hist_axis, hist_vals, **hist_plot_style_)

    if show_model or show_kde:
        if pdf:
            scale = 1
        else:
            scale = fitter.hist_binwidth * d.num_bursts[i]

    if show_model:
        model_plot_style_ = dict(color='k', alpha=0.8, label='Model')
        model_plot_style_.update(**_normalize_kwargs(model_plot_style,
                                                     kind='line2d'))
        fit_res = fitter.fit_res[i]
        x = fitter.x_axis
        y = scale*fit_res.model.eval(x=x, **fit_res.values)
        xx, yy = (y, x) if vertical else (x, y)
        ax.plot(xx, yy, **model_plot_style_)
        if  fit_res.model.components is not None:
            for component in fit_res.model.components:
                model_plot_style_.update(ls = '--', label='Model component')
                y = scale*component.eval(x=x, **fit_res.values)
                xx, yy = (y, x) if vertical else (x, y)
                ax.plot(xx, yy, **model_plot_style_)
        if show_model_peaks:
            for param in fitter.params:
                if param.endswith('center'):
                    pline(fitter.params[param][i], ls='--', color=red)
    if show_kde:
        x = fitter.x_axis
        fitter.calc_kde(bandwidth=bandwidth)
        kde_plot_style_ = dict(linewidth=1.5, color='k', alpha=0.8,
                               label='KDE')
        kde_plot_style_.update(**_normalize_kwargs(kde_plot_style,
                                                   kind='line2d'))
        y = scale*fitter.kde[i](x)
        xx, yy = (y, x) if vertical else (x, y)
        ax.plot(xx, yy, **kde_plot_style_)
    if show_kde_peak:
        pline(fitter.kde_max_pos[i], ls='--', color='orange')

    if show_fit_value or show_fit_stats:
        if fit_from == 'kde':
            fit_arr = fitter.kde_max_pos
        else:
            assert fit_from in fitter.params
            fit_arr = fitter.params[fit_from]

        if i == 0:
            if show_fit_stats:
                plt.figtext(0.4, 0.01, _get_fit_text_stats(fit_arr),
                            fontsize=16)
        if show_fit_value:
            _plot_fit_text_ch(fit_arr, i, ax=ax)

def hist_fret(d, i=0, ax=None, binwidth=0.03, bins=None, pdf=True,
            hist_style='bar',
            weights=None, gamma=1., add_naa=False,            # weights args
            show_fit_stats=False, show_fit_value=False, fit_from='kde',
            show_kde=False, bandwidth=0.03, show_kde_peak=False,  # kde args
            show_model=False, show_model_peaks=True,
            hist_bar_style={}, hist_plot_style={}, model_plot_style={},
            kde_plot_style={}, verbose=False):
    """Plot FRET histogram and KDE.

    When `bins` is not None it overrides `binwidth`.

    Histograms and KDE can be plotted on any Data variable after burst search.
    To show a model, a model must be fitted first by calling
    d.E_fitter.fit_histogram(). To show the KDE peaks position, they must be
    computed first with d.E_fitter.find_kde_max().
    """
    hist_burst_data(d, i, data_name='E', ax=ax, binwidth=binwidth, bins=bins,
            pdf=pdf, weights=weights, gamma=gamma, add_naa=add_naa,
            hist_style=hist_style, show_fit_stats=show_fit_stats,
            show_fit_value=show_fit_value, fit_from=fit_from,
            show_kde=show_kde, bandwidth=bandwidth,
            show_kde_peak=show_kde_peak,  # kde args
            show_model=show_model, show_model_peaks=show_model_peaks,
            hist_bar_style=hist_bar_style, hist_plot_style=hist_plot_style,
            model_plot_style=model_plot_style, kde_plot_style=kde_plot_style,
            verbose=verbose)

def hist_S(d, i=0, ax=None, binwidth=0.03, bins=None, pdf=True,
           hist_style='bar',
           weights=None, gamma=1., add_naa=False,                # weights args
           show_fit_stats=False, show_fit_value=False, fit_from='kde',
           show_kde=False, bandwidth=0.03, show_kde_peak=False,  # kde args
           show_model=False, show_model_peaks=True,
           hist_bar_style={}, hist_plot_style={}, model_plot_style={},
           kde_plot_style={}, verbose=False):
    """Plot S histogram and KDE.

    When `bins` is not None it overrides `binwidth`.

    Histograms and KDE can be plotted on any Data variable after burst search.
    To show a model, a model must be fitted first by calling
    d.S_fitter.fit_histogram(). To show the KDE peaks position, they must be
    computed first with d.S_fitter.find_kde_max().
    """
    hist_burst_data(d, i, data_name='S', ax=ax, binwidth=binwidth, bins=bins,
            pdf=pdf, weights=weights, gamma=gamma, add_naa=add_naa,
            hist_style=hist_style, show_fit_stats=show_fit_stats,
            show_fit_value=show_fit_value, fit_from=fit_from,
            show_kde=show_kde, bandwidth=bandwidth,
            show_kde_peak=show_kde_peak,  # kde args
            show_model=show_model, show_model_peaks=show_model_peaks,
            hist_bar_style=hist_bar_style, hist_plot_style=hist_plot_style,
            model_plot_style=model_plot_style, kde_plot_style=kde_plot_style,
            verbose=verbose)

def _get_fit_text_stats(fit_arr, pylab=True):
    """Return a formatted string for mean E and max delta-E."""
    delta = (fit_arr.max() - fit_arr.min())*100
    fit_text = r'\langle{E}_{fit}\rangle = %.3f \qquad ' % fit_arr.mean()
    fit_text += r'\Delta E_{fit} = %.2f \%%' % delta
    if pylab: fit_text = r'$'+fit_text+r'$'
    return fit_text

def _plot_fit_text_ch(fit_arr, ich, fmt_str="CH%d: $E_{fit} = %.3f$", ax=None,
            bbox=dict(boxstyle='round', facecolor='#dedede', alpha=0.5),
            xtext_low=0.2, xtext_high=0.6, fontsize=16):
    """Plot a text box with ch and fit value."""
    if ax is None: ax = gca()
    xtext = xtext_high if fit_arr[ich] < xtext_high else xtext_low
    ax.text(xtext, 0.81, fmt_str % (ich+1, fit_arr[ich]),
            transform = ax.transAxes, fontsize=fontsize, bbox=bbox)


def hist2d_alex(d, i=0, vmin=2, vmax=0, bin_step=None, S_max_norm=0.8,
                interp='bicubic', cmap='hot', under_color='white',
                over_color='white', scatter=True, scatter_ms=3,
                scatter_color='orange', scatter_alpha=0.2, gui_sel=False,
                ax=None, cbar_ax=None, grid_color='#D0D0D0'):
    """Plot 2-D E-S ALEX histogram with a scatterplot overlay.
    """
    if ax is None:
        ax = plt.gca()
    if bin_step is not None:
        d.calc_alex_hist(bin_step=bin_step)
    ES_hist, E_bins, S_bins, S_ax = d.ES_hist[i], d.E_bins, d.S_bins, d.S_ax

    colormap = plt.get_cmap(cmap)
    # Heuristic for colormap range
    if vmax <= vmin:
        S_range = (S_ax < S_max_norm)
        vmax = ES_hist[:, S_range].max()
        if vmax <= vmin: vmax = 10*vmin

    if scatter:
        ax.plot(d.E[i],d.S[i], 'o', mew=0, ms=scatter_ms, alpha=scatter_alpha,
                color=scatter_color)
    im = ax.imshow(ES_hist[:, ::-1].T, interpolation=interp,
            extent=(E_bins[0], E_bins[-1], S_bins[0], S_bins[-1]),
            vmin=vmin, vmax=vmax, cmap=colormap)
    im.cmap.set_under(under_color)
    im.cmap.set_over(over_color)
    if cbar_ax is None:
        gcf().colorbar(im)
    else:
        cbar_ax.colorbar(im)
    ax.set_xlim(-0.2, 1.2); ax.set_ylim(-0.2, 1.2)
    ax.set_xlabel('E');     ax.set_ylabel('S')
    ax.grid(color=grid_color)
    if gui_sel:
        # the selection object must be saved (otherwise will be destroyed)
        hist2d_alex.gui_sel = gs.rectSelection(gcf(), gca())


def plot_ES_selection(ax, E1, E2, S1, S2, rect=True, **kwargs):
    """Plot an overlay ROI on top of an E-S plot (i.e. ALEX histogram).

    This function plots a rectangle and inscribed ellipsis with x-axis limits
    (E1, E2) and y-axsis limits (S1, S2).

    Note that, a dict with keys (E1, E2, S1, S2, rect) can be both passed to
    :func:`fretbursts.select_bursts.ES` to apply a selection, and to
    `plot_ES_selection` to plot it.

    Parameters:
        ax (matplotlib axis): the axis where the rectangle is plotted.
            Typically you pass the axis of a previous E-S scatter plot
            or histogram.
        E1, E2, S1, S2 (floats): limits for E and S (X and Y axis respectively)
            used to plot the rectangle.
        rect (bool): if True, the rectangle is highlighted and the ellipsis is
            grey. The color are swapped otherwise.

    Any additional keyword argument specifies the matplotlib patch style
    for both the rectangle and the ellipsis.
    """
    if rect:
        rect_color, ellips_color = 'blue', 'gray'
    else:
        rect_color, ellips_color = 'gray', 'blue'
    patch_style = dict(fill=False, lw=1.5, alpha=0.5)
    patch_style.update(**kwargs)
    rect = Rectangle(xy=(E1, S1), height=(S2 - S1), width=(E2 - E1),
                     color=rect_color, **patch_style)
    ellips = Ellipse(xy=(0.5*(E1 +  E2), 0.5*(S1 + S2)), height=(S2 - S1),
                     width=(E2 - E1), color=ellips_color, **patch_style)
    ax.add_patch(rect)
    ax.add_patch(ellips)
    return rect, ellips

def get_ES_range():
    """Get the range of ES histogram selected via GUI.

    Prints E1, E2, S1, S2 and return a dict containig these values.
    """
    sel = None
    if hasattr(hist2d_alex.gui_sel, 'selection'):
        sel = hist2d_alex.gui_sel.selection
        print 'E1={E1:.3}, E2={E2:.3}, S1={S1:.3}, S2={S2:.3}'.format(**sel)
    return sel

def hist_sbr(d, ich=0, **hist_kwargs):
    """Histogram of per-burst Signal-to-Background Ratio (SBR).
    """
    if not 'sbr' in d:
        d.calc_sbr()
    style_kwargs = dict(bins=np.r_[0:20:0.5])  # default style
    style_kwargs.update(**hist_kwargs)
    hist(d.sbr[ich], **style_kwargs)
    xlabel('SBR'); ylabel('# Bursts')


def hist_bg_single(d, i=0, period=0, binwidth=1e-4, bins=None, tmax=0.01,
                   ph_sel=Ph_sel('all'), show_fit=True, yscale='log',
                   manual_rate=None, manual_tau_th=500,
                   xscale='linear', plot_style={}, fit_style={}):
    """Plot histogram of photon interval for a single photon streams.

    Optionally plots the fitted background.
    """

    # If `bins` is not passed or is a scalar create the `bins` array
    if bins is None:
        bins = np.arange(0, tmax + binwidth, binwidth)
    elif np.size(bins) == 1:
        warnings.warn('`bins` is a scalar, `tmax` will be ignored.')
        bins = np.arange(0, bins*binwidth, binwidth)
    t_ax = bins[:-1] + 0.5*binwidth

    # Compute histograms
    ph_times_period = d.get_ph_times_period(ich=i, period=period,
                                            ph_sel=ph_sel)
    delta_ph_t_period = np.diff(ph_times_period)*d.clk_p
    counts, _ = np.histogram(delta_ph_t_period, bins=bins)

    # Max index with counts > 0
    n_trim = np.trim_zeros(counts).size + 1

    # Plot histograms
    plot_style_ = dict(marker='o', markersize=5, linestyle='none', alpha=0.6)
    if ph_sel in _ph_sel_color_dict:
        plot_style_['color'] = _ph_sel_color_dict[ph_sel]
        plot_style_['label'] = _ph_sel_label_dict[ph_sel]
    plot_style_.update(_normalize_kwargs(plot_style, kind='line2d'))
    plot(t_ax[:n_trim]*1e3, counts[:n_trim], **plot_style_)

    if show_fit or manual_rate is not None:
        # Compute the fit function
        if manual_rate is not None:
            bg_rate = manual_rate
            tau_th = manual_tau_th*1e-6
        else:
            bg_rate = d.bg_from(ph_sel)[i][period]
            tau_th = d.bg_th_us[ph_sel][i]*1e-6

        i_tau_th = np.searchsorted(t_ax, tau_th)
        counts_integral = counts[i_tau_th:].sum()
        y_fit = np.exp(- t_ax * bg_rate)
        y_fit *= counts_integral/y_fit[i_tau_th:].sum()

        # Plot
        fit_style_ = dict(plot_style_)
        fit_style_.update(linestyle='-', marker='', label='auto')
        fit_style_.update(_normalize_kwargs(fit_style, kind='line2d'))
        if fit_style_['label'] is 'auto':
            fit_style_['label'] = '%s, %.2f kcps' % (plot_style_['label'],
                                                     bg_rate*1e-3)
        plot(t_ax[:n_trim]*1e3,  y_fit[:n_trim], **fit_style_)

    if yscale == 'log':
        gca().set_yscale(yscale)
        plt.ylim(1)
        _plot_status['hist_bg_single'] = {'autoscale': False}
    if xscale == 'log':
        gca().set_xscale(yscale)
        plt.xlim(0.5*binwidth)
        _plot_status['hist_bg_single'] = {'autoscale': False}

    xlabel(u'Timestamp waiting time (ms)'); ylabel("# Waiting times")


def hist_bg(d, i=0, period=0, binwidth=1e-4, bins=None, tmax=0.01,
            show_da=False, show_fit=True, yscale='log', xscale='linear',
            plot_style={}, fit_style={}, legend=True):
    """Plot histogram of photon interval for different photon streams.

    Optionally plots the fitted background.
    """
    # Plot multiple timetraces
    ph_sel_list = [Ph_sel('all'), Ph_sel(Dex='Dem'), Ph_sel(Dex='Aem')]
    if d.ALEX:
         ph_sel_list.append(Ph_sel(Aex='Aem'))
         if show_da:
             ph_sel_list.append(Ph_sel(Aex='Dem'))

    for ix, ph_sel in enumerate(ph_sel_list):
        if not bl.mask_empty(d.get_ph_mask(i, ph_sel=ph_sel)):
            hist_bg_single(d, i=i, period=period, binwidth=binwidth,
                           bins=bins, tmax=tmax, ph_sel=ph_sel,
                           show_fit=show_fit, yscale=yscale, xscale=xscale,
                           plot_style=plot_style, fit_style=fit_style)
    if legend:
        plt.legend(loc='best', fancybox=True)

    if yscale == 'log' or xscale == 'log':
        _plot_status['hist_bg'] = {'autoscale': False}

def hist_multiphdelays(d, i=0, m=10, binwidth=1e-3, dt_max=10e-3, bins=None,
                       bursts=True, plot_style={}):
    counts, x = bext.histogram_mdelays(d, ich=i, m=m, binwidth=binwidth,
                                          dt_max=dt_max, bins=bins,
                                          bursts=bursts)
    plot(x, counts)

def hist_ph_delays(d, i=0, time_min_s=0, time_max_s=30, bin_width_us=10,
        mask=None, yscale='log', hfit_bin_ms=1, efit_tail_min_us=1000,
        **kwargs):
    """Histog. of ph delays and comparison with 3 BG fitting functions.
    """
    ph = d.ph_times_m[i].copy()
    if mask is not None: ph = ph[mask[i]]
    ph = ph[(ph < time_max_s/d.clk_p)*(ph > time_min_s/d.clk_p)]
    dph = np.diff(ph)*d.clk_p
    H = hist(dph*1e6, bins=r_[0:1200:bin_width_us], histtype='step', **kwargs)
    gca().set_yscale('log')
    xlabel(u'Ph delay time (μs)'); ylabel("# Ph")

    efun = lambda t, r: np.exp(-r*t)*r
    re = bg.exp_fit(ph, tail_min_us=efit_tail_min_us)
    rg = bg.exp_hist_fit(ph, tail_min_us=efit_tail_min_us, binw=hfit_bin_ms*1e3)
    rc = bg.exp_cdf_fit(ph, tail_min_us=efit_tail_min_us)
    t = r_[0:1200]*1e-6
    F = 1 if 'normed' in kwargs else H[0].sum()*(bin_width_us)
    plot(t*1e6, 0.65*F*efun(t,rc)*1e-6, lw=3, alpha=0.5, color='m',
            label="%d cps - Exp CDF (tail_min_p=%.2f)" % (rc, efit_tail_min_us))
    plot(t*1e6, 0.65*F*efun(t,re)*1e-6, lw=3, alpha=0.5, color='r',
            label="%d cps - Exp ML (tail_min_p=%.2f)" % (re, efit_tail_min_us))
    plot(t*1e6, 0.68*F*efun(t,rg)*1e-6, lw=3, alpha=0.5, color='g',
            label=u"%d cps - Hist (bin_ms=%d) [Δ=%d%%]" % (hfit_bin_ms, rg,
                                                           100*(rg-re)/re))
    plt.legend(loc='best', fancybox=True)

def hist_mdelays(d, i=0, m=10, bins_s=(0, 10, 0.02), bp=0, no_bg_fit=True,
                 hold=False, bg_ppf=0.01, ph_sel=Ph_sel('all'), spline=True,
                 s=1., bg_fit=True, bg_F=0.8):
    """Histogram of m-ph delays (all ph vs in-burst ph)."""
    ax = gca()
    if not hold:
        #ax.clear()
        for _ind in range(len(ax.lines)): ax.lines.pop()

    results = bext.calc_mdelays_hist(
                        d=d, ich=i, m=m, period=bp, bins_s=bins_s,
                        ph_sel=ph_sel, bursts=True, bg_fit=bg_fit, bg_F=bg_F)
    bin_x, histog_y = results[:2]
    bg_dist = results[2]
    rate_ch_kcps = 1./bg_dist.kwds['scale']  # extract the rate
    if bg_fit:
        a, rate_kcps = results[3:5]

    mdelays_hist_y = histog_y[0]
    mdelays_b_hist_y = histog_y[1]

    # Center of mass (COM)
    binw = bins_s[2]
    com = np.sum(bin_x*mdelays_hist_y)*binw
    com_b = np.sum(bin_x*mdelays_b_hist_y)*binw
    #print com, com_b

    # Compute a spline smoothing of the PDF
    mdelays_spline = UnivariateSpline(bin_x, mdelays_hist_y, s=s*com)
    mdelays_b_spline = UnivariateSpline(bin_x, mdelays_b_hist_y, s=s*com_b)
    mdelays_spline_y = mdelays_spline(bin_x)
    mdelays_b_spline_y = mdelays_b_spline(bin_x)
    if spline:
        mdelays_pdf_y = mdelays_spline_y
        mdelays_b_pdf_y = mdelays_b_spline_y
    else:
        mdelays_pdf_y = mdelays_hist_y
        mdelays_b_pdf_y = mdelays_b_hist_y

    # Thresholds and integrals
    max_delay_th_P = bg_dist.ppf(bg_ppf)
    max_delay_th_F = m/rate_ch_kcps/d.F

    burst_domain = bin_x < max_delay_th_F
    burst_integral = np.trapz(x=bin_x[burst_domain],
                              y=mdelays_hist_y[burst_domain])

    title("I = %.1f %%" % (burst_integral*100), fontsize='small')
    #text(0.8,0.8,"I = %.1f %%" % (integr*100), transform = gca().transAxes)

    ## MDelays plot
    plot(bin_x, mdelays_pdf_y, lw=2, color='b', alpha=0.5,
         label="Delays dist.")
    plot(bin_x, mdelays_b_pdf_y, lw=2, color='r', alpha=0.5,
         label="Delays dist. (in burst)")
    plt.axvline(max_delay_th_P, color='k',
                label="BG ML dist. @ %.1f%%" % (bg_ppf*100))
    plt.axvline(max_delay_th_F, color='m',
                label="BS threshold (F=%d)" % d.F)

    ## Bg distribution plots
    bg_dist_y = bg_dist.pdf(bin_x)
    ibin_x_bg_mean = np.abs(bin_x - bg_dist.mean()).argmin()
    bg_dist_y *= mdelays_pdf_y[ibin_x_bg_mean]/bg_dist_y[ibin_x_bg_mean]
    plot(bin_x, bg_dist_y, '--k', alpha=1.,
         label='BG ML dist.')
    plt.axvline(bg_dist.mean(), color='k', ls='--', label="BG mean")
    if bg_fit:
        bg_y = a*erlang.pdf(bin_x, a=m, scale=1./rate_kcps)
        plot(bin_x, bg_y, '--k', alpha=1.)
    plt.legend(ncol=2, frameon=False)
    xlabel("Time (ms)")

def hist_mrates(d, i=0, m=10, bins=r_[0:20e3:20], yscale='log', normed=True,
        dense=True):
    """Histogram of m-photons rates."""
    ph = d.ph_times_m[i]
    if dense:
        ph_mrates = 1.*m/((ph[m-1:]-ph[:ph.size-m+1])*d.clk_p*1e3)
    else:
        ph_mrates = 1.*m/(np.diff(ph[::m])*d.clk_p*1e3)
    #gauss = lambda M,std: gaussian(M,std)/gaussian(M,std).sum()
    H = np.histogram(ph_mrates, bins=bins, normed=normed)
    epdf_x = H[1][:-1]
    epdf_y = H[0]
    plot(epdf_x, epdf_y, '.-')
    #plot(epdf_x, convolve(epdf_y, gauss(30,4),'same'), lw=2)
    gca().set_yscale(yscale)
    xlabel("Rates (kcps)")

## Bursts stats
def hist_rate_in_burst(d, i=0, bins=20):
    """Histogram of total photon rate in each burst."""
    b = d.mburst[i]
    rate = 1e-3*d.nt[i]/(bl.b_width(b)*d.clk_p)
    hist(rate, bins=bins, color="blue")
    xlabel('In-burst ph. rate (kcps)'); ylabel('# Bursts')
    #xlim(xmin=d.L/2); ylim(ymin=0)

def hist_burst_delays(d, i=0, tmax_seconds=0.5, bins=100, **kwargs):
    """Histogram of waiting times between bursts."""
    b = d.mburst[i]
    bd = clk_to_s(np.sort(np.diff(b[:,0].astype(float))))[:-20]
    hist(bd[bd<tmax_seconds], bins=bins, **kwargs)
    xlabel('Delays between bursts (s)'); ylabel('# bursts')

## Burst internal "symmetry"
def hist_asymmetry(d, i=0, bin_max=2, binwidth=0.1, stat_func=np.median):
    burst_asym = bext.asymmetry(d, ich=i, func=stat_func)
    bins_pos = np.arange(0, bin_max+binwidth, binwidth)
    bins = np.hstack([-bins_pos[1:][::-1], bins_pos])
    izero = (bins.size - 1)/2.
    assert izero == np.where(np.abs(bins) < 1e-8)[0]

    counts, _ = np.histogram(burst_asym, bins=bins)
    asym_counts_neg = counts[:izero] - counts[izero:][::-1]
    asym_counts_pos = counts[izero:] - counts[:izero][::-1]
    asym_counts = np.hstack([asym_counts_neg, asym_counts_pos])

    plt.bar(bins[:-1], width=binwidth, height=counts, fc='b', alpha=0.5)
    plt.bar(bins[:-1], width=binwidth, height=asym_counts, fc='r', alpha=0.5)
    plt.grid(True)
    plt.xlabel('Time (ms)')
    plt.ylabel('# Bursts')
    plt.legend(['{func}$(t_D)$ - {func}$(t_A)$'.format(func=stat_func.__name__),
                'positive half - negative half'],
                frameon=False, loc='best')
    skew_abs = asym_counts_neg.sum()
    skew_rel = 100.*skew_abs/counts.sum()
    print 'Skew: %d bursts, (%.1f %%)' % (skew_abs, skew_rel)

##
#  Scatter plots
#

def scatter_width_size(d, i=0):
    """Scatterplot of burst width versus size."""
    b = d.mburst[i]
    plot(bl.b_width(b)*d.clk_p*1e3, d.nt[i], 'o', mew=0, ms=3, alpha=0.7,
         color='blue')
    t_ms = arange(0,50)
    plot(t_ms,((d.m)/(d.T[i]))*t_ms*1e-3,'--', lw=2, color='k',
            label='Slope = m/T = min. rate = %1.0f cps' % (d.m/d.T[i]))
    plot(t_ms,d.rate_m[i]*t_ms*1e-3,'--', lw=2, color='r',
            label='Noise rate: BG*t')
    xlabel('Burst width (ms)'); ylabel('Burst size (# ph.)')
    plt.xlim(0,10); plt.ylim(0,300)
    legend(frameon=False)

def scatter_rate_da(d, i=0):
    """Scatter of nd rate vs na rate (rates for each burst)."""
    b = d.mburst[i]
    Rate = lambda nX: nX[i]/bl.b_width(b)/d.clk_p*1e-3
    plot(Rate(d.nd), Rate(d.na), 'o', mew=0, ms=3, alpha=0.1, color='blue')
    xlabel('D burst rate (kcps)'); ylabel('A burst rate (kcps)')
    plt.xlim(-20,100); plt.ylim(-20,100)
    legend(frameon=False)

def scatter_fret_size(d, i=0, which='all', gamma=1, add_naa=False,
                      plot_style={}):
    """Scatterplot of FRET efficiency versus burst size.
    """
    if which == 'all':
        size = d.burst_sizes_ich(ich=i, gamma=gamma, add_naa=add_naa)
    else:
        assert which in d
        size = d[which][i]

    plot_style_ = dict(linestyle='', alpha=0.1, color='b',
                       marker='o', markeredgewidth=0, markersize=3)
    plot_style_.update(_normalize_kwargs(plot_style, kind='line2d'))
    plot(d.E[i], size, **plot_style_)
    xlabel("FRET Efficiency (E)")
    ylabel("Corrected Burst size (#ph)")

def scatter_fret_nd_na(d, i=0, show_fit=False, no_text=False, gamma=1.,
                       **kwargs):
    """Scatterplot of FRET versus gamma-corrected burst size."""
    default_kwargs = dict(mew=0, ms=3, alpha=0.3, color="blue")
    default_kwargs.update(**kwargs)
    plot(d.E[i], gamma*d.nd[i]+d.na[i], 'o', **default_kwargs)
    xlabel("FRET Efficiency (E)")
    ylabel("Burst size (#ph)")
    if show_fit:
        _fitted_E_plot(d, i, F=1., no_E=no_text, ax=gca())
        if i==0 and not no_text:
            plt.figtext(0.4,0.01, _get_fit_E_text(d),fontsize=14)

def scatter_fret_width(d, i=0):
    """Scatterplot of FRET versus burst width."""
    b = d.mburst[i]
    plot(d.E[i],(b[:,1]*d.clk_p)*1e3, 'o', mew=0, ms=3, alpha=0.1,
         color="blue")
    xlabel("FRET Efficiency (E)")
    ylabel("Burst width (ms)")

def scatter_da(d, i=0, alpha=0.3):
    """Scatterplot of donor vs acceptor photons (nd, vs na) in each burst."""
    plot(d.nd[i], d.na[i],'o', mew=0,ms=3, alpha=alpha, color='blue')
    xlabel('# donor ph.'); ylabel('# acceptor ph.')
    plt.xlim(-5,200); plt.ylim(-5,120)

def scatter_naa_nt(d, i=0, alpha=0.5):
    """Scatterplot of nt versus naa."""
    plot(d.nt[i], d.naa[i],'o', mew=0,ms=3, alpha=alpha, color='blue')
    plot(arange(200), color='k', lw=2)
    xlabel('Total burst size (nd+na+naa)'); ylabel('Accept em-ex BS (naa)')
    plt.xlim(-5,200); plt.ylim(-5,120)

def scatter_alex(d, i=0, **kwargs):
    """Scatterplot of E vs S. Keyword arguments passed to `plot`."""
    plot_style = dict(mew=1, ms=4, mec='black', color='purple',
                      alpha=0.1)
    plot_style = _normalize_kwargs(plot_style, 'line2d')
    plot_style.update(**_normalize_kwargs(kwargs))
    plot(d.E[i], d.S[i], 'o', **plot_style)
    xlabel("E"); ylabel('S')
    plt.xlim(-0.2,1.2); plt.ylim(-0.2,1.2)


## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#  High-level plot wrappers
## - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def dplot_48ch(d, func, sharex=True, sharey=True,
        pgrid=True, figsize=None, AX=None, nosuptitle=False,
        scale=True, ich=None, **kwargs):
    """Plot wrapper for 48-spot measurements. Use `dplot` instead."""
    global gui_status
    if ich is None:
        iter_ch = xrange(d.nch)
        if d.nch == 48:
            top_adjust = 0.95
            ax_ny, ax_nx = 6, 8
            if figsize is None:
                figsize = (20, 16)
        elif d.nch == 8:
            top_adjust = 0.93
            ax_ny, ax_nx = 4, 2
            if figsize is None:
                figsize = (12, 9)
    else:
        top_adjust = 0.9
        iter_ch = [ich]
        ax_ny, ax_nx = 1, 1
        if figsize is None:
            figsize = (8, 5)

    if AX is None:
        fig, AX = plt.subplots(ax_ny, ax_nx, figsize=figsize, sharex=sharex,
                               sharey=sharey, squeeze=False)
        fig.subplots_adjust(left=0.08, right=0.96, top=top_adjust,
                            bottom=0.07, wspace=0.05)
        old_ax = False
    else:
        fig = AX[0,0].figure
        old_ax = True

    for i, ich in enumerate(iter_ch):
        b = d.mburst[ich] if 'mburst' in d else None
        ax = AX.ravel()[i]
        if i == 0 and not nosuptitle:
            fig.suptitle(d.status())
        s = u'[%d]' % (ich+1)
        if 'rate_m' in d: s += (' BG=%.1fk' % (d.rate_m[ich]*1e-3))
        if b is not None: s += (', #bu=%d' %  b.shape[0])
        ax.set_title(s, fontsize=12)
        ax.grid(pgrid)
        plt.sca(ax)
        gui_status['first_plot_in_figure'] = (i == 0)
        func(d, ich, **kwargs)
    [a.set_xlabel('') for a in AX[:-1,:].ravel()]
    [a.set_ylabel('') for a in AX[:,1:].ravel()]
    if sharex:
        plt.setp([a.get_xticklabels() for a in AX[:-1,:].ravel()], visible=False)
        [a.set_xlabel('') for a in AX[:-1,:].ravel()]
        if not old_ax: fig.subplots_adjust(hspace=0.15)
    if sharey:
        if AX.shape[1] > 1:
             plt.setp([a.get_yticklabels() for a in AX[:, 1]], visible=False)
        fig.subplots_adjust(wspace=0.08)

        func_allows_autoscale = True
        if func.__name__ in _plot_status:
            func_allows_autoscale = _plot_status[func.__name__]['autoscale']
        if scale and func_allows_autoscale:
            ax.autoscale(enable=True, axis='y')
    return AX

def dplot_8ch(d, func, sharex=True, sharey=True,
        pgrid=True, figsize=(12, 9), nosuptitle=False, AX=None,
        scale=True, **kwargs):
    """Plot wrapper for 8-spot measurements. Use `dplot` instead."""
    global gui_status
    if AX is None:
        fig, AX = plt.subplots(4,2,figsize=figsize, sharex=sharex,
                               sharey=sharey)
        fig.subplots_adjust(left=0.08, right=0.96, top=0.93, bottom=0.07,
                wspace=0.05)
        old_ax = False
    else:
        fig = AX[0,0].figure
        old_ax = True
    for i in xrange(d.nch):
        b = d.mburst[i] if 'mburst' in d else None
        if (func not in [timetrace, ratetrace, timetrace_single,
                         ratetrace_single, hist_bg_single, hist_bg,
                         timetrace_bg]) and np.size(b) == 0:
            continue
        ax = AX.ravel()[i]
        if i == 0 and not nosuptitle:
            fig.suptitle(d.status())
        s = u'[%d]' % (i+1)
        if 'rate_m' in d: s += (' BG=%.1fk' % (d.rate_m[i]*1e-3))
        if 'T' in d: s += (u', T=%dμs' % (d.T[i]*1e6))
        if b is not None: s += (', #bu=%d' %  b.shape[0])
        ax.set_title(s, fontsize=12)
        ax.grid(pgrid)
        plt.sca(ax)
        gui_status['first_plot_in_figure'] = (i == 0)
        func(d, i, **kwargs)
        if i % 2 == 1: ax.yaxis.tick_right()
    [a.set_xlabel('') for a in AX[:-1,:].ravel()]
    [a.set_ylabel('') for a in AX[:,1:].ravel()]
    if sharex:
        plt.setp([a.get_xticklabels() for a in AX[:-1,:].ravel()], visible=False)
        [a.set_xlabel('') for a in AX[:-1,:].ravel()]
        if not old_ax: fig.subplots_adjust(hspace=0.15)
    if sharey:
        plt.setp([a.get_yticklabels() for a in AX[:,1]], visible=False)
        fig.subplots_adjust(wspace=0.08)

        func_allows_autoscale = True
        if func.__name__ in _plot_status:
            func_allows_autoscale = _plot_status[func.__name__]['autoscale']
        if scale and func_allows_autoscale:
            ax.autoscale(enable=True, axis='y')
    return AX

def dplot_1ch(d, func, pgrid=True, ax=None,
              figsize=(9, 4.5), fignum=None, nosuptitle=False, **kwargs):
    """Plot wrapper for single-spot measurements. Use `dplot` instead."""
    global gui_status
    if ax is None:
        fig = plt.figure(num=fignum, figsize=figsize)
        ax = fig.add_subplot(111)
    else:
        fig = ax.figure
    s = d.name()
    if 'rate_m' in d: s += (' BG=%.1fk' % (d.rate_m[0]*1e-3))
    if 'T' in d: s += (u', T=%dμs' % (d.T[0]*1e6))
    if 'mburst' in d: s += (', #bu=%d' %  d.num_bursts[0])
    if not nosuptitle: ax.set_title(s, fontsize=12)
    ax.grid(pgrid)
    plt.sca(ax)
    gui_status['first_plot_in_figure'] = True
    func(d, **kwargs)
    return ax

def dplot(d, func, **kwargs):
    """Main plot wrapper for single and multi-spot measurements."""
    if d.nch == 1:
        return dplot_1ch(d=d, func=func, **kwargs)
    elif d.nch == 8:
        return dplot_8ch(d=d, func=func, **kwargs)
    elif d.nch == 48:
        return dplot_48ch(d=d, func=func, **kwargs)

