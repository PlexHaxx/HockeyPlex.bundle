# HockeyPlex
# HockeyStreams.com Plugin for Plex Media Center
# by Mark Freden m@sitticus.com
# Version .05
# Oct 23, 2013

APP_KEY = "plexApp"
TOKEN = ""

TITLE = "HockeyPlex .05"
PREFIX = "/video/hockeyplex"

ART = "art-default.jpg"
ICON = "icon-default.png"
ICON_LIVE = ""
ICON_LOCATIONS = "server-globe.png"
ICON_ONDEMAND = ""

TITLE_GETLOCATIONS = "Server: "
TITLE_LIVEGAMES = "Live Games"
TITLE_LOGIN = "Log In"
TITLE_ONDEMANDGAMES = "On Demand"
TITLE_PREFERENCES = "Preferences"
TITLE_PREVIEW = "Preview"

URL_GAMEOFF = "http://repo.hockeystreams.com/hockeyplex/vids/GAME_OFF.m4v"
URL_LIVEGAMES = "https://api.hockeystreams.com/GetLive?token=%s"
URL_LOCATIONS = "https://api.hockeystreams.com/GetLocations"
URL_LOGIN = "https://api.hockeystreams.com/Login"
URL_ONDEMANDDATES = "https://api.hockeystreams.com/GetOnDemandDates?token=%s"
URL_ONDEMANDGAMES = "https://api.hockeystreams.com/GetOnDemand?date=%s&token=%s"
URL_ONDEMANDSTREAM = "https://api.hockeystreams.com/GetOnDemandStream?id=%s&token=%s"
URL_PH = "http://sitticus.com/hockeyplex/ph.php"
URL_PREVIEW = "http://s.hscontent.com/preview/previewHD_hs.m3u8?token="
URL_REPO = "http://repo.hockeystreams.com/hockeyplex/"
URL_LOGOREPO = URL_REPO + "logos/"
URL_ARENAREPO = URL_REPO + "arenas/"

###################################################################################################
# Import date and time modules for FormatDate
## may be able to use builtin Datetime
from datetime import date, timedelta
import time

# Import urlparse for encodeUrlToken
from urlparse import urlparse

###################################################################################################
def Start():

    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = TITLE
    DirectoryObject.thumb = R(ICON)

    # HTTP.ClearCookies()
    # HTTP.ClearCache()
    # HTTP.CacheTime = 1
    # HTTP.Headers["User-Agent"] = "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_0 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7"

    ValidatePrefs()

###################################################################################################
@handler(PREFIX, TITLE, thumb=ICON, art=ART)
def MainMenu():

    oc = ObjectContainer(no_cache=True)

    # Only show menus if TOKEN has been successfully set
    if TOKEN != None:
        oc.add(DirectoryObject(
            key=Callback(LiveGamesMenu),
            title=TITLE_LIVEGAMES,
            thumb=R(ICON_LIVE)
        ))
        oc.add(DirectoryObject(
            key=Callback(OnDemandDatesMenu),
            title=TITLE_ONDEMANDGAMES,
            thumb=R(ICON_ONDEMAND)
        ))

        oc.add(PrefsObject(
            title=TITLE_PREFERENCES
        ))

    else:
        oc.add(PrefsObject(
            title=TITLE_LOGIN
        ))

        oc.add(StreamM3U8("0", TITLE_PREVIEW, URL_PREVIEW, "", "", ""))

    return oc

###################################################################################################
@route(PREFIX + '/livegamesmenu')
def LiveGamesMenu():

    Log("Getting Live Games Menu")

    # Get Prefs
    serverLocation = Prefs["serverlocation"]

    Log(" Pref - Serverlocation: " + serverLocation)

    title = TITLE_LIVEGAMES
    url = URL_LIVEGAMES % TOKEN

    # Add ServerLocation if specified in Prefs
    if (serverLocation != "Automatic"):
        # serverLocation = urllib.quote_plus(serverLocation)
        url = url + "&location=" + String.Quote(serverLocation, True)

    oc = ObjectContainer(title2=title, no_cache=True)

    # Loop thru videos array returned from GetLiveGames
    for video in GetLiveGames(url):
        (game_id, title, srcUrl, logo, arena, summary) = video

        # Log(" Adding to Menu: " + str(game_id))

        # If there was an error, display it
        if game_id == 0:

            Log(" ERROR Adding to Menu: " + title)

            return (ObjectContainer(header="HockeyStreams Error", message=title))
        else:
            oc.add(StreamM3U8(game_id, title, srcUrl, logo, arena, summary))

            Log(" Added to Menu: " + str([game_id, title, srcUrl, logo, arena, summary]))

    return oc

###################################################################################################
@route(PREFIX + '/getlivegames')
def GetLiveGames(url):

    Log("Getting Live Games")

    # Set up our array to return
    videos = []

    # Get Prefs
    # streamType = Prefs["streamtype"]
    shortNames = Prefs["shortnames"]
    serverLocation = Prefs["serverlocation"]

    #Log (" Pref - StreamType: " + streamType)
    Log(" Pref - ShortNames: " + shortNames)
    # Log(" Pref - Serverlocation: " + serverLocation)

    # Get data from server
    game_json = JSON.ObjectFromURL(url)

    Log(" Got Live Games JSON - Status: " + game_json["status"])

    if game_json["status"] == "Success":

        # Get Prefs
        leagueFilter = Prefs["leaguefilter"]
        quality = Prefs["quality"]

        # Loop thru each to build videos meta
        for video in game_json["schedule"]:

            # Set flag to not add video
            addVid = False

            # Check if league filter is on and filter results
            if leagueFilter == "All":
                addVid = True
            else:
                if video["event"] == leagueFilter:
                    addVid = True
                else:
                    Log(" Filtering Out Game ID: " + video["id"])

            # If the video should be added, build the meta
            if addVid:

                game_id = video["id"]

                Log(" Adding Game ID: " + game_id)

                awayTeam = ""
                homeTeam = ""
                startTime = ""
                feedType = ""

                # If the game isn't on yet, set to gameoff vid
                if video["isPlaying"] == 0:
                    srcUrl = URL_GAMEOFF + "?" + game_id # Add game_id so Plex thinks its a unique URL and reads thumb

                # Set vid quality chosen in prefs
                elif video["isHd"] == "1" and quality == "High":
                    # if streamType == "Live":# and video["TrueLiveHD"]:
                    #     srcUrl = video["TrueLiveHD"]
                    # else:
                    srcUrl = video["hdUrl"]
                else:
                    # if streamType == "Live":# and video["TrueLiveSD"]:
                    #     srcUrl = video["TrueLiveSD"]
                    # else:
                    srcUrl = video["sdUrl"]

                # Encode the URL
                srcUrl = encodeUrlToken(srcUrl)

                # # Add ServerLocation if specified in Prefs
                # if (serverLocation != "Automatic"):
                #     # serverLocation = urllib.quote_plus(serverLocation)
                #     srcUrl = srcUrl + "&location=" + String.Quote(serverLocation, True)

                # Set up home and away team names
                if video["awayTeam"]: awayTeam = video["awayTeam"]
                if video["homeTeam"]: homeTeam = video["homeTeam"]

                # Set up arena pic name (have to do it before "vs" gets added)
                arena = homeTeam + " Arena.jpg"

                # Add "vs" if there is a home and away team
                if homeTeam: homeTeam = " vs " + homeTeam

                # Set up logo pic name
                logo = awayTeam + homeTeam + " Logo.png"

                #Player Indicator went here

                if video["startTime"]: startTime = "Start Time: " + video["startTime"]
                if video["period"]: startTime = video["period"]
                if video["feedType"]: feedType = " - " + video["feedType"]

                # Put the start time & server location in the summary area
                summary = startTime + "\n" + serverLocation + " Server"

                # If shortNames pref is on
                if shortNames == "On" and homeTeam:
                    if awayTeam: awayTeam = awayTeam.split()[-1]
                    if homeTeam: homeTeam = " vs " + homeTeam.split()[-1]

                # Add playing indicator if game-on (maybe take this out)
                if video["isPlaying"] == 1: awayTeam = ">" + awayTeam

                # Build the title
                title = awayTeam + homeTeam + feedType

                if srcUrl:
                    videos.append([game_id, title, srcUrl, logo, arena, summary])
                    Log(" Added: " + str([game_id, title, srcUrl, logo, arena, summary]))
                else:
                    Log(" Didn't Add [No URL]: " + game_id + ", " + title)
    else:

        Log(" Get Live Games ERROR - " + game_json["msg"])

        # Send back an empty video with the Failed message so we can display a dialog
        if game_json["status"] == "Failed":
            videos.append([0, game_json["msg"], "", "", "", ""])

    return videos

###################################################################################################
@route(PREFIX + '/ondemanddatesmenu')
def OnDemandDatesMenu():

    Log("Getting OnDemand Dates Menu")

    oc = ObjectContainer(title2="On Demand Dates", no_cache=True)

    # Read the dates data from the server
    url = URL_ONDEMANDDATES % TOKEN
    json = JSON.ObjectFromURL(url)

    Log(" Got Dates Menu JSON - Status: " + json["status"])

    # Make sure there wasn't an error
    if json["status"] == "Success":

        # Loop thru the array of dates return from the server
        for gameDate in json["dates"]:

            if gameDate: # Make sure it's not empty
                oc.add(DirectoryObject(
                    key=Callback(OnDemandGamesMenu, gameDate=gameDate),
                    title=FormatDate(gameDate),
                    thumb=R(ICON_ONDEMAND)
                ))

                Log(" Added " + FormatDate(gameDate))

            else:
                Log(" Empty Date")
    else:

        Log(" Dates Menu ERROR - Status: " + json["status"] + " - " + json["msg"])

        # Show popup Error
        return (ObjectContainer(header="HockeyStreams Error",
                                message=json["msg"]))

    return oc

###################################################################################################
@route(PREFIX + '/ondemandgamesmenu')
def OnDemandGamesMenu(gameDate):

    Log("Getting OnDemand Games Menu")

    title = "On Demand Games For " + gameDate
    url = URL_ONDEMANDGAMES % (gameDate, TOKEN)

    oc = ObjectContainer(title2=title, no_cache=True)

    # Loop thru the array return by GetOnDemandGames
    for video in GetOnDemandGames(url):
        (game_id, title, logo, arena, summary) = video

        Log(" Adding To Menu: " + str(video))

        oc.add(DirectoryObject(
            key=Callback(OnDemandStreamMenu, game_id=game_id, title=title, logo=logo, arena=arena, summary=summary),
            title=title,
            thumb=URL_LOGOREPO + logo,
            art=URL_ARENAREPO + arena,
            summary=summary
        ))

    return oc

###################################################################################################
@route(PREFIX + '/getondemandgames')
def GetOnDemandGames(url):

    Log("Getting OnDemand Games")

    videos = []

    # Get Prefs
    leagueFilter = Prefs["leaguefilter"]
    shortNames = Prefs["shortnames"]

    Log(" Pref - LeagueFilter: " + leagueFilter)
    Log(" Pref - ShortNames: " + shortNames)

    # Get data from server
    game_json = JSON.ObjectFromURL(url)

    Log(" Got Game JSON - Status: " + game_json["status"])

    if "ondemand" in game_json:

        for video in game_json["ondemand"]:

            # If there isn't an iStream, don't list it
            if video["isiStream"] == 1:

                # Don't add any games until they pass the tests
                addVid = False

                # Check if league filter is on and filter results
                if leagueFilter == "All":
                    addVid = True
                else:
                    if video["event"] == leagueFilter:
                        addVid = True
                    else:
                        Log(" LeagueFilter Skipped Game ID: " + video["id"])

                # If the video should be added, build meta and add to videos list
                if addVid:

                    game_id = video["id"]

                    Log(" Adding Game ID: " + game_id)

                    awayTeam = ""
                    homeTeam = ""
                    summary = ""
                    feedType = ""

                    # Set up home and away teams
                    if video["awayTeam"]: awayTeam = video["awayTeam"]
                    if video["homeTeam"]: homeTeam = video["homeTeam"]

                    # Set up arena pic name (have to do it before "vs" gets added)
                    if homeTeam:
                        arena = homeTeam + " Arena.jpg"
                    else:
                        # If it's a single event
                        arena = awayTeam + " Arena.jpg"

                    # Add "vs" if there is a home and away team
                    if homeTeam: homeTeam = " vs " + homeTeam

                    # Set up logo pic name
                    logo = awayTeam + homeTeam + " Logo.png"

                    # Add the feedType with a dash
                    if video["feedType"]: feedType = " - " + video["feedType"]

                    # If shortNames pref is on
                    if shortNames == "On" and homeTeam:
                        if awayTeam: awayTeam = awayTeam.split()[-1]
                        if homeTeam: homeTeam = " vs " + homeTeam.split()[-1]

                    # Built the title
                    title = awayTeam + homeTeam + feedType

                    videos.append([game_id, title, logo, arena, summary])

                    Log(" Added Game: " + game_id + ", " + title + ", " + logo + ", " + arena + ", " + summary)

            else:
                Log(" No iStream URL for Game ID: " + video["id"])

    return videos

###################################################################################################
@route(PREFIX + '/ondemandstreammenu')
def OnDemandStreamMenu(game_id, title, logo, arena, summary):

    Log("Getting OnDemand Stream")

    # Get Prefs
    quality = Prefs["quality"]
    serverLocation = Prefs["serverlocation"]

    Log(" Pref - Quality: " + quality)
    Log(" Pref - Serverlocation: " + serverLocation)

    # Add ServerLocation if specified in Prefs
    if (serverLocation == "Automatic"):
        url = URL_ONDEMANDSTREAM % (game_id, TOKEN)
    else:
        url = URL_ONDEMANDSTREAM % (game_id, TOKEN + "&location=" +  String.Quote(serverLocation, True))

    Log(" URL: "+url)

    # Get game data from server
    game_json = JSON.ObjectFromURL(url)

    Log(" Got Stream JSON - Status: " + game_json["status"])

    oc = ObjectContainer(title2=title, no_cache=True)

    summary = serverLocation + " Server"

    homeTeam = game_json["homeTeam"]
    awayTeam = game_json["awayTeam"]

    homeHighlights = game_json["highlights"][0]["homeSrc"]
    awayHighlights = game_json["highlights"][0]["awaySrc"]
    homeCondensed = game_json["condensed"][0]["homeSrc"]
    awayCondensed = game_json["condensed"][0]["awaySrc"]
    if game_json["HDstreams"][0]["src"]: HD = game_json["HDstreams"][0]["src"]
    if game_json["SDstreams"][0]["src"]: SD = game_json["SDstreams"][0]["src"]

    # Encode the URLs
    HD = encodeUrlToken(HD)
    SD = encodeUrlToken(SD)

    if homeTeam:
        gameName = "Full Game"
    else:
        gameName = "Watch " + awayTeam

    # Set vid quality chosen in prefs
    if HD and quality == "High":
        oc.add(StreamM3U8(game_id, gameName, HD, logo, arena, summary))
    else:
        oc.add(StreamM3U8(game_id, gameName, SD, logo, arena, summary))

    # If the home and away condensed feeds are the same, don't bother listing both
    if homeCondensed == awayCondensed and homeCondensed != "" and awayCondensed != "":
        oc.add(StreamM3U8(game_id, "Condensed Game", homeCondensed, logo, arena, summary))
    else:
        if homeCondensed:
            oc.add(StreamM3U8(game_id, homeTeam + " Condensed Game", homeCondensed, logo, arena, summary))
        if awayCondensed:
            oc.add(StreamM3U8(game_id, awayTeam + " Condensed Game", awayCondensed, logo, arena, summary))

    # If the home and away highlight feeds are the same, don't bother listing both
    if homeHighlights == awayHighlights and homeHighlights != "" and awayHighlights != "":
        oc.add(StreamM3U8(game_id, "Highlights", homeHighlights, logo, arena, summary))
    else:
        if homeHighlights:
            oc.add(StreamM3U8(game_id, homeTeam + " Highlights", homeHighlights, logo, arena, summary))
        if awayHighlights:
            oc.add(StreamM3U8(game_id, awayTeam + " Highlights", awayHighlights, logo, arena, summary))

    return oc

###################################################################################################
@route(PREFIX + '/streamm3u8')
def StreamM3U8(game_id, title1, url, thumb, art, summary, include_container=False):

    Log("StreamM3U8 Game: " + str([game_id, title1, url, thumb, art, summary]))

    vco = VideoClipObject(key=Callback(StreamM3U8, game_id=game_id, title1=title1, url=url, thumb=thumb, art=art, summary=summary, include_container=True),
        rating_key=game_id,
        title=title1,
        art=URL_ARENAREPO + art,
        thumb=URL_LOGOREPO + thumb,
        summary=summary,
        items=[
            MediaObject(
                optimized_for_streaming=True,
                parts=[
                    PartObject(key=HTTPLiveStreamURL(url=url))
                ]
            )
        ]
    )

    if include_container:
        return ObjectContainer(objects=[vco])
    else:
        return vco

###################################################################################################
@route(PREFIX + '/encodeurltoken')
def encodeUrlToken(url):

    # Encode the token param so it doesn't fail on 3rd party/web devices
    parsed = urlparse(url)
    encodedToken = String.Quote(parsed[4], True)
    # encodedToken = encodedToken.replace('%3D', '=', 2)

    encUrl = parsed[0] + '://' + parsed[1] + parsed[2] + "?" + encodedToken

    return encUrl

###################################################################################################
@route(PREFIX + '/validateprefs')
def ValidatePrefs():

    Log("Validating Prefs")

    global TOKEN

    # When prefs get saved, update Token
    TOKEN = GetToken()
    HTTP.Request(URL_PH,{"user":Prefs["username"],"platform":Platform.OS})

    # Assume there was an error if we receive None
    if TOKEN == None:
        Log("ERROR Validating Prefs")

        # Show Error popup
        return ObjectContainer(header="HockeyStreams.com Login Error",
                               message="Make sure your username and password are correct.")

    return

###################################################################################################
@route(PREFIX + '/gettoken')
def GetToken():

    Log("Getting Token")

    # Get the username and pass from the prefs
    user = Prefs["username"]
    password = Prefs["password"]

    data = {"username": user, "password": password, "key": APP_KEY}

    # Get the token from HS Login API
    try:
        Log(" Logging In")

        json = JSON.ObjectFromURL(URL_LOGIN, data)
        ## How can I get the HTTP Error and the json?

        Log(" Got User Token " + String.Quote(json["token"], True))

        return String.Quote(json["token"], True)

    except:

        Log("ERROR Getting Token")

        return None

###################################################################################################
@route(PREFIX + '/formatdate')
def FormatDate(theDate):

    # Get and make today and yesterday strings for comparison to theDate
    today = date.today()
    todayStr = today.strftime("%m/%d/%Y")
    yesterday = today - timedelta(1)
    yesterdayStr = yesterday.strftime("%m/%d/%Y")

    # If theDate is today or tomorrow return that
    if theDate == todayStr:
        return "Today"
    elif theDate == yesterdayStr:
        return "Yesterday"
    else:
        # Convert the text to a time obj
        c = time.strptime(theDate, "%m/%d/%Y")

        if DateDiff(todayStr, theDate) > 7:
            # Get day item and add suffix
            day = c[2]
            if 4 <= day <= 20 or 24 <= day <= 30:
                suffix = "th"
            else:
                suffix = ["st", "nd", "rd"][day % 10 - 1]

            # Format into a readable format, Day the Number of Month, Year
            formatedDate = time.strftime("%A the %d" + suffix + " of %B, %Y", c)

            # Strip any leading zeros from the day
            formatedDate = formatedDate.replace(" 0", " ")
        else:
            formatedDate = time.strftime("%A", c)

        return formatedDate

###################################################################################################
@route(PREFIX + '/datediff')
def DateDiff(date1, date2):

    # Get the day difference between 2 dates

    timeString1 = date1 + " 12:00:00AM"
    timeTuple1 = time.strptime(timeString1, "%m/%d/%Y %I:%M:%S%p")

    timeString2 = date2 + " 12:00:00AM"
    timeTuple2 = time.strptime(timeString2, "%m/%d/%Y %I:%M:%S%p")

    time_difference = time.mktime(timeTuple1) - time.mktime(timeTuple2)

    return time_difference / (60.0 * 60) / 24