import os
import re
from glob import glob
from urllib.request import urlopen, urlretrieve
from time import time
from zipfile import ZipFile
from itertools import combinations
from collections import defaultdict
from copy import deepcopy
import sys


def update_tsv_export(reporthook=None):
    """If export is missing or not current, download the current one.
       Returns True iff the export was updated."""

    # Is export file missing or older than 10 minutes?
    here = glob('WCA_export*_*.tsv.zip')
    if not here or time() - os.stat(max(here)).st_mtime > 10 * 60:

        # What's the current export on the WCA site?
        base = 'https://www.worldcubeassociation.org/results/misc/'
        try:
            with urlopen(base + 'export.html') as f:
                current = re.search(r'WCA_export\d+_\d+.tsv.zip',
                                    str(f.read())).group(0)
        except:
            print('failed looking for the newest export')
            return

        # Download if necessary, otherwise mark local as up-to-date
        if not os.path.isfile(current):
            if not reporthook:
                print('downloading export', current, '...')
            urlretrieve(base + current, current, reporthook)
            for h in here:
                if h != current:
                    os.remove(h)
            return True
        else:
            os.utime(max(here))


def prepair_data():
    global all_persons, event_names, all_averages, countries

    with ZipFile(max(glob('WCA_export*_*.tsv.zip'))) as zf:
        def load(wanted_table, wanted_columns):
            with zf.open('WCA_export_' + wanted_table + '.tsv') as tf:
                column_names, *rows = [line.split('\t') for line
                                       in tf.read().decode().splitlines()]
                columns = []
                for name in wanted_columns.split():
                    i = column_names.index(name)
                    column = [row[i] for row in rows]
                    try:
                        column = list(map(int, column))
                    except:
                        pass
                    columns.append(column)
                return list(zip(*columns))

        all_persons = list((id, name, countryId) for id, subid, name, countryId
                           in load('Persons', 'id subid name countryId')
                           if subid == 1)
        event_names = dict((id, name) for id, name
                           in load('Events', 'id name'))
        all_averages = load('RanksAverage', 'personId eventId best')
        countries = [country[0] for country in load('Countries', 'id')]


class TopTeams:
    def __init__(self, max_team_count):
        self.max_team_count = max_team_count
        self.teams = []

    def add(self, team, times, event_division):
        # check, if there is a team consisting of the same same people
        for i, (team2, times2, event_division2) in enumerate(self.teams):
            if set(team) == set(team2):
                if sorted(times, reverse=True) < sorted(times2, reverse=True):
                    self.teams[i] = (deepcopy(team), deepcopy(times),
                                     deepcopy(event_division))
                break
        else:
            self.teams.append((deepcopy(team), deepcopy(times),
                               deepcopy(event_division)))
        # sort teams by times and if necessary remove the last entry
        self.teams.sort(key=lambda t: sorted(t[1], reverse=True))
        if len(self.teams) > self.max_team_count:
            self.teams.pop()

    def get_worst_time(self):
        if len(self.teams) > 0:
            return self.teams[len(self.teams) - 1][1]
        else:
            return [float('inf')]

    def storage_full(self):
        return len(self.teams) == self.max_team_count

    def printTeams(self):
        global persons, event_names
        for team, times, event_division in self.teams:
            zipped_team = list(zip(team, times, event_division))
            zipped_team.sort(key=lambda t: t[1], reverse=True)
            for person, t, events in zipped_team:
                event_str = ', '.join([event_names[event] for event in events])
                time_str = ' (' + str(t/100) + ' seconds)'
                try:
                    print(persons[person] + ': ' + event_str + time_str)
                except:
                    print(person + ': ' + event_str + time_str)
            print('Total:', max(times)/100, '\n')


def search_for_team(country, team_size, events, number_of_top_teams,
                    show_output=True):
    global all_persons, all_averages
    global persons, averages, top_teams

    # organize the corresponding data
    persons = dict((id, name) for id, name, countryId in all_persons
                   if countryId == country or country == 'world')
    averages = defaultdict(dict)
    for personId, eventId, best in all_averages:
        if personId in persons and eventId in events:
            averages[personId][eventId] = best

    # remove people who have at least teamsize nemesis
    averages2 = dict()
    for person, person_events in averages.items():
        nemesis_count = -1  # a person is it's own nemesis
        for possible_nemesis, nemesis_events in averages.items():
            if set(person_events.keys()).issubset(set(nemesis_events.keys())):
                if all(person_events[event] >= nemesis_events[event]
                       for event in person_events):
                    nemesis_count += 1
                    if nemesis_count == team_size + number_of_top_teams - 1:
                        break
        else:
            averages2[person] = person_events
    averages = averages2

    top_teams = TopTeams(number_of_top_teams)
    for team in combinations(averages, team_size):
        divide_events(team, events, [0 for i in range(team_size)],
                      [[] for i in range(team_size)])

    if show_output:
        print('Top teams for %d-person teams for the'
              ' guildford_challenge in %s:' % (team_size, country))
        top_teams.printTeams()
    return top_teams


def divide_events(team, events_left, times, event_division):
    global top_teams, averages

    if len(events_left) == 0:
        top_teams.add(team, times, event_division)
    else:
        next_event = events_left[0]
        for i, person in enumerate(team):
            if next_event in averages[person]:
                times_copy = times[:]
                times_copy[i] += averages[person][next_event]
                if not top_teams.storage_full() or \
                   sorted(times_copy, reverse=True) < \
                   sorted(top_teams.get_worst_time(), reverse=True):
                    event_division2 = [events[:] for events in event_division]
                    event_division2[i].append(next_event)
                    divide_events(team, events_left[1:], times_copy,
                                  event_division2)


def country_ranking(team_size, events):
    global countries, all_persons, event_names
    persons_names = dict((id, name) for id, name, countryId in all_persons)
    country_rankings = []
    for country in countries:
        top_team = search_for_team(country, team_size, events, 1, False)
        if len(top_team.teams) > 0:
            country_rankings.append((country, deepcopy(top_team.teams[0])))

    country_rankings.sort(key=lambda i: sorted(i[1][1], reverse=True))

    for i, (country, team) in enumerate(country_rankings, start=1):
        time_str = str(max(team[1])/100) + ' seconds'
        print(str(i) + '. ' + country + ': ' + time_str)
        zipped_team = list(zip(team[0], team[1], team[2]))
        zipped_team.sort(key=lambda t: t[1], reverse=True)
        for person, t, events in zipped_team:
            event_str = ', '.join([event_names[event] for event in events])
            time_str = ' (' + str(t/100) + ' seconds)'
            try:
                print('   ' + persons_names[person] + ': ' +
                      event_str + time_str)
            except:
                print('   ' + person + ': ' +
                      event_str + time_str)


if __name__ == '__main__':
    update_tsv_export()
    prepair_data()

    global countries
    events = '777 666 555 minx 333ft 444 sq1 222 333 333oh clock pyram skewb'\
             .split()
    team_size = 3
    number_of_top_teams = 10
    country = None
    rank_by_country = False
    for command in sys.argv[1:]:
        m = re.findall(r'events=(.*)', command)
        if m:
            events = m[0].split()
            continue
        m = re.findall(r'team_size=(.*)', command)
        if m:
            try:
                team_size = int(m[0])
                continue
            except:
                pass
        m = re.findall(r'number_of_top_teams=(.*)', command)
        if m:
            try:
                number_of_top_teams = int(m[0])
                continue
            except:
                pass
        if command in countries:
            country = command
            continue
        if command == 'countries':
            rank_by_country = True
            continue
        if command == 'world':
            country = command
            continue
        # if nothing match, print usage
        print('Usage: ')
        print('  python guildford_challenge.py'
              ' country_name | countries | world')
        print('                    [events="event_names"]')
        print('                    [team_size=number]')
        print('                    [number_of_top_teams=number]')
        print()
        print('Examples: ')
        print('python guildford_challenge.py Finland')
        print('      list the top teams for Finland')
        print('python guildford_challenge.py "United Kingdom"'
              ' events="555 444 333 222 333oh sq1 pyram minx clock skewb"')
        print('      list the top teams for UK for the mini'
              ' guildford challenge')
        print('python guildford_challenge.py countries')
        print('       ranks the countries by their top team')
        print('python guildford_challenge.py world team_size=2')
        print('       top 2-person teams in the world')
        break
    else:
        if country:
            search_for_team(country, team_size, events, number_of_top_teams)
        elif rank_by_country:
            country_ranking(team_size, events)
