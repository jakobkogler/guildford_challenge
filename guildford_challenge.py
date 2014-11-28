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
import optparse


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
        countries = load('Countries', 'id')


class TopTeams:
    def __init__(self, max_team_count):
        self.max_team_count = max_team_count
        self.teams = []

    def add(self, team, times, event_division):
        for i, (team2, times2, event_division2) in enumerate(self.teams):
            if set(team) == set(team2):
                if self.is_faster(times, times2):
                    self.teams[i] = deepcopy((team, times, event_division))
                break
        else:
            self.teams.append(deepcopy((team, times, event_division)))
        self.teams.sort(key=lambda t: sorted(t[1], reverse=True))
        if len(self.teams) > self.max_team_count:
            self.teams.pop()

    @staticmethod
    def is_faster(times1, times2):
        return sorted(times1, reverse=True) < sorted(times2, reverse=True)

    def get_worst_time(self):
        if len(self.teams) == self.max_team_count:
            return self.teams[len(self.teams) - 1][1]
        else:
            return [float('inf')]

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
                if TopTeams.is_faster(times_copy, top_teams.get_worst_time()):
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
    parser = optparse.OptionParser("usage: %prog [options]")
    parser.add_option("-c", "--country", dest="country",
                      default="world", type="string",
                      help="country name, 'countries' or 'world'")
    parser.add_option("-e", "--events", dest="events",
                      default='777 666 555 minx 333ft 444 sq1 '
                              '222 333 333oh clock pyram skewb',
                      type="string", help="included events")
    parser.add_option("-s", "--size", dest="team_size",
                      default=3, type="int", help="team size")
    parser.add_option("-n", "--number", dest="number_of_top_teams",
                      default=10, type="int", help="show this many teams")

    (options, args) = parser.parse_args()

    update_tsv_export()
    prepair_data()

    if options.country == 'countries':
        country_ranking(options.team_size, options.events.split())
    else:
        search_for_team(options.country, options.team_size,
                        options.events.split(), options.number_of_top_teams)
