#! /usr/bin/env python
# -*- coding: utf-8 -*-

import arrow
import ast
from collections import OrderedDict
import requests
from sys import argv
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import base64
import codecs
import json

TIME_FORMAT = 'HH:mm'
DATE_FORMAT = 'DD/MM/YYYY'
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
    def __init__(self, date, entries, aditional_time=0, interval=0):
        self.date = date
        self.entries = entries
        self.aditional_time = aditional_time
        self.interval = interval
        self.total_time = 0

    def __str__(self):
        interval_time_str = seconds_to_time(self.interval).format("HH:mm")
        aditional_time_str = seconds_to_time(self.aditional_time).format("HH:mm")
        total_time_str = seconds_to_time(self.calculate_total_time()).format("HH:mm")
        return self.date.format(DATE_FORMAT) + " " + str(self.entries[0]) + " " + str(self.entries[1]) + " " + aditional_time_str + " " + interval_time_str + " " + total_time_str

    def as_dict(self):
        dict = {}
        dict['date'] = self.date.format(DATE_FORMAT)
        dict['entries'] = []
        if self.entries is not None:
            #dict['entries'] = [str(self.entries[0]), str(self.entries[1])]
            dict['entries'] = []
            d = {}
            if self.entries[0] is not None:
                d['start'] = self.entries[0].start.format("HH:mm")
                d['stop'] = self.entries[0].stop.format("HH:mm")
                dict['entries'].append(d)
            else:
                dict['entries'].append({'start': '00:00', 'stop':'00:00'})
            if self.entries[1] is not None:
                d = {}
                d['start'] = self.entries[1].start.format("HH:mm")
                d['stop'] = self.entries[1].stop.format("HH:mm")
                dict['entries'].append(d)
            else:
                dict['entries'].append({'start':'00:00', 'stop':'00:00'})
        dict['interval'] = seconds_to_time(self.interval).format("HH:mm")
        dict['aditional_time'] = seconds_to_time(self.aditional_time).format("HH:mm")
        dict['total_time'] = seconds_to_time(self.calculate_total_time()).format("HH:mm")
        #return json.dumps(dict, ensure_ascii=False)
        return dict

    def calculate_total_time(self):
        total_time = timedelta()
        for e in self.entries:
            if e is not None:
                total_time += e.stop - e.start
        return total_time.seconds - self.interval + self.aditional_time

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
    time_dict_tmp = {}
    for entry in data:
        horario_verao = arrow.get('2016-10-16')
        if arrow.get(entry['start']) < horario_verao:
            start = arrow.get(entry['start']).to("-03:00")
            stop = arrow.get(entry['stop']).to("-03:00")
        else:
            start = arrow.get(entry['start']).to("-02:00")
            stop = arrow.get(entry['stop']).to("-02:00")
        duration = entry['duration']
        date = start.date()
        if date >= startdate.date():
            tmp = TimeEntry(start, stop, duration)
            if time_dict_tmp.has_key(date):
                time_dict_tmp[date].append(tmp)
            else:
                time_dict_tmp[date] = [tmp]

    result = []

    # Preenchimento dos dias que não houve registros
    diff_date = enddate - startdate
    for i in range(diff_date.days + 1):
        tmp_key = (startdate + timedelta(days=i)).date()
        if not time_dict_tmp.has_key(tmp_key):
            time_dict_tmp[tmp_key] = None

    time_dict = OrderedDict(sorted(time_dict_tmp.items(), key=lambda t: t[0]))
    for key, value in time_dict.items():
        entries = value
        start1 = arrow.get('2100-01-01T00:00:00+00:00')
        stop1 = arrow.get('2000-01-01T00:00:00+00:00')
        last_stop = None
        interval_sum = timedelta()
        interval = timedelta()
        maxInterval = TimeEntry(None, None, 0)

        if entries is None:
            resume = ResumeDay(arrow.get(key.isoformat()), [None, None])
            result.append(resume.as_dict())
            continue

        for e in entries:
            if e.start < start1:
                start1 = e.start

            if e.stop > stop1:
                stop1 = e.stop

            if last_stop is not None:
                interval = e.start - last_stop
                # Tratamento para quando houver interseção de horário
                if interval.seconds > 80000:
                    interval = timedelta()
                if interval.seconds  >= maxInterval.duration:
                    maxInterval = TimeEntry(last_stop, e.start, interval.seconds)
                interval_sum += interval
                last_stop = e.stop

            last_stop = e.stop

        #TODO : Quando houver configuração de divisão de horário, levar em conta
        t1 = None
        t2 = None
        if maxInterval.start is None and maxInterval.stop is None:
            t1 = TimeEntry(start1, stop1)
            tMax = t1
        else:
            t1 = TimeEntry(start1, maxInterval.start)
            t2 = TimeEntry(maxInterval.stop, stop1)
            tMax = t2
        horario_verao = arrow.get('2016-10-16')
	if arrow.get(tMax.stop.date()) < horario_verao:
            meia_noite = arrow.get(tMax.stop.date().isoformat() + " 00:00-03:00")
        else:
            meia_noite = arrow.get(tMax.stop.date().isoformat() + " 00:00-02:00")
        aditional_time = timedelta()
        if (meia_noite - tMax.stop).seconds > 70000:
            aditional_time = tMax.stop - meia_noite
            tMax.stop = meia_noite

        resume_entries = [t1, t2]
        resume = ResumeDay(start1,resume_entries, aditional_time = aditional_time.seconds, interval = (interval_sum.seconds - maxInterval.duration))
        result.append(resume.as_dict())

    def obj_default(obj):
        return obj

    result_str = json.dumps(result, default=obj_default)
    return ast.literal_eval(result_str)
