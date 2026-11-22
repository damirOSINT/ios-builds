# Summertime Saga 0.20 was made for Ren'Py 7.3. Two things changed since:
#  - renpy.loadsave.dumps (core.rpy copies objects with it) moved to
#    renpy.compat.pickle;
#  - im.Composite takes its oversample from its first image, so the game's
#    empty im.Composite((0, 0)) fails.
# sys.modules is used so that nothing rebinds the store's renpy name.
python early:
    import sys as _compat_sys
    _compat_ls = _compat_sys.modules["renpy.loadsave"]
    if not hasattr(_compat_ls, "dumps"):
        __import__("renpy.compat.pickle")
        _compat_ls.dumps = _compat_sys.modules["renpy.compat.pickle"].dumps

    _compat_im = _compat_sys.modules["renpy.display.im"]
    _compat_composite_init = _compat_im.Composite.__init__

    def _compat_composite(self, size, *args, **properties):
        if args:
            return _compat_composite_init(self, size, *args, **properties)
        _compat_im.ImageBase.__init__(self, size, **properties)
        self.size = size
        self.positions = ()
        self.images = []
        self.oversample = 1

    _compat_im.Composite.__init__ = _compat_composite
    del _compat_sys, _compat_ls
