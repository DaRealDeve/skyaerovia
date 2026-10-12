"""Rolling 90-day fictional schedules, generated only for the requested route/day."""
from datetime import date, datetime, timedelta
import json
import gzip
import math
from pathlib import Path
from city_catalog import CITY_DATA, CITIES, CODES, AIRLINES

DAYS=90
TIMES=('05:45','08:30','11:40','14:55','18:20','22:10')


def build_catalog():
    templates=[]
    for oi,origin in enumerate(CITIES):
        for di,destination in enumerate(CITIES):
            if origin==destination:continue
            _,lat1,lon1=CITY_DATA[origin];_,lat2,lon2=CITY_DATA[destination]
            lat1,lat2=map(math.radians,(lat1,lat2))
            dlat=lat2-lat1;dlon=math.radians(lon2-lon1)
            a=math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
            distance=6371*2*math.asin(min(1,math.sqrt(a)))
            direct=max(50,round((distance/650*60+35)/5)*5)
            for ti,time in enumerate(TIMES):
                stops=1 if ti in (2,4) else 0
                duration=direct+(95 if stops else 0)+ti%2*5
                price=max(1800,round((1800+distance*1.7+ti*180-stops*550)/50)*50)
                templates.append({'template':f'{CODES[origin]}-{CODES[destination]}-{ti+1}',
                    'airline':AIRLINES[(oi+di+ti)%len(AIRLINES)],'from':origin,'to':destination,
                    'departure':time,'duration':duration,'stops':stops,'price':price})
    return {'version':1,'days':DAYS,'simulated':True,'templates':templates}


class RollingSchedule:
    def __init__(self,catalog,today):
        if catalog.get('version')!=1 or catalog.get('days')!=DAYS or catalog.get('simulated') is not True:
            raise ValueError('Invalid demo schedule catalog')
        self.start=today;self.end=today+timedelta(days=DAYS-1)
        self.by_route={};self.by_template={}
        for t in catalog['templates']:
            if t['from'] not in CITIES or t['to'] not in CITIES or t['from']==t['to'] or t['template'] in self.by_template:
                raise ValueError('Invalid schedule route')
            datetime.strptime(t['departure'],'%H:%M')
            if t['duration']<=0 or t['price']<=0 or t['stops'] not in (0,1):raise ValueError('Invalid schedule values')
            self.by_template[t['template']]=t
            self.by_route.setdefault((t['from'],t['to']),[]).append(t)
        if len(self.by_route)!=len(CITIES)*(len(CITIES)-1) or any(len(ts)!=6 for ts in self.by_route.values()):
            raise ValueError('Incomplete demo route coverage')
        self.options=len(self.by_template)*DAYS

    def materialize(self,t,day):
        dep=datetime.combine(day,datetime.strptime(t['departure'],'%H:%M').time())
        arr=dep+timedelta(minutes=t['duration'])
        price=t['price']+((day.toordinal()+sum(map(ord,t['template'])))%5)*100
        return {**{k:v for k,v in t.items() if k!='template'},'id':f'SKY2-{day:%Y%m%d}-{t["template"]}',
                'date':day.isoformat(),'arrival':arr.strftime('%H:%M'),'arrival_date':arr.date().isoformat(),'price':price}

    def for_route(self,origin,destination,day):
        day=date.fromisoformat(day) if isinstance(day,str) else day
        if not self.start<=day<=self.end:return []
        return [self.materialize(t,day) for t in self.by_route.get((origin,destination),[])]

    def get(self,ident):
        if not isinstance(ident,str) or not ident.startswith('SKY2-'):return None
        try:
            _,stamp,origin,destination,index=ident.split('-');day=datetime.strptime(stamp,'%Y%m%d').date()
            t=self.by_template[f'{origin}-{destination}-{index}']
            return self.materialize(t,day) if self.start<=day<=self.end else None
        except (ValueError,KeyError):return None


def load_app_flights(root,today):
    path=Path(root)/'flight_catalog.json.gz'
    if path.exists():return RollingSchedule(json.loads(gzip.decompress(path.read_bytes())),today)
    from integration import load_flights
    return load_flights(Path(root)/'flights.json')


def bounds(flights):
    if isinstance(flights,RollingSchedule):return flights.start,flights.end
    if flights:return min(date.fromisoformat(f['date']) for f in flights),max(date.fromisoformat(f['date']) for f in flights)
    return None,None


def find_flight(flights,ident):
    if isinstance(flights,RollingSchedule):return flights.get(ident)
    return next((f for f in (flights or []) if f['id']==ident),None)
