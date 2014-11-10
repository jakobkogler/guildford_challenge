import os, re
from glob import glob
from urllib.request import urlopen, urlretrieve
from time import time
from zipfile import ZipFile
from itertools import combinations
from collections import defaultdict

def update_tsv_export(reporthook=None):
    """If export is missing or not current, download the current one. Returns True iff the export was updated."""

    # Is export file missing or older than 10 minutes?
    here = glob('WCA_export*_*.tsv.zip')
    if not here or time() - os.stat(max(here)).st_mtime > 10 * 60:

        # What's the current export on the WCA site?
        base = 'https://www.worldcubeassociation.org/results/misc/'
        try:
            with urlopen(base + 'export.html') as f:
                current = re.search(r'WCA_export\d+_\d+.tsv.zip', str(f.read())).group(0)
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
    global all_persons, event_names, all_averages

    with ZipFile(max(glob('WCA_export*_*.tsv.zip'))) as zf:
        def load(wanted_table, wanted_columns):
            with zf.open('WCA_export_' + wanted_table + '.tsv') as tf:
                column_names, *rows = [line.split('\t') for line in tf.read().decode().splitlines()]
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

        all_persons = list((id, name, countryId) for id, subid, name, countryId in load('Persons', 'id subid name countryId') if subid == 1)
        event_names = dict((id, name) for id,name in load('Events', 'id name'))
        all_averages = load('RanksAverage', 'personId eventId best')

def search_for_team(country, events, team_size):
    global all_persons, all_averages
    global persons, averages

    #organize the corresponding data
    persons = dict((id, name) for id, name, countryId in all_persons if countryId == country)
    averages = defaultdict(dict)
    for personId, eventId, best in all_averages:
        if personId in persons and eventId in events:
            averages[personId][eventId] = best


update_tsv_export()
prepair_data()
search_for_team('Finland', '777 666 555 minx 333ft 444 sq1 222 333 333oh clock pyram'.split(), 3)