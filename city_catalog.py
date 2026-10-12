"""Shared domestic demo cities; coordinates are approximate city centres."""
CITY_DATA = {
 'Delhi':('DEL',28.61,77.21), 'Mumbai':('BOM',19.08,72.88),
 'Bengaluru':('BLR',12.97,77.59), 'Chennai':('MAA',13.08,80.27),
 'Hyderabad':('HYD',17.39,78.49), 'Kolkata':('CCU',22.57,88.36),
 'Pune':('PNQ',18.52,73.86), 'Ahmedabad':('AMD',23.02,72.57),
 'Jaipur':('JAI',26.91,75.79), 'Goa':('GOI',15.49,73.83),
 'Lucknow':('LKO',26.85,80.95), 'Kochi':('COK',9.93,76.27),
 'Thiruvananthapuram':('TRV',8.52,76.94), 'Varanasi':('VNS',25.32,82.97),
 'Patna':('PAT',25.59,85.14), 'Chandigarh':('IXC',30.73,76.78),
 'Srinagar':('SXR',34.08,74.80), 'Bhubaneswar':('BBI',20.30,85.82),
 'Visakhapatnam':('VTZ',17.69,83.22), 'Mangaluru':('IXE',12.91,74.86),
 'Indore':('IDR',22.72,75.86), 'Nagpur':('NAG',21.15,79.09),
 'Bhopal':('BHO',23.26,77.41), 'Ranchi':('IXR',23.34,85.31),
 'Amritsar':('ATQ',31.63,74.87), 'Udaipur':('UDR',24.59,73.71),
 'Dehradun':('DED',30.32,78.03), 'Coimbatore':('CJB',11.02,76.96),
 'Jammu':('IXJ',32.73,74.86), 'Raipur':('RPR',21.25,81.63),
 'Madurai':('IXM',9.93,78.12), 'Tiruchirappalli':('TRZ',10.79,78.70),
}
CITIES=tuple(CITY_DATA)
CODES={name:data[0] for name,data in CITY_DATA.items()}
EXTRA_ALIASES={'Raipur':['rpr'],'Madurai':['ixm'],'Tiruchirappalli':['trichy','tiruchi','trz']}
AIRLINES=('IndiGo','Air India','Akasa Air','SpiceJet','Air India Express','Alliance Air')
