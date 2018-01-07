from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

import googlemaps

from match_texts import MAY_12_MATCHES
from gmaps_auth import GMAPS_KEY

gmaps = googlemaps.Client(key=GMAPS_KEY)


def _get_url_content(url):
    response = requests.get(url)
    assert response.content
    return response.content


def init_data():
    global match_infos, match_documents
    match_infos = {}
    match_documents = {}


def get_match_info(search_string):
    match_url = f'https://www.google.co.uk/search?q={quote_plus(search_string)}+May+12'
    document = BeautifulSoup(_get_url_content(match_url), 'html.parser')
    smart_box = document.find(class_='_Fc')
    if not smart_box:
        return None, document

    league, start_time, location, *_ = smart_box.children
    return dict(
        league=league.text,
        start_time=start_time.text,
        location=location.text,), None

def get_route_info(destination, travel_mode='transit'):
    try:
        dirs = gmaps.directions('munich', destination, mode=travel_mode)
    except googlemaps.exceptions.ApiError as e:
        print(e, destination)
        return {'distance': None, 'duration': None}

    if not dirs:
        if travel_mode == 'transit':
            # If transit isn't available, record driving distance
            # (but not duration, so we can easily rule out)
            route_info = get_route_info(destination, travel_mode='driving')
            route_info.update(duration=None)
            return route_info
        else:
            return {'distance': None, 'duration': None}

    first_leg = dirs[0]['legs'][0]

    return {'distance': first_leg['distance']['text'], 'duration': first_leg['duration']['text']}


def fetch_all_match_infos():
    global match_infos, match_documents

    for match in MAY_12_MATCHES.split('\n'):
        if not match:
            continue

        if match in match_infos:
            continue

        match_info, match_document = get_match_info(match)

        if not match_info:
            match_infos[match] = None
            match_documents[match] = match_document
            print('X No smartbox for', match)
            continue

        match_infos[match] = match_info

def fetch_all_route_infos():
    global match_infos, match_documents

    for match_name, match_info in match_infos.items():
        if not match_info or not match_info['location']:
            continue

        if match_info.get('distance'):
            # If we've already found how long it is between places, don't look up again
            continue

        match_info.update(get_route_info(match_info['location']))
        print_match(match_name, match_info)


def print_match(match_name, match_info):
    print(f'{match_name} ({match_info["league"]}): {match_info["location"]} ({match_info["distance"]}, {match_info["duration"]})')


def find_short_routes():
    global match_infos

    for match_name, match_info in match_infos.items():
        if not match_info:
            continue

        duration = match_info.get('duration')
        if not duration:
            continue

        # Limit to things under 2 hours away
        if 'hours' in duration:
            continue

        print(f'{match_name} ({match_info["league"]}),{match_info["location"].replace(",", ";")},{match_info["duration"]},{match_info["start_time"].replace(",", "")}')


# init_data()
# fetch_all_match_infos()
# fetch_all_route_infos()
# find_short_routes()
