# tr.py <www> — translates Cocogoat? Cocomilk! to Russian. The UI is a Vue
# build whose texts are template literals in assets/index-*.js; each one in
# ru.json is swapped (keeping the spaces around it), except alt texts.
import glob, json, os, re, sys

www = sys.argv[1]
ru = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ru.json"), encoding="utf-8"))
js = glob.glob(os.path.join(www, "assets", "index-*.js"))[0]
s = open(js, encoding="utf-8").read()
missing = []
for en, tr in ru.items():
    pat = re.compile(r"(?<!alt:)`(\s*)" + re.escape(en) + r"(\s*)`")
    s, n = pat.subn(lambda m: "`" + m.group(1) + tr.replace("`", "'") + m.group(2) + "`", s)
    if not n:
        missing.append(en)
open(js, "w", encoding="utf-8").write(s)
print("translated:", len(ru) - len(missing), "of", len(ru))
for m in missing:
    print("not found:", m)
