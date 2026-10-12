"""Route form, transparent empty states, and responsive flight cards."""
import html
from datetime import datetime,date
from zoneinfo import ZoneInfo
import streamlit as st
from integration import find_matches
from schedule import bounds,RollingSchedule
from city_catalog import CITIES,CODES,AIRLINES
from fares import fare_quote
from bookings import departure_time
from booking_ui import start_booking

CSS='''<style>
.stApp{background:#F3F6FB;color:#102A43;}.block-container{max-width:1180px;padding-top:2rem;}
[data-testid="stSidebar"]{background:#EAF1FA;}
.hero{background:linear-gradient(120deg,#071B3A,#145DA0);padding:24px;border-radius:18px;color:white;margin-bottom:16px;}
.hero h1{color:white;font-size:clamp(27px,4vw,40px);padding-top:0;}.hero p{color:#E3EEFF;margin-bottom:0;}
.st-key-quick_actions button{color:#145DA0;background:white;border:1px solid #D8E4F2;min-height:46px;}
.st-key-quick_actions button p{font-size:1rem;font-weight:600;color:#145DA0;}
.st-key-quick_actions button:hover{background:#EAF1FA;border-color:#145DA0;}
.flight-card{background:white;padding:22px;border:1px solid #D8E4F2;border-radius:16px;margin-bottom:6px;box-shadow:0 3px 12px #071B3A06;}
.flight-card h3{color:#071B3A;font-size:23px;padding-top:8px;}.flight-card .detail{color:#526D82;font-size:13px;}
.card-top{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;color:#526D82;font-size:13px;}
.stop-pill{background:#EAF4F0;color:#17624B;border-radius:20px;padding:3px 10px;}
.journey{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);align-items:center;gap:18px;margin:14px 0;}
.journey strong{display:block;font-size:27px;color:#071B3A;}.journey span{display:block;overflow-wrap:anywhere;color:#526D82;font-size:14px;}
.journey-line{color:#145DA0;border-bottom:1px solid #C9D9E9;padding:8px;}
.card-fare{border-top:1px solid #E2EBF4;padding-top:12px;display:flex;gap:10px;justify-content:space-between;flex-wrap:wrap;}
.card-fare .fare{margin-right:8px;font-size:27px;font-weight:700;color:#0B3D91;}
[data-testid="stForm"]{background:white;border-radius:14px;}
@media(max-width:700px){.block-container{padding-top:1rem;padding-left:1rem;padding-right:1rem;}.hero{padding:18px;}.hero h1{font-size:27px;}.flight-card{padding:16px;}.journey{gap:8px;}.journey strong{font-size:22px;}.journey span{font-size:12px;}.journey-line{font-size:12px;}.card-fare .fare{font-size:24px;}}
</style>'''


def schedule_header(flights,today):
    first,last=bounds(flights)
    if flights:
        if isinstance(flights,RollingSchedule):
            st.caption(f'{len(CITIES)} cities · {len(flights.by_route):,} routes · {len(AIRLINES)} airline names · Next 90 days · IST')
        st.caption(f'Travel dates: {first} to {last}. Overnight arrivals show their arrival date.')
        if last<today:st.warning('The sample dates have expired. Please refresh the schedule.')
    return first,last


def search_form(first,last,today):
    with st.expander('Choose your route and date',expanded=st.session_state.results is None):
        st.caption('Use the form for a quick search, or describe your journey to Skye below.')
        with st.form('flight_search'):
            origin_col,dest_col,date_col=st.columns([1,1,1])
            origin=origin_col.selectbox('From',CITIES,key='form_origin')
            destination=dest_col.selectbox('To',CITIES,index=1,key='form_destination')
            minimum=max(first,today) if first else today
            maximum=max(minimum,last) if last else None
            when=date_col.date_input('Travel date',value=minimum,min_value=minimum,max_value=maximum)
            submit=st.form_submit_button('Search flights',type='primary',use_container_width=True)
        if submit:
            if origin==destination:st.warning('Choose different departure and destination cities.')
            else:
                state={'origin':origin,'destination':destination,'date':when.isoformat(),'sort_by':'price'}
                st.session_state.results=state;st.session_state.request=dict(state)
                st.session_state.messages.append({'role':'user','content':f'{origin} to {destination} on {when}'})
                st.session_state.messages.append({'role':'assistant','content':f'Here are your simulated flight options for {origin} to {destination} on {when}.'})
                st.rerun()


def filtered_matches(flights,state,sort=None,budget=None,stops=None):
    matches=find_matches(flights,state,sort,budget,stops)
    airlines=st.session_state.get('airline_choices',[]);time=st.session_state.get('time_choice','Any time')
    if airlines:matches=[f for f in matches if f['airline'] in airlines]
    windows={'Morning (05–12)':(5,12),'Afternoon (12–17)':(12,17),'Evening (17–22)':(17,22)}
    if time in windows:
        lo,hi=windows[time];matches=[f for f in matches if lo<=int(f['departure'][:2])<hi]
    elif time=='Late night (22–05)':matches=[f for f in matches if int(f['departure'][:2])>=22 or int(f['departure'][:2])<5]
    return matches


def clear_result_filters():
    for k,v in (('budget_enabled',False),('stops_choice','Allow stops'),('airline_choices',[]),('time_choice','Any time')):st.session_state[k]=v
    if st.session_state.results:
        st.session_state.results={**st.session_state.results,'max_price':None,'non_stop':False}
        st.session_state.request=dict(st.session_state.results)


def empty_message(flights,state):
    first,last=bounds(flights)
    if first and not first<=date.fromisoformat(state['date'])<=last:
        return f'That date is outside our schedule. Choose a date from {first} through {last}.'
    route=find_matches(flights,{**state,'max_price':None,'non_stop':False})
    if route:return f'Flights exist on this route. The lowest base fare is ₹{min(f["price"] for f in route):,}. Try another airline/time or relax the budget and stops filters.'
    return 'No simulated flights on that date. Choose another date within the displayed schedule.'


def cards(flights,state,sort,budget,stops,cabin):
    matches=filtered_matches(flights,state,sort,budget,stops)
    st.divider();st.subheader('Your flight options');st.caption(f'{len(matches)} simulated flight(s) match the current filters.')
    if not matches:
        st.info(empty_message(flights,state))
        if find_matches(flights,{**state,'max_price':None,'non_stop':False}):
            st.button('Show all flights on this route',on_click=clear_result_filters)
    for flight in matches:
        airline,ident,origin,destination,day,departure,arrival=(html.escape(str(flight[k])) for k in ('airline','id','from','to','date','departure','arrival'))
        stop_label='Nonstop' if flight['stops']==0 else f'{flight["stops"]} stop(s)'
        quote=fare_quote(flight['price'],1,cabin);total=quote['total_paise']/100
        arrival_day=flight.get('arrival_date',flight['date'])
        overnight=' · arrives '+html.escape(arrival_day)+' (+1 day)' if arrival_day!=flight['date'] else ''
        st.markdown(f'''<div class="flight-card">
          <div class="card-top"><span>{airline} · {ident}</span><span class="stop-pill">{stop_label}</span></div>
          <h3>{origin} → {destination}</h3>
          <div class="journey"><div><strong>{departure}</strong><span>{CODES.get(flight['from'],'')} · {origin}</span></div>
          <div class="journey-line">{flight['duration']//60}h {flight['duration']%60:02d}m →</div>
          <div><strong>{arrival}</strong><span>{CODES.get(flight['to'],'')} · {destination}</span></div></div>
          <p class="detail">{day}{overnight} · All times IST</p>
          <div class="card-fare"><div><span class="fare">₹{total:,.2f}</span> <span>{cabin} · per passenger, including GST</span></div>
          <span class="detail">Economy base fare ₹{flight['price']:,}. Cabin fare and tax shown before confirmation.</span></div>
        </div>''',unsafe_allow_html=True)
        departed=departure_time(flight)<=datetime.now(ZoneInfo('Asia/Kolkata'))
        st.button('Book demo ticket',key='book_'+flight['id'],type='primary',disabled=departed,
                  on_click=start_booking,args=(flight['id'],cabin),use_container_width=True)
        if departed:st.caption('This departure has passed. Choose a later flight to create a demo ticket.')
