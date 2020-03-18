#!/usr/bin/env python3
import grequests
import requests

from flask import Flask, jsonify
from datetime import datetime
from bs4 import BeautifulSoup

app = Flask(__name__, static_url_path="")
currentYear = datetime.today().year
baseurl = "https://github.com/"


@app.route('/contributions/<username>', methods=['GET'])
def getAllCommits(username):
    if isValidUser(username) == False:
        return jsonify("User does not exist")

    contributions = []
    userCreationYear = getUserCreationYear(username)
    years = []

    for i in range(userCreationYear, currentYear+1, 1):
        years.append(i)

    urls = fillUrls(username, years)
    results = grequests.map((grequests.get(u) for u in urls), size=len(years))

    for i in results:
        soup = BeautifulSoup(i.content, 'html.parser')
        day_elems = soup.find_all('rect')

        for day_elem in day_elems:
            tempDate = datetime.strptime(
                day_elem.attrs['data-date'], '%Y-%m-%d')
            if (tempDate <= datetime.today()):
                contributions.append({
                    'date': day_elem.attrs['data-date'],
                    'color': day_elem.attrs['fill'],
                    'count': int(day_elem.attrs['data-count']),
                    'dayOfWeek': getWeekDay(day_elem.attrs['data-date'])
                })
            else:
                break

    return jsonify({'contributions': contributions})


def fillUrls(username, yearsToGet):
    urls = []

    for year in yearsToGet:
        otherUrl = "?tab=overview&from={}-01-01&to={}-12-31".format(year, year)
        urls.append(baseurl + "/" + username + otherUrl)

    return urls


def getWeekDay(dateToAnalyze):
    curDate = datetime.strptime(dateToAnalyze, '%Y-%m-%d').date()
    return (curDate.weekday()+1) % 7


@app.route('/todayCount/<username>', methods=['GET'])
def getDailyCommit(username):
    if isValidUser(username) == False:
        return jsonify("User does not exist")

    otherUrl = "?tab=overview&from={}-01-01&to={}-12-31".format(
        currentYear, currentYear)
    page = requests.get(baseurl + username + otherUrl)

    soup = BeautifulSoup(page.content, 'html.parser')
    day_elems = soup.find_all('rect')
    contributions = [{
        'Error': "Data Not Found",
    }]

    for day_elem in day_elems:
        tempDate = datetime.strptime(
            day_elem.attrs['data-date'], '%Y-%m-%d').date()
        todayDate = datetime.today().date()

        if (tempDate == todayDate):
            contributions.clear()
            contributions.append({
                'date': day_elem.attrs['data-date'],
                'color': day_elem.attrs['fill'],
                'count': int(day_elem.attrs['data-count']),
                'dayOfWeek': getWeekDay(day_elem.attrs['data-date'])
            })

    return jsonify({'today': contributions})


def getUserCreationYear(username):
    """
    So theres an api limit on this so we need to manually parse
    """
    r = requests.get("https://api.github.com/users/{}".format(username))
    data = r.json()
    return int(data['created_at'].split("-")[0])


def isValidUser(username):
 # There's an API limit that I'm hitting for some reason
 # SO essentially, we need to manually parse the github site to see if they are
 # a valid user or not because the api is being weird
    x = requests.get("https://github.com/".format(username))

    print(x.status_code)
    return True


def trunc_datetime(someDate):
    return someDate.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


if __name__ == '__main__':
    app.run(debug=False)