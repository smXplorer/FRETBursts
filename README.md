FRETBursts
==========

[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.12784.png)](http://dx.doi.org/10.5281/zenodo.12784)
[![Build Status](https://travis-ci.org/tritemio/FRETBursts.svg?branch=master)](https://travis-ci.org/tritemio/FRETBursts)

> *Quick links: [Reference documentation](http://fretbursts.readthedocs.org/en/latest/index.html), [FRETBursts tutorials](https://github.com/tritemio/FRETBursts_notebooks)*

Project description
-------------------

<div style="float: right; margin-left: 30px;">
<img title="FRETBurst generated ALEX histogram"style="float: right; margin-left: 30px;" src="http://i.imgur.com/My7rWc2.png" align=right height = 340 />
</div>

**[FRETBursts](https://github.com/tritemio/FRETBursts)** is a
software toolkit for burst analysis of confocal
[single-molecule FRET](http://en.wikipedia.org/wiki/Single-molecule_FRET)
(smFRET) measurements.

FRETBursts is an effort to bring
[reproducible computing](http://dx.doi.org/10.1371/journal.pcbi.1003285)
to the field of single-molecule confocal microscopy. It provides
a standard implementation of state-of-the-art algorithms
for confocal smFRET analysis.
FRETBursts is opensource and contributions are welcome.
The authors are committed to promptly fix bugs whenever discovered.

Together with FRETBursts we promote the open file format
[HDF5-Ph-Data](https://github.com/tritemio/FRETBursts/wiki/HDF5-Ph-Data-format-0.2-Draft).

Issues can be reported and discussed on the
[issue tracker](https://github.com/tritemio/FRETBursts/issues?state=open).
Fixes or enhancements can be sent with a [github pull request](https://help.github.com/articles/creating-a-pull-request).
Small corrections can be made directly online
by clicking on the GitHub edit button of a specific file.

FRETBursts allows to analyze both [single-spot](http://dx.doi.org/10.1126/science.283.5408.1676)
and [multi-spot smFRET](http://dx.doi.org/10.1117/12.2003704) data.
Alternating laser excitation ([ALEX](http://dx.doi.org/10.1529/biophysj.104.054114))
scheme is supported.

Main analysis features includes:

- background estimation as a function of time (for example in 30s windows)
- sliding-window burst search with adaptive (background-dependent) rate-threshold. No timetrace binning required.
- burst corrections: background, D-spectral leakage (bleed-through), A-direct excitation,
gamma-factor
- per-burst statistics (# photons, burst duration, E, S, peak rate in burst, etc...)
- post-burst-search [selection functions](http://fretbursts.readthedocs.org/en/latest/burst_selection.html)
  (for ex.: [burst size](http://fretbursts.readthedocs.org/en/latest/burst_selection.html#fretbursts.select_bursts.size),
  [burst width](http://fretbursts.readthedocs.org/en/latest/burst_selection.html#fretbursts.select_bursts.width),
  [E, S](http://fretbursts.readthedocs.org/en/latest/burst_selection.html#fretbursts.select_bursts.ES), ...).
  Defining a new burst selection
criterium requires only a couple of lines of code.
- [fit routines](http://fretbursts.readthedocs.org/en/latest/fit.html) for FRET efficiency
  ([multi-model histogram fit](http://fretbursts.readthedocs.org/en/latest/fit.html#fitting-e-or-s-histograms),
  [MLE Poisson models](http://fretbursts.readthedocs.org/en/latest/data_class.html#fretbursts.burstlib.Data.fit_E_ML_poiss),
  [weighted least squares models](http://fretbursts.readthedocs.org/en/latest/data_class.html#fretbursts.burstlib.Data.fit_E_m),
  [weighted expectation maximization](http://fretbursts.readthedocs.org/en/latest/data_class.html#fretbursts.burstlib.Data.fit_E_two_gauss_EM),
  etc...)

Moreover FRETBursts includes
[a large set](https://github.com/tritemio/FRETBursts/blob/master/fretbursts/burst_plot.py) of modular
[plot functions](http://fretbursts.readthedocs.org/en/latest/files_description.html#module-fretbursts.burst_plot) for
background, time-traces, rate-traces, E, S, ALEX histograms, weighted kernel
density estimation ([KDE](http://en.wikipedia.org/wiki/Kernel_density_estimation))
and more. Thanks to the excellent [Matplotlib](http://matplotlib.org/) library,
FRETBursts can produce publication-quality plots out of the box.

Motivations
-----------

This software aims to be a reference implementation for both established
and novel algorithms related to bursts analysis of smFRET data.

Despite the broad diffusion of smFRET experiments on freely diffusing
molecules, before FRETBursts, no complete smFRET burst analysis software was
freely available on internet. Each group have re-implemented the analysis
in-house with little or no code sharing. This is clearly sub-optimal
either because specific advances in the burst analysis are not readily
available to a wide public of smFRET users and because subtle differences in
implementation make the comparison of experiments performed by different
groups problematic.

We envision FRETBursts both as a state-of-the-art burst analysis package
for smFRET experimenters, and as a benchmark for advanced users willing
to explore new algorithms or to compare alternative implementations.

Software Environment
--------------------
FRETBursts is written in the [python programming language](http://www.python.org/)
using the standard scientific-python stack of libraries (Numpy, Scipy, Matplotlib, IPython).
Not only FRETBursts but also the entire software stack on which it is built upon
are open-source and freely available to any scientist.

FRETBursts uses consolidated software engineering techniques (version control,
unit testing, regression testing) and a workflow based on
[IPython Notebook](http://ipython.org/notebook.html)
to ensure robustness and reproducibility of the results. For example,
when loading FRETBursts in an ipython notebook, the current commit ID is always
displayed and saved.

We provide a [list of tutorials](#how-to-use) (IPython notebooks) that can be
viewed online, edited and re-executed. The
[reference documentation](http://fretbursts.readthedocs.org/en/latest/)
is generated by Sphinx extracting the docstrings from the source code.

###External resources

For a comprehensive tutorial on using python for scientific computing:

* [Python Scientific Lecture Notes](http://scipy-lectures.github.io/)

IPython Notebook is an interactive web-based environment that allows mixing
rich text, math and graphics with (live) code. For more info please visit:

* [The IPython Notebook Homepage](http://ipython.org/ipython-doc/stable/interactive/notebook.html)
* [Notebook examples](http://nbviewer.ipython.org/github/ipython/ipython/blob/master/examples/Notebook/Index.ipynb)
* [A gallery of interesting IPython Notebooks](https://github.com/ipython/ipython/wiki/A-gallery-of-interesting-IPython-Notebooks)

##Installation

Briefly, the installation requires installing a scientific python
distribution, downloading FRETBursts sources, and setting up a folder for the
FRETBursts notebooks.

The first time you execute FRETBursts, you need to
run the [FRETBursts Installation.ipynb](http://nbviewer.ipython.org/github/tritemio/FRETBursts/blob/master/notebooks/FRETBursts Installation.ipynb)
notebook that will write a configuration file
containing FRETBursts's source folder.
After that, FRETBursts is loaded running a small script (`load_fretbursts.py`) placed
in the notebooks folder.

A detailed description of the installation can be found in:

* [FRETBursts documentation: Getting started](http://fretbursts.readthedocs.org/en/latest/getting_started.html)


##How to use
The official FRETBursts documentation is built and hosted by ReadTheDocs:

* [FRETBursts Documentation](http://fretbursts.readthedocs.org/en/latest/)

We provide a list of IPython notebooks showing typical workflows
for smFRET analysis and illustrating FRETBursts functionalities.
These notebooks can be either viewed online or downloaded and executed locally
using publically available datasets (see below). You can read the tutorials
online at the following locations:

* [FRETBursts - us-ALEX smFRET burst analysis](http://nbviewer.ipython.org/urls/raw.github.com/tritemio/FRETBursts_notebooks/master/notebooks/FRETBursts%2520-%2520us-ALEX%2520smFRET%2520burst%2520analysis.ipynb) *(start here)*
* [FRETBursts - 8-spot smFRET burst analysis](http://nbviewer.ipython.org/urls/raw.github.com/tritemio/FRETBursts_notebooks/master/notebooks/FRETBursts%2520-%25208-spot%2520smFRET%2520burst%2520analysis.ipynb)
* [FRETBursts - ns-ALEX example](http://nbviewer.ipython.org/urls/raw.github.com/tritemio/FRETBursts_notebooks/master/notebooks/FRETBursts%20-%20ns-ALEX%20example.ipynb)

You can download the tutorials from the [FRETBursts_notebooks](https://github.com/tritemio/FRETBursts_notebooks)
repository.

> *NOTE:* We include an unevaluated copy of the tutorials in the FRETBursts
> sources in the
> [notebooks folder](https://github.com/tritemio/FRETBursts/tree/master/notebooks).

We provide a public dataset [1] to test and demonstrate FRETBursts
functionalities. These dataset files will be downloaded when running
the tutorials.

[1] A. Ingargiola, S. Chung (2014): smFRET example datasets for the FRETBursts
software. [DOI 10.6084/m9.figshare.1019906](http://dx.doi.org/10.6084/m9.figshare.1019906)

##Development

The documentation is built using [Sphinx](http://sphinx-doc.org/) (1.2.2 or
later) and the [napoleon extension](https://pypi.python.org/pypi/sphinxcontrib-napoleon).
A notebook that builds the HTML docs can be found in
[`notebooks/dev/docs/`](https://github.com/tritemio/FRETBursts/tree/master/notebooks/dev/docs).

The unit tests are written with [pytest](http://pytest.org/latest/).
Notebooks that execute the unit tests can be found in
[`notebooks/dev/test/`](https://github.com/tritemio/FRETBursts/tree/master/notebooks/dev/tests).
In the same folder a notebook for regression testing is provided.


##Acknowledgements

This work was supported by NIH grants R01 GM069709 and R01 GM095904.

##License and Copyrights

FRETBursts - A bursts analysis toolkit for single and multi-spot smFRET data.

Copyright (C) 2014 Antonino Ingargiola - *tritemio @ gmail.com*

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
version 2, as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You can find a full copy of the license in the file LICENSE.txt
