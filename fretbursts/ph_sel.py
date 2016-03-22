#
# FRETBursts - A single-molecule FRET burst analysis toolkit.
#
# Copyright (C) 2014-2016 Antonino Ingargiola <tritemio@gmail.com>
#
"""
In this module, we define the class :class:`Ph_sel` used to specify a
"selection" of a sub-set of photons/timestamps  (i.e. all-photons,
Donor-excitation-period photons, etc...).

A photon selection can be one of the base *photon streams* or a combination of
them. The base *photon streams* are: photon from the donor (or acceptor) emission
channel, detected during the donor (or acceptor) excitation period. For
non-ALEX data, only the donor excitation period streams are defined.

The following table shows base *photon streams* for smFRET data (non-ALEX):

=================   =====================
Photon selection    Syntax
=================   =====================
D-emission          `Ph_sel(Dex='Dem')`
A-emission          `Ph_sel(Dex='Aem')`
=================   =====================

and for ALEX data:

==============================   =====================
Photon selection                 Syntax
==============================   =====================
D-emission during D-excitation   `Ph_sel(Dex='Dem')`
A-emission during D-excitation   `Ph_sel(Dex='Aem')`
D-emission during A-excitation   `Ph_sel(Aex='Dem')`
A-emission during A-excitation   `Ph_sel(Aex='Aem')`
==============================   =====================

Additionally, all photons can be selected with `Ph_sel('all')` (this is a
shortcut for  `Ph_sel(Dex='DAem', Aex='DAem')` as explained below).

Examples:

    - `Ph_sel(Dex='DAem', Aex='DAem')` or `Ph_sel('all')` select all photons.
    - `Ph_sel(Dex='DAem')` selects only donor and acceptor photons
      emitted during donor excitation. These are all photons in
      non-ALEX data.
    - `Ph_sel(Dex='Aem', Aex='Aem')` selects all photons detected in
      the acceptor-emission channel.

The documentation for the :class:`Ph_sel` class can be found below.

"""

from collections import namedtuple


# Implementation Rationale:
#
#   This class is implemented as a named tuple that is an immutable object.
#   This means the Ph_sel objects can be used as dictionary keys. This would
#   not be possible if Ph_sel were dict objects. The __new__ method is just a nicety
#   to allow only valid arguments values and to throw meaningful exceptions
#   otherwise.
#
class Ph_sel(namedtuple('Ph_sel', ['Dex', 'Aex'])):
    """Class that describes a selection of photons.

    This class takes two arguments `Dex` and `Aex`.
    Valid values for the arguments are the strings 'DAem', 'Dem', 'Aem' or
    `None`. These values select, respectively, donor+acceptor, donor-only,
    acceptor-only or no photons during an excitation period (`Dex` or `Aex`).

    The class must be called with at least one keyword argument or using
    the string 'all' as the only argument. Calling `Ph_sel('all')` is
    equivalent to `Ph_sel(Dex='DAem', Aex='DAem')`.
    Not specifying a keyword argument is equivalent to setting it to None.

    """
    valid_values = ('DAem', 'Dem', 'Aem', None)
    def __new__(cls, Dex=None, Aex=None):
        if Dex is None and Aex is None:
            raise ValueError("You need to specify at least one argument "
                             "(Dex, Aex or 'all').")
        if Dex == 'all':
            return super(Ph_sel, cls).__new__(cls, 'DAem', 'DAem')
        if Dex not in cls.valid_values or Aex not in cls.valid_values:
            raise ValueError("Invalid value %s. Valid values are "
                             "'DAem', 'Dem' or 'Aem' (or None)." %\
                             str((Dex, Aex)))
        return super(Ph_sel, cls).__new__(cls, Dex, Aex)

    def __str__(self):
        labels = {Ph_sel('all'): 'all',
                  Ph_sel(Dex='Dem'): 'DexDem', Ph_sel(Dex='Aem'): 'DexAem',
                  Ph_sel(Aex='Aem'): 'AexAem', Ph_sel(Aex='Dem'): 'AexDem',
                  Ph_sel(Dex='DAem'): 'Dex', Ph_sel(Aex='DAem'): 'Aex',
                  Ph_sel(Dex='DAem', Aex='Aem'): 'DexDAem_AexAem'}
        return labels.get(self, repr(self))
