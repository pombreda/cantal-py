import sys
import struct

if sys.version_info >= (3, 4, 0):
    MemoryView = memoryview
else:

    import ctypes

    TYPEMAP = {
        'B': ctypes.c_char,
        'l': ctypes.c_long,
        'L': ctypes.c_ulong,
        'd': ctypes.c_double,
    }

    class MemoryView(object):
        __slots__ = ('_mmap', '_slice')

        def __init__(self, _mmap, _slice=None):
            self._mmap = _mmap
            self._slice = _slice

        def __getitem__(self, item):
            assert isinstance(item, slice), "Only slicing is supported"
            assert self._slice is None, "Only single level of slicing required"
            return MemoryView(self._mmap, item)

        def cast(self, typ):
            start, stop, step = self._slice.indices(len(self._mmap))
            assert step == 1, 'Only step 1 supported'
            bytesize = struct.calcsize(typ)
            _typ = TYPEMAP[typ] * ((stop - start) // bytesize)
            return _typ.from_buffer(self._mmap, start)
