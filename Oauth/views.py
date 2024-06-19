from django.shortcuts import render
from django.shortcuts import redirect
from django.db.utils import DataError
import requests
import polyline
import json
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import Activities
from datetime import datetime
import time
import urllib.parse

def login(request):
    return render(request, 'login.html')

def date_to_epoch(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    epoch_time = int(time.mktime(dt.timetuple()))
    return epoch_time

@csrf_exempt
def strava_callback(request, path=''):
    code = request.GET.get('code')
    print(request)
    MAPBOX_KEY = settings.MAPBOX_KEY

    if code:
        access_token = exchange_code_for_token(code)
        state = request.GET.get('state')
        state_params = state.split("$")
        print(state_params)
        start_date_epoch = date_to_epoch(state_params[1]) if state_params[1] else None
        end_date_epoch = date_to_epoch(state_params[2]) if state_params[2] else None
        activity_type = state_params[3]
        per_page = state_params[4] if state_params[4] else 30
        page_num = state_params[5] if state_params[5] else 1
        print(start_date_epoch, end_date_epoch, per_page, page_num)
        
        token = access_token["access_token"]
        url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {
        'before': end_date_epoch,
        'after': start_date_epoch,
        'per_page': per_page,
        'page': page_num
        }

        response = requests.get(url, params=params, headers=headers).json()
        
        if response:
            for activity in response:
                if activity['map'] == None or activity['map']['summary_polyline'] == None:
                    continue
                # ideally get rid of this
                try:
                    add_to_db(activity)
                except DataError:
                    pass
            """
            activity['map']['summary_polyline'] = polyline.decode(activity['map']['summary_polyline'], geojson=True)
            activity['map']['summary_polyline'] = [list(tup) for tup in activity['map']['summary_polyline']]
            poly = response[0]['map']['summary_polyline']
            coords = polyline.decode(poly, geojson=True)
            coords = [list(tup) for tup in coords]
            json_coords = json.dumps(coords)
            """
        
    return render(request, 'home.html', 
                            {
                            'MAPBOX_KEY': settings.MAPBOX_KEY,
                            'routes':False,
                            'center_longitude': 0,
                            'center_latitude': 0,
                            'zoom': 1
                            })

def to_homepage(request, path=''):
    return render(request, 'home.html', 
                            {
                            'MAPBOX_KEY': settings.MAPBOX_KEY,
                            'routes':False,
                            'center_longitude': 0,
                            'center_latitude': 0,
                            'zoom': 1,
                            'distance':5,
                            'elevation': 50,
                            'radius': 5,
                            'quantity': 5
                            })


def exchange_code_for_token(authorization_code):
    token_url = 'https://www.strava.com/oauth/token'
    client_id = settings.STRAVA_CLIENT_ID
    client_secret = settings.STRAVA_CLIENT_SECRET
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': authorization_code,
        'grant_type': 'authorization_code'
    }
    res = requests.post(token_url, data=payload)
    
    if res.status_code == 200:
        access_token = res.json()
        return access_token
    else:
        return None

def strava_signon(request):
    return render(request, 'upload.html')

def strava_redirect(request):
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    activity_type = request.POST.get('activity_type')
    per_page = request.POST.get('per_page', 30)
    page_num = request.POST.get('page_num', 1)
    state = urllib.parse.urlencode({
        'start_date': "$"+start_date+"$"+end_date+"$"+activity_type+"$"+per_page+"$"+page_num
    })

    route = (
        'https://www.strava.com/oauth/authorize?client_id=' + str(settings.STRAVA_CLIENT_ID) +
        '&response_type=code&redirect_uri=' + settings.REDIRECT + 'exchange_token' +
        '&approval_prompt=force&scope=activity:read_all' +
        '&state=' + state
    )
    print(route)
    return redirect(route)


def add_to_db(activity):
    if not Activities.objects.filter(athlete_id=activity["athlete"]["id"], activity_id=activity["id"]).exists():
            entry = Activities(athlete_id=activity["athlete"]["id"], activity_id=activity["id"], name=activity["name"], distance=activity["distance"], total_elevation_gain=activity["total_elevation_gain"], type=activity["sport_type"], location_city=activity["location_city"], location_state=activity["location_state"], location_country=activity["location_country"], mapid=activity["map"]["id"], mappolyline=activity["map"]["summary_polyline"], mapresource_state=activity["map"]["resource_state"], upload_id=activity["upload_id"])
            entry.save()
            entry.save(force_update=True)
    else:
        pass