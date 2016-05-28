#!/usr/bin/env python3
'''
Suppose you're trying to estimate someone's median household income
based on their current location. Perhaps they posted a photograph on
Twitter that has latitude and longitude in its EXIF data. You might go
to the FCC census block conversions API (https://www.fcc.gov/general
/census-block-conversions-api) to figure out in which census block the
photo was taken.
'''

from destructure import match, MatchError, Binding, Switch
import json
from urllib.request import urlopen
from urllib.parse import urlencode



url = 'http://data.fcc.gov/api/block/find?'
params = {'format': 'json', 'showall': 'true',
          # 'latitude': 28.35975, 'longitude': -81.421988}
          'latitude': 28.359, 'longitude': -81.421}



results = Binding()

schema_one = \
{
    "County": {
        "name": results.county,
        "FIPS": str,
    },
    "State": {
        "name": results.state,
        "code": str,
        "FIPS": str,
    },
    "Block": {
        "FIPS": results.fips,
    },
    "executionTime": str,
    "status": "OK",
}

schema_intersection = \
{
    "executionTime": str,
    "County": {
        "FIPS": str,
        "name": results.county
    },
    "messages": [
        "FCC0001: The coordinate lies on the boundary of mulitple blocks, first FIPS is displayed. For a complete list use showall=true to display 'intersection' element in the Block"
    ],
    "Block": {
        "FIPS": str,
        "intersection": results.intersection
    },
    "status": "OK",
    "State": {
        "code": str,
        "FIPS": str,
        "name": results.state
    }
}



with urlopen(url + urlencode(params)) as response:
    data = response.read()

text = data.decode('utf-8')
mapping = json.loads(text)



s = Switch(data=mapping, binding=results)

if s.case(schema_one):
    codes = [results.fips]

elif s.case(schema_intersection):
    codes = [block['FIPS'] for block in results.intersection]

else:
    raise MatchError('Could not match any schemas')



if not codes or None in codes:
    fmt = 'No FIPS found for {latitude}, {longitude}'
    raise ValueError(fmt.format(**params))

for fips in codes:
    print(fips)

# From there, it's on to http://api.census.gov to finish the task.


