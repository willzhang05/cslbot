from random import choice


def cmd(send, msg, args):
    coin = ['heads', 'tails']
    if not msg:
        send('The coin lands on... ' + choice(coin) + '.')
    else:
        headFlips = randint(int(msg))
        tailFlips = int(msg) - headFlips
        send('The coins land on heads ' + str(headFlips) + ' times and on tails ' + str(tailFlips) + ' times.')
