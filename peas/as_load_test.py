#! /usr/bin/python

import subprocess
import threading
import time
import datetime
import pathlib
import argparse

from peas import *

now=str(datetime.datetime.now())
subject='Stress test (%s)' % now
base=10000
global quiet

quiet=False

class AtomicInteger():
    def __init__(self, value=0):
        self._value = int(value)
        self._lock = threading.Lock()

    def inc(self, d=1):
        with self._lock:
            self._value += int(d)
            return self._value

    def dec(self, d=1):
        return self.inc(-d)

    @property
    def value(self):
        with self._lock:
            return self._value

    @value.setter
    def value(self, v):
        with self._lock:
            self._value = int(v)


class AtomicLog():
    def __init__(self, file_name):
        self._f = open(file_name, "wt")
        self._lock = threading.Lock()

    def write(self,msg):
        with self._lock:
            self._f.write(msg)
    def close(self):
        self._f.close()

succeeded = AtomicInteger()
failed = AtomicInteger()
executed = AtomicInteger()
global log
#log = None

R = '\033[1;31m'  # RED
G = '\033[0;32m'  # GREEN
Y = '\033[0;33m'  # YELLOW
M = '\033[0;35m'  # MAGENTA
S = '\033[0m'     # RESET


def error(msg):
    sys.stderr.write('{0}[-] {1}{2}\n'.format(R, msg, S))


def init_authed_client(server, user, password, verify=True):

    if user is None:
        error("A username must be specified for this command.")
        return False
    if password is None:
        error("A password must be specified for this command.")
        return False

    client = Peas()

    creds = {
        'server': server,
        'user': user,
        'password': password,
    }
    """
    if options.smb_user is not None:
        creds['smb_user'] = options.smb_user
    if options.smb_password is not None:
        creds['smb_password'] = options.smb_password    
    """

    client.set_creds(creds)

    if not verify:
        client.disable_certificate_verification()

    return client


def test_thread_function(server, domain, password, index, begin, end, sleep, period):
    tic = time.perf_counter()
    toc = tic
    time.sleep(index*sleep)
    while True:
        for i in range(begin, end):
            email="L%d.T%d@%s" % (i,i,domain)
            user=email
            args=['ruler', "-k", "--email", email, "--username", user, "--password", password, "send", "--subject", subject]

            ticrun = time.perf_counter()
            client = init_authed_client(server, user, password, False)
            if not client:
                return

            creds_valid = client.check_auth()

            toc = time.perf_counter()
            if not quiet:
                print("thread {%03d}: %s %0.2fs %0.2fs" % (index, email, toc-tic, toc-ticrun))
            if creds_valid:
                succeeded.inc()
            else:
                failed.inc()

            executed.inc()
            time.sleep(sleep)
            if period is not None and (toc-tic)/60 > period:
                return
        if period is None:
            return

def test_main(args):
    tic = time.perf_counter()
    delay = args.delay
    accounts = args.accounts
    server = args.server
    domain = args.domain
    period = args.period
    password = args.password

    global quiet
    quiet = args.quiet

    # prepare test threads
    threads = []

    global log
    log = AtomicLog(args.log)

    print("======== Preparing threads ================")

    for i in range(0, accounts):
        begin = base + i
        end = begin + 1
        print("thread %d, %d -> %d" % (i, begin, end))
        threads.append(threading.Thread(target=test_thread_function, args=(server, domain, password, i, begin, end, delay, period)))

    # run all tests
    print("======== Start threads ====================")

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    print("======== Finished =========================")

    # print summary
    toc = time.perf_counter()
    print("threads: %d" % accounts)
    print("delay: %f" % delay)
    if period is not None:
        print("period: %d" % period)
    print("")
    print("accounts: %d" % accounts)
    print("succeeded: %d" % succeeded.value)
    print("failed: %d" % failed.value)
    print("requests/second: %0.4f" % (float(succeeded.value + failed.value)/(toc - tic)) )
    print(f"Tests finished in {toc - tic:0.4f} seconds")

    # generate test report
    report_file = pathlib.Path(args.report)
    is_old = report_file.is_file()

    f=open(args.report, "at")
    if not is_old:
        f.write('timestamp,threads,delay,accounts,succeeded,failed,time\n') # write csv header
    f.write('"%s","%d","%f","%d","%d","%d","%f"\n' % (now,accounts,delay,accounts,succeeded.value,failed.value, toc - tic))
    f.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='ActiveSync load tester')
# For simplicity, threads = accounts,
#    parser.add_argument('--threads', help='number of concurrent threads',type=int, required=True)
    parser.add_argument('--delay', default=0.1, help='the delay (in seconds) between each requests in a thread, default value: 0.1 (seconds)',type=float)
    parser.add_argument('--accounts', help='the number of accounts to be tested',type=int, required=True)
    parser.add_argument('--domain', help='the test domain, e.g. yourdomain.com', required=True)
    parser.add_argument('--server', help='the exchange server, e.g. mail.yourdomain.com', required=True)
    parser.add_argument('--password', help='mailbox password', required=True)
    parser.add_argument('--period', help='test period, in minutes, optional', type=int)
    parser.add_argument('--report', default="report.csv", help='report file name, default name: report.csv')
    parser.add_argument('--quiet', action=argparse.BooleanOptionalAction, help='do not show result of every request')
    parser.add_argument('--log', default="activesync_test.log", help='error log file name, default name: activesync_test.log')

    args = parser.parse_args()
    test_main(args)