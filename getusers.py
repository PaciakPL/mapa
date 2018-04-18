#!/usr/bin/env python3
"""
Script to get data from paciak and geocode it.
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import time
import requests
import os

DEBUG = True

API_TOKEN = os.environ['API_TOKEN']
API_URL = "https://paciak.pl/api/"
API_SLEEP = 1
TOKEN = {"Authorization": "Bearer {API_TOKEN}".format(API_TOKEN=API_TOKEN)}


def debug(text):
    """Debug messages"""
    if DEBUG:
        print(text)


def paciak_api_url(req):
    """Prepare discourse api call url"""
    return "{0}{1}".format(API_URL, req)


def paciak_api(url):
    """Make API call to discourse"""
    response = None
    try:
        debug("In paciak_api: {0}".format(url))
        response = requests.get(url, headers=TOKEN)
    except urllib.error.HTTPError as e:
        print("Oppss, HTTP returned: {0} with: {1}".format(e.code, e.reason))
        print("Check API settings")
        exit(1)
    except urllib.error.URLError as e:
        print("Oppss, URL error: {0}".format(e.reason))
        exit(2)

    return response


def get_users():
    """Get list of all users"""
    page_number = 1
    uid = 0
    users = list()
    while uid is not 1:
        page = "users?page={page}".format(page=page_number)
        url = paciak_api_url(page)
        debug("In get_users: {0}".format(url))
        response = paciak_api(url).text  # .decode('utf-8') - not needed anymore(?)
        response = json.loads(response)
        for user in response["users"]:
            users.append(user["userslug"])
            uid = int(user["uid"])
        page_number += 1
    return users


def get_data(users):
    """Get data about users, omit users without location"""
    users_data = list()

    for user in users:
        debug("Processing in get_data: {0}".format(user))

        data = dict()
        url = paciak_api_url("user/{0}".format(user))
        user_data = paciak_api(url).text  # .decode('utf-8') - not needed anymore(?)
        user_data = json.loads(user_data)

        if len(user_data["location"]) > 0:
            data["username"] = user_data["username"]
            data["avatar"] = user_data["picture"].replace("{size}", "32")
            data["location"] = dict()

            location = get_latlon(user_data["location"])
            if location:
                data["location"]["name"] = user_data["location"]
                data["location"]["lat"] = location[0]["lat"]
                data["location"]["lon"] = location[0]["lon"]

                debug("In get_data, location: {0}".format(location))

                users_data.append(data)
            else:
                debug("In get_data, no location for {0}".format(user))

        time.sleep(API_SLEEP)
    print(users_data)
    return users_data


def get_latlon(location):
    """Geocode location"""
    url = "https://nominatim.openstreetmap.org/search/?q={0}&format=json&limit=1".format(
        urllib.parse.quote(location))
    debug("In get_latlon: {0}".format(url))
    response = None
    try:
        response = urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        print("Geocoding HTTP error {0} with: {1}".format(e.code, e.reason))
        exit(3)
    except urllib.error.URLError as e:
        print("Geocoding URL error: {0}".format(e.reason))
        exit(4)

    response = json.loads(response.read().decode('utf-8'))

    return response


if __name__ == "__main__":
    paciak_users = get_users()
    usersdata = get_data(paciak_users)
    print(json.dumps(usersdata, indent=2))
