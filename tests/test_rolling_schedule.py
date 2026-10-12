from datetime import date,datetime,timedelta
import tempfile,unittest,json,gzip
from pathlib import Path
from unittest.mock import patch
import extractor
from integration import prepare_request,find_matches
from schedule import RollingSchedule,build_catalog,find_flight,load_app_flights
from city_catalog import CITIES,AIRLINES
from bookings import BookingStore

class TestRollingSchedule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=json.loads(gzip.decompress((Path(__file__).resolve().parents[1]/'flight_catalog.json.gz').read_bytes()));cls.start=date(2026,12,29);cls.schedule=RollingSchedule(cls.catalog,cls.start)
    def test_all_city_pairs_have_six_options_and_four_nonstop_every_day(self):
        self.assertEqual(len(CITIES),32);self.assertEqual(self.schedule.options,535680)
        for origin in CITIES:
            for dest in CITIES:
                if origin==dest:continue
                for offset in (0,30,89):
                    flights=self.schedule.for_route(origin,dest,self.start+timedelta(days=offset))
                    self.assertEqual(len(flights),6);self.assertEqual(len({f['id'] for f in flights}),6)
                    self.assertEqual(sum(f['stops']==0 for f in flights),4)
                    self.assertEqual({f['airline'] for f in flights},set(AIRLINES))
    def test_overnight_arrival_dates_and_durations_match(self):
        overnight=0
        for origin in CITIES:
            for dest in CITIES:
                if origin==dest:continue
                for f in self.schedule.for_route(origin,dest,self.start):
                    dep=datetime.fromisoformat(f['date']+'T'+f['departure']);arr=datetime.fromisoformat(f['arrival_date']+'T'+f['arrival'])
                    self.assertEqual((arr-dep).total_seconds()/60,f['duration'])
                    overnight+=arr.date()>dep.date()
        self.assertGreater(overnight,0)
    def test_window_rolls_forward_and_ids_and_prices_remain_stable(self):
        day=self.start+timedelta(days=5)
        before=self.schedule.for_route('Goa','Jaipur',day)
        after=RollingSchedule(self.catalog,self.start+timedelta(days=1)).for_route('Goa','Jaipur',day)
        self.assertEqual(before,after)
        self.assertEqual(self.schedule.for_route('Delhi','Mumbai',self.start-timedelta(days=1)),[])
        self.assertEqual(self.schedule.for_route('Delhi','Mumbai',self.start+timedelta(days=90)),[])
        self.assertEqual(find_flight(self.schedule,before[-1]['id']),before[-1])
    def test_new_cities_aliases_and_search_return_results(self):
        for message,origin,dest in [('Delhi to Goa tomorrow','Delhi','Goa'),('Trichy to Jaipur tomorrow','Tiruchirappalli','Jaipur'),('Madurai se Raipur kal','Madurai','Raipur')]:
            with patch.object(extractor,'extract_with_ai',side_effect=RuntimeError('offline')):
                state,status,_=prepare_request(message,{},self.start,extractor.extract_request)
            self.assertEqual((status,state['origin'],state['destination']),('ready',origin,dest))
            self.assertEqual(len(find_matches(self.schedule,state)),6)
    def test_nonstop_budget_and_sort_filters_still_apply(self):
        state={'origin':'Delhi','destination':'Goa','date':self.start.isoformat(),'non_stop':True}
        direct=find_matches(self.schedule,state);self.assertEqual(len(direct),4)
        limit=direct[0]['price'];cheap=find_matches(self.schedule,state,budget_override=limit)
        self.assertTrue(cheap);self.assertTrue(all(f['price']<=limit for f in cheap))
        shortest=find_matches(self.schedule,state,sort_override='duration')
        self.assertEqual([f['duration'] for f in shortest],sorted(f['duration'] for f in shortest))
    def test_booking_snapshot_preserves_overnight_arrival_date(self):
        f=self.schedule.for_route('Delhi','Kochi',self.start)[-1]
        with tempfile.TemporaryDirectory() as d:
            s=BookingStore(Path(d)/'b.db');t=s.create(f,1,'8'*32,now=datetime(2026,12,28).astimezone())
            self.assertEqual(t['flight']['arrival_date'],f['arrival_date'])
