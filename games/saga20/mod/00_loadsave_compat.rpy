# Summertime Saga 0.20 was made for Ren'Py 7.3, whose renpy.loadsave had
# dumps (core.rpy copies objects with it). Ren'Py 7.8 moved it to
# renpy.compat.pickle, so put it back where the game looks for it.
python early:
    import renpy.loadsave
    if not hasattr(renpy.loadsave, "dumps"):
        import renpy.compat.pickle
        renpy.loadsave.dumps = renpy.compat.pickle.dumps
