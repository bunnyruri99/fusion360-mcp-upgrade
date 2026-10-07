"""Invoke the installed native bridge in the current Fusion document."""
import argparse
import asyncio
import json
from fusion360_mcp.fusion.client import FusionClient
from fusion360_mcp.fusion.protocol import FusionRequest

p=argparse.ArgumentParser()
p.add_argument('action')
p.add_argument('--report-path')
p.add_argument('--output-dir')
p.add_argument('--image-path')
p.add_argument('--view')
p.add_argument('--verification-dir')
a=p.parse_args()
args={k:v for k,v in vars(a).items() if v is not None}
c=FusionClient('127.0.0.1',9876,600)
response=asyncio.run(c.send(FusionRequest(tool='pcb_bracket_native',args=args)))
print(json.dumps(response.model_dump(),indent=2),flush=True)
if not response.success:raise SystemExit(1)
