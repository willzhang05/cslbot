# Copyright (C) 2013-2015 Samuel Damashek, Peter Foley, James Forcier, Srijay Kasturi, Reed Koser, Christopher Reffett, and Fox Wilson
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import re
import signal
import threading
import multiprocessing
import concurrent.futures
from collections import namedtuple
from threading import Timer
from . import backtrace, babble, control
from .orm import Babble_last, Log
from sqlalchemy import or_

worker_lock = threading.Lock()
executor_lock = threading.Lock()

Event = namedtuple('Event', ['event', 'run_on_cancel'])


def pool_init():
    """We ignore Ctrl-C in the poll workers, so that we can clean things up properly."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


class Workers():

    def __init__(self, handler):
        with worker_lock:
            self.pool = multiprocessing.Pool(initializer=pool_init)
            self.events = {}
        with executor_lock:
            self.executor = concurrent.futures.ThreadPoolExecutor(4)
        self.handler = handler
        # Set-up notifications for pending admin approval.

        def send(msg, target=handler.config['core']['ctrlchan']):
            handler.send(target, handler.config['core']['nick'], msg, 'privmsg')
        self.defer(3600, False, self.handle_pending, handler, send)
        self.defer(3600, False, self.check_babble, handler, send)

    def start_thread(self, func, *args, **kwargs):
        with executor_lock:
            self.executor.submit(func, *args, **kwargs)

    def run_pool(self, func, args):
        with worker_lock:
            result = self.pool.apply_async(func, args)
        return result

    def restart_pool(self):
        with worker_lock:
            self.pool.terminate()
            self.pool.join()
            self.pool = multiprocessing.Pool(initializer=pool_init)

    def run_action(self, func, args):
        try:
            thread = threading.current_thread()
            thread_id = re.match('Thread-\d+', thread.name).group(0)
            thread.name = '%s running %s' % (thread_id, func.__name__)
            func(*args)
        except Exception as ex:
            ctrlchan = self.handler.config['core']['ctrlchan']
            backtrace.handle_traceback(ex, self.handler.connection, ctrlchan, self.handler.config)

    def defer(self, t, run_on_cancel, func, *args):
        event = Timer(t, self.run_action, kwargs={'func': func, 'args': args})
        event.name = '%s deferring %s' % (event.name, func.__name__)
        event.start()
        with worker_lock:
            self.events[event.ident] = Event(event, run_on_cancel)
        return event.ident

    def cancel(self, eventid):
        with worker_lock:
            self.events[eventid].event.cancel()
            if self.events[eventid].run_on_cancel:
                self.events[eventid].event.function(**self.events[eventid].event.kwargs)
            del self.events[eventid]

    def stop_workers(self, clean):
        """ Stop workers and deferred events """
        with executor_lock:
            self.executor.shutdown(clean)
            del self.executor
        with worker_lock:
            if clean:
                self.pool.close()
            else:
                self.pool.terminate()
            self.pool.join()
            del self.pool
            for x in self.events.values():
                x.event.cancel()
            self.events.clear()

    def handle_pending(self, handler, send):
        # Re-schedule handle_pending
        self.defer(3600, False, self.handle_pending, handler, send)
        admins = ": ".join(handler.admins)
        with handler.db.session_scope() as session:
            control.show_pending(session, admins, send, True)

    def check_babble(self, handler, send):
        # Re-schedule check_babble
        self.defer(3600, False, self.check_babble, handler, send)
        cmdchar = handler.config['core']['cmdchar']
        ctrlchan = handler.config['core']['ctrlchan']
        with handler.db.session_scope() as session:
            # If we don't actually update anything, don't bother checking the last row.
            if not babble.update_markov(session, handler.config):
                return
            last = session.query(Babble_last).first()
            row = session.query(Log).filter(or_(Log.type == 'pubmsg', Log.type == 'privmsg'), ~Log.msg.startswith(cmdchar), Log.target != ctrlchan).order_by(Log.id.desc()).first()
            if last is None or row is None:
                return
            if abs(last.last - row.id) > 1:
                raise Exception("Last row in babble cache (%d) does not match last row in log (%d)." % (last.last, row.id))
