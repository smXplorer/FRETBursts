Burst selection
===============

.. module:: fretbursts.burstlib

After performing a burst search is common to select bursts according to
different criteria (burst size, FRET efficiency, etc...).

In FRETBursts this can be easily accomplished using the function
:func:`Select_bursts` (or its alias :func:`Sel`). This function requires a
:class:`Data` object and a :ref:`selection function <selection_functions>`
as parameters. :func:`Select_bursts` returns a new :class:`Data` object
containing only the new sub-set of bursts. A new selection can be applied 
to this new object as well. In this way, different
selection criteria can be freely combined in order to obtain a
burst population satisfying arbitrary constrains.

FRETBursts provides a large number of
:ref:`selection functions <selection_functions>`. Moreover, creating a new
selection function is extremely simple, requiring (usually) 2-3 lines of code.
You can just start from one of the functions in `select_bursts.py` and modify
it to obtain a different criterium.

The reference documentation for the selection functions follows.

.. autofunction:: Select_bursts

.. function:: Sel()

    Alias for :func:`Select_bursts`


.. autofunction:: Sel_mask

.. autofunction:: Sel_mask_apply


.. _selection_functions:

List of selection functions
---------------------------

.. automodule:: fretbursts.select_bursts
    :members:
