.. _fit-section:

Fit framework
=============

This page contains only a general description of FRETBursts fitting
functionalities. The content of this page is:

.. contents::

For the reference documentation for fitting multi-channel histograms see:

.. toctree::
    :maxdepth: 3

    mfit

For some legacy modules used for gaussian and exponential fitting see:

.. toctree::
    :maxdepth: 3

    gaussian_fitting
    exp_fitting


Overview
--------

FRETBursts uses of the powerful `lmfit <http://lmfit.github.io/lmfit-py/>`_
library for most fittings (like E or S histogram fitting).
Lmfit is installed when running the *FRETBursts Installation* notebook
(see :doc:`installation`).

FRETBursts requires `lmfit` version 0.8rc3 or higher.

Fitting E or S histograms
-------------------------

The module :mod:`fretbursts.mfit` provides a class
:class:`fretbursts.mfit.MultiFitter`
that allow to build histograms and KDE on a multi-channel sample population
(typically E or S values for each burst). The MultiFitter class can find
the max peak position of a KDE or fit the histogram with an arbitrary model.
A set of predefined models is provided to handle common cases.
While sensible defaults are applied the user can control
every detail of the fit by setting initial values, parameter bounds
(min, max), algebraic constrains and so on. New models can be created by
composing simpler models (by using `+` operator). See the lmfit documentation
for more info on how to define
`models <http://lmfit.github.io/lmfit-py/model.html>`_
and `composite models <http://lmfit.github.io/lmfit-py/model.html#creating-composite-models>`_.

A convenience function :func:`fretbursts.burstlib_ext.burst_fitter` can be
used to create a `MultiFitter` object to fit either E or S. As an example
let suppose having a measurement loaded in the variable `d`. To create a
fitter object and compute the FRET histogram we execute::

    bext.burst_fitter(d) # Creates d.E_fitter
    d.E_fitter.histogram() # Compute the histogram for all the channels

Now we fit the E histogram with a 2-Gaussians model::

    d.E_fitter.fit_histogram(mfit.factory_two_gaussians)

And plot the histogram and the fitted model::

    dplot(d, hist_fret, show_model=True)

More detailed example can be found in the
`tutorials <https://github.com/tritemio/FRETBursts_notebooks>`_
in notebooks on
`us-ALEX analysis <http://nbviewer.ipython.org/github/tritemio/FRETBursts_notebooks/blob/master/notebooks/FRETBursts%20-%20us-ALEX%20smFRET%20burst%20analysis.ipynb>`_.

Lmfit introduction
------------------
Lmfit provides a simple and flexible interface for non-linear least squares
and other minimization methods. All the model parameters can be fixed/varied,
have bounds (min, max) or constrained to an algebraic expression.

Moreover lmfit provides a Model class and a set of built-in models
that allows to express curve-fitting problems in an compact and expressive
form. Basic models (such as a Gaussian peak) and be composed allowing
an easy definitions of a variety of models (2 or 3 Gaussians).

For more information refer to the official
`lmfit documentation <http://lmfit.github.io/lmfit-py/>`_.



Legacy Fit functions
====================

These are legacy functions used in versions of FRETBursts < 0.4.
This function are retained for backward compatibility.

A set of generic fit function is provided in `fretbursts/fit`.
These are low-level (i.e. generic) fit functions to fit gaussian or
exponential models.

.. toctree::
    :maxdepth: 3

    gaussian_fitting
    exp_fitting

