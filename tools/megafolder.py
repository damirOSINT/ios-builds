"""List or download files from a public MEGA folder or file link.

megafolder.py <folder-url>                 lists the files
megafolder.py <folder-url> <regex> <out>   downloads the first matching file
megafolder.py <file-url> - <out>           downloads a single shared file
"""
import base64, json, re, sys, time, urllib.request
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def b64(s):
    s = s.replace("-", "+").replace("_", "/").replace(",", "")
    return base64.b64decode(s + "=" * (-len(s) % 4))


def api(handle, req):
    r = urllib.request.Request(
        "https://g.api.mega.co.nz/cs?id=1" + (f"&n={handle}" if handle else ""),
        data=json.dumps([req]).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r).read())[0]


def ecb_dec(key, data):
    d = Cipher(algorithms.AES(key), modes.ECB()).decryptor()
    return d.update(data) + d.finalize()


def nodes(url):
    handle, key = re.search(r"folder/([^#]+)#([^/?]+)", url).groups()
    master = b64(key)
    out = []
    for n in api(handle, {"a": "f", "c": 1, "ca": 1, "r": 1})["f"]:
        if n["t"] not in (0, 1):
            continue
        for pair in n["k"].split("/"):
            k = ecb_dec(master, b64(pair.split(":")[1]))
            akey = k if n["t"] == 1 else bytes(a ^ b for a, b in zip(k[:16], k[16:32]))
            d = Cipher(algorithms.AES(akey), modes.CBC(b"\0" * 16)).decryptor()
            attr = (d.update(b64(n["a"])) + d.finalize()).rstrip(b"\0")
            if attr.startswith(b"MEGA"):
                break
        name = json.loads(attr[4:].decode())["n"] if attr.startswith(b"MEGA") else "?"
        out.append({"h": n["h"], "p": n["p"], "t": n["t"], "name": name, "size": n.get("s", 0), "key": k})
    byh = {n["h"]: n for n in out}
    for n in out:
        path, p = [n["name"]], n["p"]
        while p in byh:
            path.insert(0, byh[p]["name"]); p = byh[p]["p"]
        n["path"] = "/".join(path)
    return handle, out


def download(handle, n, dest, part=64 << 20):
    """Fetches the file in ranges, retrying a range that stalls or fails."""
    k = n["key"]
    key = bytes(a ^ b for a, b in zip(k[:16], k[16:32]))
    iv = k[16:24] + b"\0" * 8
    dec = Cipher(algorithms.AES(key), modes.CTR(iv)).decryptor()
    size, start, t0 = n["size"], 0, time.time()
    with open(dest, "wb") as f:
        while start < size:
            end = min(start + part, size) - 1
            for attempt in range(8):
                try:
                    g = api(handle, {"a": "g", "g": 1, "p" if n.get("public") else "n": n["h"]})["g"]
                    with urllib.request.urlopen(f"{g}/{start}-{end}", timeout=60) as r:
                        data = r.read()
                    if len(data) == end - start + 1:
                        break
                except Exception as e:
                    print("retry", start, e, flush=True)
                time.sleep(5 * (attempt + 1))
            else:
                raise SystemExit(f"range {start}-{end} failed")
            f.write(dec.update(data))
            start = end + 1
            print(f"{start / 2**20:.0f}/{size / 2**20:.0f} MB, {start / 2**20 / (time.time() - t0):.1f} MB/s", flush=True)
        f.write(dec.finalize())


def file_node(url):
    """A single shared file (mega.nz/file/H#K or the old mega.nz/#!H!K)."""
    handle, key = (re.search(r"file/([^#]+)#(.+)$", url) or re.search(r"#!([^!]+)!(.+)$", url)).groups()
    k = b64(key)
    info = api(None, {"a": "g", "p": handle})
    akey = bytes(a ^ b for a, b in zip(k[:16], k[16:32]))
    d = Cipher(algorithms.AES(akey), modes.CBC(b"\0" * 16)).decryptor()
    attr = (d.update(b64(info["at"])) + d.finalize()).rstrip(b"\0")
    name = json.loads(attr[4:].decode())["n"] if attr.startswith(b"MEGA") else "?"
    return {"h": handle, "p": None, "t": 0, "name": name, "path": name, "size": info["s"], "key": k, "public": True}


if __name__ == "__main__":
    if "/file/" in sys.argv[1] or "#!" in sys.argv[1]:
        n = file_node(sys.argv[1])
        print(n["name"], n["size"], flush=True)
        if len(sys.argv) > 3:
            download(None, n, sys.argv[3])
        sys.exit()
    handle, ns = nodes(sys.argv[1])
    if len(sys.argv) == 2:
        for n in ns:
            if n["t"] == 0:
                print(f'{n["size"] / 2**20:8.1f} MB  {n["path"]}')
    else:
        n = next(n for n in ns if n["t"] == 0 and re.search(sys.argv[2], n["path"]))
        print("downloading", n["path"], n["size"], flush=True)
        download(handle, n, sys.argv[3])
