from django.shortcuts import render
from django.db.models import Q
from django.shortcuts import redirect
from Oauth.models import Activities
from django.views.decorators.csrf import csrf_exempt
import requests
import json
from django.conf import settings
from django.http import JsonResponse
from django import forms
from geopy.geocoders import Nominatim
from geopy import distance as get_distance
import random
from types import SimpleNamespace

def _trans(value, index):
    byte, result, shift = None, 0, 0

    comp = None
    while byte is None or byte >= 0x20:
        byte = ord(value[index]) - 63
        index += 1
        result |= (byte & 0x1f) << shift
        shift += 5
        comp = result & 1

    return ~(result >> 1) if comp else (result >> 1), index


def decode(expression: str, precision: int = 5, geojson: bool = False, quick: bool = False) -> list[tuple[float, float]]:
    """
    Decode a polyline string into a set of coordinates.

    :param expression: Polyline string, e.g. 'u{~vFvyys@fS]'.
    :param precision: Precision of the encoded coordinates. Google Maps uses 5, OpenStreetMap uses 6.
        The default value is 5.
    :param geojson: Set output of tuples to (lon, lat), as per https://tools.ietf.org/html/rfc7946#section-3.1.1
    :return: List of coordinate tuples in (lat, lon) order, unless geojson is set to True.
    """
    coordinates, index, lat, lng, length, factor = [], 0, 0, 0, len(expression), float(10 ** precision)

    if (quick):
        lat_change, index = _trans(expression, index)
        lng_change, index = _trans(expression, index)
        lat += lat_change
        lng += lng_change
        coordinates.append((lng / factor, lat / factor))
        return [list(tup) for tup in coordinates]

    try:
        while index < length:
            lat_change, index = _trans(expression, index)
            lng_change, index = _trans(expression, index)
            lat += lat_change
            lng += lng_change
            coordinates.append((lat / factor, lng / factor))
    except IndexError:
        pass # just don't include the last coordinate pair...weird bug

    if geojson is True:
        coordinates = [t[::-1] for t in coordinates]

    return [list(tup) for tup in coordinates]

@csrf_exempt
def craft_runs(request):
    if request.method == 'GET':
        geoLoc = Nominatim(user_agent="GetLoc")
        city = request.GET.get('location')
        run = request.GET.get('run')
        bike = request.GET.get('bike')
        quantity = request.GET.get('quantity')
        mode = ""
        if run and mode == "checked":
            mode = "Run"
        elif bike and bike == "checked":
            mode = "Ride"
        else:
            mode = "Run"
        
        if not quantity:
            quantity = 5
        else:
            quantity = int(quantity)
    
        target = geoLoc.geocode(city) if city else SimpleNamespace(latitude=43.07, longitude=-89.4)
        distance = request.GET.get('distanceSlider')
        radius = request.GET.get('radiusSlider')
        elevation = request.GET.get('elevationSlider')# given in feet
        distance_value = int(distance) if distance else 5                # given in miles
        meters_val = int(distance_value) * 1609.344                      # strava API uses meters
        elevation_value = int(int(elevation) / 3.3)  if elevation else 100    # strava API uses meters
        radius = int(radius) if radius else 5
        upper_dist = meters_val + 10000 
        lower_dist = meters_val - 10000 
        upper_elv = elevation_value + 500 
        lower_elv = elevation_value - 500
        meters_to_miles = 0.000621371
        meters_to_feet = 3.28084
        MAPBOX_KEY = settings.MAPBOX_KEY

        # Use the filter() method with Q objects to specify the range condition
        results = Activities.objects.filter(Q(distance__gte=lower_dist) 
                                            & Q(distance__lte=upper_dist)
                                            & Q(total_elevation_gain__gte=lower_elv) 
                                            & Q(total_elevation_gain__lte=upper_elv)
                                            & Q(type=mode)
                                            & ~Q(mappolyline__exact=''))
        # sort results by best match
        results = list(results.values())
        final_results = []

        for route in results:
            # process route for map
            # BUT only add to results if the route's location is within range of the desired area
            poly = route['mappolyline']
            coords = decode(poly, geojson=True, quick=True)  # just get first coordinate pair
        
            try:   
                loc = list(reversed(coords[0]))
            except ValueError:
                continue

            target_pos = (target.latitude, target.longitude)
            distance_miles = get_distance.distance(tuple(loc), target_pos).miles
            SEARCH_THRESHOLD = 7 # don't do reverse lookup if the route is close
            if (distance_miles < int(radius)):

                # get the location since strava API tends to bug tf out and not return one
                # geopy returns "address, neighborhood, city, county, state, zip, country"
                # we just want city and state ... for now
                # also note... this is pretty slow so we really don't want to do it
                if (distance_miles > SEARCH_THRESHOLD):
                    print("reverse lookup...")
                    full_location = geoLoc.reverse(loc).address.split(", ")
                    route['location_city'] = full_location[-5] 
                    route['location_state'] = full_location[-3]
                else:
                    full_location = city.split(", ") if city else ["Madison", "Wisconsin"]
                    route['location_city'] = full_location[0] 
                    route['location_state'] = full_location[1]

                # conversions for template
                route['distance'] = round(route['distance'] * meters_to_miles, 1)
                route['total_elevation_gain'] = round(route['total_elevation_gain']*meters_to_feet)

                # get sum squared error
                error = ((route['distance']-int(distance))**2 + 0.1*(route['total_elevation_gain'])) ** 0.5
                coords = decode(poly, geojson=True)
                final_results.append([route,error,coords])  # doing this for now, since list remove isn't reliable
                                                            # for removing routes
            
        """ final preprocessing steps """
        city_only = ""
        if (city):
            city_only = city.split(",")[0]

        if mode == "Run":
            mode = "running"
        else:
            mode = "biking"

        # get the top {quantity} results
        final_results = sorted(final_results, key=lambda x: x[1])[:quantity]
        final_activities = [res[0] for res in final_results]
        lines = json.dumps([res[2] for res in final_results])

        return render(request, 
                    'home.html', 
                    {
                    'results': final_activities, 
                    'MAPBOX_KEY': MAPBOX_KEY,
                    'routes':True,
                    'lines':lines,
                    'distance':distance_value,
                    'elevation': elevation_value,
                    'center_latitude': target.latitude,
                    'center_longitude': target.longitude,
                    'zoom': 11,
                    'city': city,
                    'city_only': city_only,
                    'mode': mode,
                    'radius': radius,
                    'quantity': quantity
                    })

    else: 
        errors = request.errors
        return JsonResponse({'errors': errors}, status=400)  # Return validation errors