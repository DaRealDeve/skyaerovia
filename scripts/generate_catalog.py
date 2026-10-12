"""Regenerate the fictional domestic route catalog; dates advance at runtime."""
import sys,json,gzip
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from schedule import build_catalog
catalog=build_catalog()
(ROOT/'flight_catalog.json.gz').write_bytes(gzip.compress((json.dumps(catalog,separators=(',',':'))+'\n').encode(),mtime=0))
print(f"Generated {len(catalog['templates']):,} daily departures across 32 cities, repeated over a rolling 90-day window.")
