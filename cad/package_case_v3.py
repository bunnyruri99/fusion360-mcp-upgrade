"""Package the final, verified native design and print files without modifying Fusion."""
from pathlib import Path
import json
import zipfile

out=Path(__file__).resolve().parent/'case_v3'
report=json.loads((out/'native_exports_verification.json').read_text())
assert len(report['module_insertion_samples'])==49 and report['lid_insertion_samples']==25
assert all(s['intersection_mm3']==0 for s in report['module_insertion_samples'])
assert report['M3_insert_count']==12 and report['M3_screw_count']==12
native=json.loads((out/'fusion_case_verification.json').read_text())
assert all(not s['warnings_or_errors'] for s in native['native_features'].values())
assert native['assembly_grounded'] and native['TFT_to_frame_seating_gap_mm']==0
assert abs(native['USB_front_recess_mm']-.25)<1e-8
files=list((out/'deliverables').glob('*.stl'))+list((out/'deliverables').glob('*.f3d'))
assert len(files)==5
files += [out/name for name in ['LAP_RAP_V3.md','fusion_inside.png','fusion_frame.png','fusion_assembled.png',
                              'fusion_case_verification.json','native_exports_verification.json','delivery_verification.json']]
archive=out/'flip_clock_v3_M3_STL_Fusion_va_lap_rap.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in files:
        assert p.exists() and p.stat().st_size>0,p
        z.write(p,p.relative_to(out))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(files)
with zipfile.ZipFile(out/'deliverables'/'flip_clock_case_v3_M3_inserts.f3d') as z:assert z.testzip() is None
print(json.dumps({'package':str(archive),'file_count':len(files),'bytes':archive.stat().st_size,'CRC':'passed'},indent=2))
