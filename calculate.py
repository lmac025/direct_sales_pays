#!/usr/bin/python2

import sys
sys.path.append('/srv/django')

import syslog
import pyodbc
import multiprocessing

from common.servers import get_redis, DEPLOY_MODE
from common.databases import get_database_connections


DATABASES = get_database_connections(DEPLOY_MODE)


def loop():
    syslog.openlog('direct.pays', syslog.LOG_PID)
    syslog.syslog(syslog.LOG_PID, 'Starting up: DEPLOY_MODE={0}'.format(DEPLOY_MODE))

    r = get_redis(db=3)
    syslog.syslog(syslog.LOG_PID, 'Acquired Redis connection: {0}'.format(r))

    syslog.syslog(syslog.LOG_PID, 'Entering main loop')

    try:
        while True:
            _, jobid = r.blpop('q:direct.pays')
            process(jobid)
    except KeyboardInterrupt:
        syslog.syslog(syslog.LOG_PID, 'Caught SIGINT; exiting')
        sys.exit(1)


def get_dbcon(data):

    try:
        syslog.syslog(syslog.LOG_PID, 'Getting DB connection for project {0}'.format(**data))
    except:
        syslog.syslog(syslog.LOG_PID, 'Data messy?')
    try:
        dbid = '{0}_{1}pays_default'.format(data['project'], ('', 'ibu_')['ibu' in data])
    except KeyError:
        syslog.syslog(syslog.LOG_PID, 'bad data: {0}'.format(data))
        return

    dbinfo = DATABASES.get(dbid)

    try:
        dbinfo['driver'] = dbinfo['OPTIONS']['driver']
    except Exception:
        syslog.syslog(syslog.LOG_PID, 'couldn\'t get database connection information: data={0}'.format(data))
        return

    dsn = 'driver={{{driver}}};server={HOST};database={NAME};uid={USER};pwd={PASSWORD}'
    con = pyodbc.connect(dsn.format(**dbinfo), autocommit=True)

    return con


def process(jobid):
    syslog.syslog(syslog.LOG_PID, 'Processing jobid {0}'.format(jobid))

    if not jobid:
        syslog.syslog(syslog.LOG_PID, 'got falsy jobid')
        return

    syslog.syslog(syslog.LOG_PID, 'Getting data for jobid {0}'.format(jobid))
    r = get_redis(db=3)
    data = r.hgetall('i:direct.pays:{0}'.format(jobid))

    if not data:
        syslog.syslog(syslog.LOG_PID, 'no data for jobid: {0}'.format(jobid))
        return

    syslog.syslog(syslog.LOG_PID, 'Got {0} bytes of data for jobid {1}'.format(len(repr(data)), jobid))

    dbcon = get_dbcon(data)

    if not dbcon:
        return

    cur = dbcon.cursor()

    sql = 'exec {0}.xsp_calculate_paylines @cycleid = ?, @payrunid = ?;'.format(('pays', 'ibu')['ibu' in data])
    params = (data.get('cycle'), data.get('pay_run'))
    syslog.syslog(syslog.LOG_PID, 'executing: {0}  [params: {1}]'.format(sql, params))

    try:
        cur.execute(sql, params)
    except Exception as e:
        syslog.syslog(syslog.LOG_PID, str(e))

    cur.close()
    dbcon.close()


def main():
    jobs = []
    for i in range(5):
        p = multiprocessing.Process(target=loop)
        jobs.append(p)
        p.start()

    try:
        for p in jobs:
            p.join()
    except KeyboardInterrupt:
        syslog.syslog(syslog.LOG_PID, 'Caught SIGINT')


if __name__ == '__main__':
    main()
