#! /usr/bin/env python
# -*- coding: utf-8 -*-

import arrow
import requests
from sys import argv
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import base64
import codecs

TIME_FORMAT = 'HH:mm'
DATETIME_FORMAT = 'DD/MM/YYYY HH:mm'

class TimeEntry(object):
    def __init__(self, start, stop, duration = 0):
        self.start = start
        self.stop = stop
        self.duration = duration

    def __str__(self):
        if self.start is not None and self.stop is not None:
            return self.start.format("HH:mm") + " " + self.stop.format("HH:mm")
        else:
            return ""

class ResumeDay(object):
    def __init__(self, date, entries, sum_time=0, interval=0):
        self.date = date
        self.entries = entries
        self.sum_time = sum_time
        self.interval = interval
        self.total_time = 0

    def __str__(self):
        interval_time_str = seconds_to_time(self.interval).format("HH:mm")
        total_time_str = seconds_to_time(self.calculate_total_time()).format("HH:mm")
        #interval_time_str = interval_time.format("HH:mm") if interval_time is not None else ""
        #total_time_str = total_time.format("HH:mm") if total_time is not None else ""
        return self.date.isoformat() + " " + str(self.entries[0]) + " " + str(self.entries[1]) + " " + interval_time_str + " " + total_time_str

    def calculate_total_time(self):
        total_time = timedelta()
        for e in self.entries:
            total_time += e.stop - e.start
        return total_time.seconds - self.interval

def seconds_to_time(seconds_time):
    hour = seconds_time // 3600
    minutes = (seconds_time % 3600) // 60
    #seconds = seconds_time % 60
    time_str = str.format("{0}:{1}", str(hour).rjust(2, '0'), str(minutes).rjust(2, '0'))
    time = arrow.get(time_str, "HH:mm")
    return time


def get_toggl_time_entries(user_token, startdate_str, stopdate_str):

    # Criar função para validar data
    try:
        startdate = datetime.strptime(startdate_str, '%d/%m/%Y%H:%M')
    except ValueError:
    	print "Data de início inválida. A data deve ser no formato dd/mm/aaaa. Ex.: 01/01/2015"
        return

    try:
    	enddate = datetime.strptime(stopdate_str, '%d/%m/%Y%H:%M')
    except ValueError:
    	print "Data de término inválida. A data deve ser no formato dd/mm/aaaa. Ex.: 31/01/2015"
        return

    toggl_url 	 = "https://www.toggl.com/api/v8/time_entries"
    #user_token 	 = "cc404a890954ed1fbf22b1896b82daa2"
    api_token	 = user_token + ":api_token"
    headers		 = {'Authorization':'Basic '+ base64.b64encode(api_token)}
    params		 = {
        'start_date': 		startdate.strftime('%Y-%m-%dT%H:%M:%S+03:00'),
        'end_date': 		enddate.strftime('%Y-%m-%dT%H:%M:%S+03:00'),
    				}

    print "Consultando toggl..."
    response = requests.get(toggl_url, headers = headers, params=params)
    if response.status_code != requests.codes.ok:
    	print "Não foi possível fazer o login. Verifique sua chave de autenticação (API Key)"
        print response
        return
    data = response.json()
    time_dict = {}
    for entry in data:
        #start = datetime.strptime(entry['start'], "%Y-%m-%dT%H:%M:%S+00:00")
        start = arrow.get(entry['start']).to("-03:00")
        stop = arrow.get(entry['stop']).to("-03:00")
        duration = entry['duration']
        date = start.date()
        tmp = TimeEntry(start, stop, duration)
        if time_dict.has_key(date):
            time_dict[date].append(tmp)
        else:
            time_dict[date] = [tmp]

    #print time_dict

    print "Resultado"
    for key in time_dict.iterkeys():
        entries = time_dict[key]
        start1 = arrow.get('2100-01-01T00:00:00+00:00')
        stop1 = arrow.get('2000-01-01T00:00:00+00:00')
        last_stop = None
        interval_sum = timedelta()
        interval = timedelta()
        maxInterval = TimeEntry(None, None, 0)

        for e in entries:
            if e.start < start1:
                start1 = e.start

            if e.stop > stop1:
                stop1 = e.stop

            if last_stop is not None:
                #TODO : Não levar em considerações os segundos
                interval = e.start - last_stop
                if interval.seconds > 80000:
                    interval = timedelta()
                if interval.seconds  >= maxInterval.duration:
                    maxInterval = TimeEntry(last_stop, e.start, interval.seconds)
                interval_sum += interval
                last_stop = e.stop

            last_stop = e.stop

        t1 = TimeEntry(start1, maxInterval.start)
        t2 = TimeEntry(maxInterval.stop, stop1)
        resume_entries = [t1, t2]
        resume = ResumeDay(start1.date(),resume_entries, interval = (interval_sum.seconds - maxInterval.duration))
        print resume
        #print start1.format("HH:mm") + " " + maxInterval.start.format("HH:mm") + " " + maxInterval.stop.format("HH:mm") + " "+ stop1.format("HH:mm") + " " + str(interval_sum.seconds - maxInterval.duration)

