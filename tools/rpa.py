"""Extract a Ren'Py archive (RPA-2.0/3.0) into a folder.

rpa.py <archive.rpa> <dest>

The index is a pickle of plain containers; the unpickler only allows the
two callables protocol 2 uses to rebuild bytes.
"""
import io, os, pickle, sys, zlib


class Plain(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) in (("_codecs", "encode"), ("builtins", "bytes"), ("__builtin__", "bytes")):
            return super().find_class(module, name)
        raise pickle.UnpicklingError(f"refusing {module}.{name}")


def main(path, dest):
    with open(path, "rb") as f:
        head = f.readline().split()
        offset = int(head[1], 16)
        key = int(head[2], 16) if head[0] == b"RPA-3.0" else 0
        f.seek(offset)
        index = Plain(io.BytesIO(zlib.decompress(f.read())), encoding="bytes").load()
        for name, parts in index.items():
            name = name.decode() if isinstance(name, bytes) else name
            out = os.path.normpath(os.path.join(dest, name))
            if not out.startswith(os.path.abspath(dest) + os.sep) and not out.startswith(dest + os.sep):
                raise SystemExit(f"bad name {name!r}")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "wb") as o:
                for part in parts:
                    off, length = part[0] ^ key, part[1] ^ key
                    prefix = part[2] if len(part) > 2 else b""
                    prefix = prefix.encode("latin-1") if isinstance(prefix, str) else prefix
                    f.seek(off)
                    o.write(prefix + f.read(length - len(prefix)))
    print(f"{len(index)} files from {path}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
