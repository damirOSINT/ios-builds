"""Read a Godot 4 .pck index (format 2 or 3) and optionally extract files."""
import struct, sys, os
def index(path):
    f=open(path,'rb'); h=f.read(4)
    assert h==b'GDPC', h
    ver,ma,mi,pa,flags=struct.unpack('<5I',f.read(20))
    base,=struct.unpack('<Q',f.read(8))
    if ver>=3:
        diro,=struct.unpack('<Q',f.read(8)); f.read(64); f.seek(diro)
    else:
        f.read(64)
    n,=struct.unpack('<I',f.read(4)); out=[]
    for _ in range(n):
        l,=struct.unpack('<I',f.read(4)); p=f.read(l).rstrip(b'\0').decode()
        off,size=struct.unpack('<QQ',f.read(16)); f.read(16); fl,=struct.unpack('<I',f.read(4))
        out.append((p,base+off,size,fl))
    return (ver,ma,mi,pa,flags),out
if __name__=='__main__':
    hdr,ents=index(sys.argv[1]); print(hdr,len(ents))
    for p,o,s,fl in ents:
        if len(sys.argv)<3 or any(k in p for k in sys.argv[2:]): print(p,s,fl)

def extract(path, out, want=lambda p: True):
    hdr, ents = index(path); f = open(path, 'rb'); n = 0
    for p, o, s, fl in ents:
        if not want(p): continue
        dst = os.path.join(out, p.replace('res://', ''))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        f.seek(o); open(dst, 'wb').write(f.read(s)); n += 1
    return n
