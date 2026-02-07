# credit: a dude on roblox named a_cemaster
import requests
import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from datetime import datetime
from time import sleep
from python.helpers import get_local_path
import time
import random
import data.config as cfg

MIN_DELAY = 5
TIMEOUT = 100
MAX_RETRIES = 100

# throttle client credit to TimorousShadow
class ThrottledClient:
    def __init__(self): # we love inits
        self.s = requests.Session()
        self._last_request_t = 0.0
            
    def _sleep_if_needed(self): # timeout
        now = time.monotonic()
        dt = now - self._last_request_t
        if dt < MIN_DELAY:
            time.sleep(MIN_DELAY - dt) # if it's requesting too fast.

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        attempt = 0
        backoff = 1.0

        while True: # lets get this bread! (request data)
            attempt += 1 # adds an attempt to the count
            self._sleep_if_needed() # if the next request is too soon, sleep that shit off
            self._last_request_t = time.monotonic() # set the last request time to this request
            
            # pray
            try:
                r = self.s.request(method, url, timeout=TIMEOUT, **kwargs)
            except (requests.Timeout, requests.ConnectionError): # fuck ass exceptions here.
                if attempt >= MAX_RETRIES: # too many tries, get vibe checked by an error
                    raise # have fun handling this one you vibe coder.
                time.sleep(backoff + random.uniform(0, 0.25)) # we are backing off because of some fuckass shit idk
                backoff = min(backoff * 2.0, 30.0) # Adding another backoff on top of the sleep function
                continue

            if r.status_code != 429 and r.status_code < 500:
                return r # yay! no rate limit

            if attempt >= MAX_RETRIES:
                r.raise_for_status()
                return r # too many reties

            # if we are getting rate limited
            retry_after = r.headers.get("Retry-After")
            try:
                wait_s = float(retry_after) if retry_after else backoff # if it gives us a retry after value at all, if not default to the backoff
            except ValueError:
                wait_s = backoff # incase the retry_after conversion just hates you

            time.sleep(wait_s + random.uniform(0, 0.25)) # lets try and finese the api here with some radomness.
            backoff = min(backoff * 2.0, 30.0) # increase the backoff for the rate limit



# Put usernames in this list to get their badge information

# Will print current amount of badges tracked if True
# Recommended if user has a lot of badges and you want to see progress
PRINT_PROGRESS = True
BATCH_PER_PRINT = 1000

def get_user_id_from_username(username: str) -> str:
    # Use the Roblox users API to get the user ID from the username
    url = f"https://users.roblox.com/v1/usernames/users"
    params = {"usernames": [username]}
    response = requests.post(url, json=params)
    data = response.json()

    # Check if the response is valid and contains the user ID field
    if response.status_code == 200 and data["data"]:
        return data["data"][0]["id"]

    raise Exception(f"Could not find the user ID for username {username}")

def check_can_view_inventory(user_id: str) -> bool:
    """
    Given a Roblox user id, check if the user can view their inventory.
    """
    url = f"https://inventory.roproxy.com/v1/users/{user_id}/can-view-inventory"
    response = requests.get(url)
    # If we get a 429 status, wait and retry with some backoff
    retry_after = 5
    while response.status_code == 429:
        print(f"{cfg.logstamp()}[Badge Graph] Rate limited. Retrying after {retry_after} seconds.")
        sleep(retry_after)
        response = requests.get(url)
        retry_after += 5

    response.raise_for_status()  # Raise an error for other non-200 responses
    data = response.json()
    return response.json()["canView"]

def fetch_badges(user_id: str) -> list[dict]:
    """
    Given a Roblox user id, get the user's badge data.
    """
    url = f"https://badges.roproxy.com/v1/users/{user_id}/badges?limit=100&sortOrder=Desc"
    badges = []
    cursor = None
    client = ThrottledClient()

    while True:
        params = {}
        if cursor:
            params['cursor'] = cursor
        response = client.request("get", url, params=params)
        data = response.json()

        for badge in data['data']:
            badges.append(badge)
            if PRINT_PROGRESS and len(badges) % BATCH_PER_PRINT == 0:
                print(f"{cfg.logstamp()}[Badge Graph] {len(badges)} badges for {user_id} requested.")

        if data['nextPageCursor']:
            cursor = data['nextPageCursor']
        else:
            break

    return badges

def convertDateToDatetime(date: str) -> datetime:
    """
    Given a timestamp string, convert to a datetime object.
    """
    milliseconds_length = len(date.split('.')[-1])

    # The string dates we get vary, so we have to sanitize to 3 places and 'Z'
    # Truncate if more than 3 places & 'Z', else pad zeroes
    if '.' in date:
        if milliseconds_length > 4:
            dotInd = date.find('.')
            date = date[:dotInd + 4] + date[-1]
        elif milliseconds_length < 4:
            date = date[:-1] + '0' * (4 - milliseconds_length) + date[-1]
    else:
        # There is no decimal portion, so we have to add it
        date = date[:-1] + ".000" + date[-1]

    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")

def fetch_award_dates(user_id: str, badges: list[dict]) -> list[str]:
    """
    Make requests to Roblox's Badge API to get user's badge awarded dates
    """
    dates = []
    badge_ids = [badge["id"] for badge in badges]
    url = f"https://badges.roproxy.com/v1/users/{user_id}/badges/awarded-dates"
    STEP = 100  # Adjust the step size as needed, we can't do too many at once
    client = ThrottledClient()
    for i in range(0, len(badge_ids), STEP):
        try:
            params = {"badgeIds": badge_ids[i:i + STEP]}
            response = client.request("get", url, params=params)

            # If we get a 429 status, wait and retry with some backoff

            response.raise_for_status()  # Raise an error for other non-200 responses

            for badge in response.json()["data"]:
                dates.append(badge["awardedDate"])
                if PRINT_PROGRESS and len(dates) % BATCH_PER_PRINT == 0:
                    print(f"{cfg.logstamp()}[Badge Graph] {len(dates)} awarded dates for {user_id} requested.")

        except Exception as e:
            print(f"{cfg.logstamp()}[Badge Graph] Error fetching data: {e}")

    return dates

def plot_cumulative_badges(username: str, user_id: str, dates: list[str]):
    """
    Graph the cumulative total of badges over time
    """
    # Sort badges by awarded date
    y_values = [convertDateToDatetime(date) for date in dates]
    y_values.sort()

    # Calculate cumulative count at each date and store into a list
    curr_count = 0
    cumulative_counts = []
    for date in y_values:
        curr_count += 1
        cumulative_counts.append(curr_count)

    # Plot the cumulative count over time
    plt.style.use('dark_background')
    plt.xlabel('Badge Earned Date')
    plt.ylabel('Total Badges')
    plt.title(f'Badges over Time for {username} ({user_id})')
    plot = plt.scatter(y_values, cumulative_counts, marker='o', alpha=0.2)

    # Set the X-axis format to 'Year' only
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())

    plt.figtext(0.05, 0.95, f"Badge Count: {len(y_values)}", ha="left", va="top", color="white")

    # Save the image, if desired. Must be ran before plt.show()
    plt.savefig(get_local_path(f"data/badgegraphs/BadgeGraph-{user_id}.png"), bbox_inches="tight")

    plot.remove()

def process_user(username: str):
    """
    Run all the functions to get the badge graph for single username
    """
    user_id = get_user_id_from_username(username)
    can_view_inventory = check_can_view_inventory(user_id)
    print(f"{cfg.logstamp()}[Badge Graph] {username}: {user_id}, Can view inventory: {can_view_inventory}")
    if not can_view_inventory:
        return
    badges = fetch_badges(user_id)
    dates = fetch_award_dates(user_id, badges)
    plot_cumulative_badges(username, user_id, dates)


