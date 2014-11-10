import os, re
from glob import glob
from urllib.request import urlopen, urlretrieve
from time import time
from zipfile import ZipFile
from itertools import combinations

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
    global persons, event_names, average_rankings

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

        persons = dict((id, name, countryId) for id, subid, name, countryId in load('Persons', 'id subid name countryId') if subid == 1)
        event_names = dict((id, name) for id,name in load('Events', 'id name'))
        average_rankings = load('RanksAverage', 'personId eventId best')

update_tsv_export()
prepair_data()