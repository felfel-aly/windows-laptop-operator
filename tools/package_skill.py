"""Build only the reviewed public inventory after a successful privacy check."""
import hashlib
from pathlib import Path
import zipfile
from privacy_scan import ROOT, scan

def main():
    names,findings=scan()
    if findings: raise SystemExit('Privacy scan failed; archive not created.')
    destination=ROOT/'dist/windows-laptop-operator.zip'
    destination.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            info=zipfile.ZipInfo('windows-laptop-operator/'+name,date_time=(2026,10,5,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,(ROOT/name).read_bytes())
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None: raise RuntimeError('Archive integrity failed')
        assert set(archive.namelist())=={'windows-laptop-operator/'+n for n in names}
    print(f'Built {destination.name}: {len(names)} files; SHA-256 {hashlib.sha256(destination.read_bytes()).hexdigest()}')

if __name__=='__main__': main()
