# -*- coding: utf-8 -*-
# Copyright 2017-2019 The pyXem developers
#
# This file is part of pyXem.
#
# pyXem is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyXem is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyXem.  If not, see <http://www.gnu.org/licenses/>.

def push_metadata_through(dummy,*args,**kwargs):
    """
    This function pushes loaded metadata through to pyxem objects, it is to be used for one
    purpose, see the __init__ of ElectronDiffraction for an example.

    Parameters
    ----------
    dummy :
        This will always be the "self" of the object to be initialised

    args : list
        This will always be the "args" of the object to be initialised

    kwargs : dict
        This will always be the "args" of the object to be initialised

    Returns
    -------
    dummy,args,kwargs :
        The input variables, adjusted correctly
    """
    try:
        meta_dict = args[0].metadata.as_dictionary()
        kwargs.update({'metadata': meta_dict})
    except AttributeError:
        pass  # this is because a numpy array has been passed
    except IndexError:
        pass  # this means that map continues to work.

    return dummy,args,kwargs

def load_mib(filename, scan_size, sum_length=10):
    """Load a medipix hdr/mib file.

    Parameters
    ----------
    filename : string
        File path and name to .hdr file.
    scan_size : int
        Scan size in pixels, allows the function to reshape the array into
        the right shape.
    sum_length : int
        Number of lines to sum over to determine scan fly back location.

    """
    dpt = load_with_reader(filename=filename, reader=mib_reader)
    dpt = ElectronDiffraction(dpt.data.reshape((scan_size, scan_size, 256, 256)))
    trace = dpt.inav[:,0:sum_length].sum((1,2,3))
    edge = np.where(trace==max(trace.data))[0][0]
    if edge==scan_size - 1:
        dp = ElectronDiffraction(dpt.inav[0:edge, 1:])
    else:
        dp = ElectronDiffraction(np.concatenate((dpt.inav[edge + 1:, 1:],
                                                 dpt.inav[0:edge, 1:]), axis=1))

    dp.data = np.flip(dp.data, axis=2)

    return dp

def load(filename,is_ElectronDiffraction=True):
    """
    A wrapper around hyperspy's load function that enables auto-setting signals to ElectronDiffraction
    and correct loading of previously saved ElectronDiffraction, TemplateMatchingResults and DiffractionVectors
    objects

    Parameters
    ----------

    filename : str
        A single filename of a previously saved pyxem object. Other arguments may
        succeed, but will have fallen back on hyperspy load and warn accordingly
    is_ElectronDiffraction : bool
        If the signal is not a pxm saved signal (eg - it's a .blo file), cast to
        an ElectronDiffraction object
    """
    if isinstance(filename,str) == False:
        warnings.warn("filename is not a single string, for clarity consider using hs.load()")
        s = hyperspyload(filename)
        return s

    signal_dictionary = {'electron_diffraction':ElectronDiffraction,
                         'template_matching':TemplateMatchingResults,
                         'diffraction_vectors':DiffractionVectors}

    file_suffix = '.' + filename.split('.')[-1]

    if file_suffix == '.mib':
        raise ValueError('mib files must be loaded directly using pxm.load_mib()')

    if file_suffix in ['.hspy','.blo']: # if True we are loading a signal from a format we know
        s = hyperspyload(filename)
        try:
            s = signal_dictionary[s.metadata.Signal.signal_type](s)
        except KeyError:
            if is_ElectronDiffraction:
                s = ElectronDiffraction(s)
            else:
                warnings.warn("No pyxem functionality used, for clarity consider using hs.load()")
    else:
        warnings.warn("file suffix unknown, for clarity consider using hs.load()")
        s = hyperspyload(filename)

    return s
