# Summertime Saga 0.20 was made for Ren'Py 7.3, whose renpy.loadsave had
# dumps (core.rpy copies objects with it). Ren'Py 7.8 moved it to
# renpy.compat.pickle, so put it back where the game looks for it.
# sys.modules is used so that nothing rebinds the store's renpy name.
python early:
    import sys as _compat_sys
    _compat_ls = _compat_sys.modules["renpy.loadsave"]
    if not hasattr(_compat_ls, "dumps"):
        __import__("renpy.compat.pickle")
        _compat_ls.dumps = _compat_sys.modules["renpy.compat.pickle"].dumps
    del _compat_sys, _compat_ls
