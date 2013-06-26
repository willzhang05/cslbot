# Copyright (C) 2013 Fox Wilson, Peter Foley, Srijay Kasturi, Samuel Damashek and James Forcier
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
import time
import sys
from config import CHANNEL, ADMINS

limit = 5
args = ['nick', 'channels', 'connection']


def do_nuke(args, target):
    c = args['connection']
    nick = args['nick']
    c.privmsg(CHANNEL, "Please Stand By, Nuking " + target)
    c.privmsg_many([nick, target], "        ____________________          ")
    c.privmsg_many([nick, target], "     :-'     ,   '; .,   )  '-:       ")
    c.privmsg_many([nick, target], "    /    (          /   /      \\      ")
    c.privmsg_many([nick, target], "   /  ;'  \\   , .  /        )   \\    ")
    c.privmsg_many([nick, target], "  (  ( .   ., ;        ;  '    ; )    ")
    c.privmsg_many([nick, target], "   \\    ,---:----------:---,    /    ")
    c.privmsg_many([nick, target], "    '--'     \\ \\     / /    '--'     ")
    c.privmsg_many([nick, target], "              \\ \\   / /              ")
    c.privmsg_many([nick, target], "               \\     /                ")
    c.privmsg_many([nick, target], "               |  .  |               ")
    c.privmsg_many([nick, target], "               |, '; |               ")
    c.privmsg_many([nick, target], "               |  ,. |               ")
    c.privmsg_many([nick, target], "               | ., ;|               ")
    c.privmsg_many([nick, target], "               |:; ; |               ")
    c.privmsg_many([nick, target], "      ________/;';,.',\\ ________     ")
    c.privmsg_many([nick, target], "     (  ;' . ;';,.;', ;  ';  ;  )    ")


def cmd(send, msg, args):
        nick = args['nick']
        levels = {1: 'Whirr...',
                  2: 'Vrrm...',
                  3: 'Zzzzhhhh...',
                  4: 'SHFRRRRM...',
                  5: 'GEEEEZZSH...',
                  6: 'PLAAAAIIID...',
                  7: 'KKKRRRAAKKKAAKRAKKGGARGHGIZZZZ...',
                  8: 'Nuke',
                  9: 'nneeeaaaooowwwwww..... BOOOOOSH BLAM KABOOM',
                  10: 'ssh root@remote.tjhsst.edu rm -rf ~'+nick}
        if not msg:
            send('What to microwave?')
            return
        match = re.match('(-?[0-9]*) (.*)', msg)
        if not match:
            send('Power level?')
        else:
            level = int(match.group(1))
            target = match.group(2)
            if level > 10:
                send('Aborting to prevent extinction of human race.')
                return
            if level < 1:
                send('Anti-matter not yet implemented.')
                return
            if level > 7:
                if nick not in ADMINS:
                    send("I'm sorry. Nukes are a admin-only feature")
                    return
                #FIXME: don't hardcode the primary channel
                elif target not in args['channels'][CHANNEL].users():
                    send("I'm sorry. Anonymous Nuking is not allowed")
                    return

            msg = levels[1]
            for i in range(2, level+1):
                if i < 8:
                    msg += ' ' + levels[i]
            send(msg)
            if level >= 8:
                do_nuke(args, target)
            if level >= 9:
                send(levels[9])
            if level == 10:
                send(levels[10])
            send('Ding, your %s is ready.' % target)
            if level == 10:
                time.sleep(7)
                args['connection'].quit("Caught in backwash.")
                sys.exit(0)
