"""tiny scratch main/readback control; saved-state inspection is stubbed."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('second_spatial_metadata',here/'accept_real_spatial_20222023.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
scratch=Path(tempfile.mkdtemp(prefix='spatial-second-resource-',dir=here))
results=[]
for name,log,expected in (
    ('present','1.0 real 2.0 user 3.0 sys\n10 maximum resident set size\n20 peak memory footprint\n4.5 real 6.0 user 7.0 sys\n123456 maximum resident set size\n234567 peak memory footprint\n',
        dict(timing=dict(wall_seconds=4.5,user_seconds=6.,system_seconds=7.),maximum_resident_bytes=123456,peak_memory_footprint_bytes=234567)),
    ('missing','ordinary fit log without time metrics\n',dict(timing=None,maximum_resident_bytes=None,peak_memory_footprint_bytes=None))):
    stem=scratch/name
    for suffix,value in {'-exit.txt':'0\n','-launch-analysis-tree.txt':h.ANALYSIS+'\n','-launch-analysis-status.txt':'',
        '-start.txt':'start\n','-finish.txt':'finish\n','-launch-head.txt':'tiny-head\n','.log':log}.items():
        Path(str(stem)+suffix).write_text(value)
    with patch.object(h,'OUTPUT',stem),patch.object(h,'PREVIOUS_SHA','a'*64),patch.object(h,'inspect_second_year',return_value=dict(status='metadata_passed_pending_root_acceptance',eligible_as_predecessor=True)) as inspect,redirect_stdout(io.StringIO()):
        assert h.main()==0
    assert inspect.call_count==1
    report=json.loads(Path(str(stem)+'-saved-metadata-acceptance.json').read_text())
    assert report['whole_command']==expected
    assert report['launch']['exit']==0 and report['launch']['analysis_tree']==h.ANALYSIS
    results.append(dict(mode=name,whole_command=report['whole_command']))
print(json.dumps(dict(status='passed',scope='scratch run-record files and stubbed saved-json inspection only; no real artifacts, source, arrays, model or strict reader',controls=results,scratch=str(scratch)),indent=2))
