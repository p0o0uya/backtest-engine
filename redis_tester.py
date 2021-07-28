import time
from datetime import timedelta
import redis

def findnxt(prev, epoch):
    i = 0
    while True:
        i += 1
        nxt = prev + i*epoch
        if nxt > time.time():
            return nxt

IP   = '127.0.0.1'
PORT = 6379
PASS = '4501210575Hk_21' 

r = redis.Redis(host=IP, port=PORT,
                 db=0, password=PASS, socket_timeout=None,
                 )

r.set('pouya', 184)
print(r.get('pouya'))

# NEXT SECTION

# r.setex('timer1',
#         timedelta(seconds=20),
#         value=time.time())

epoch_period = 5*1000 #ms
scale        = 1000
r.set('timer1', px=epoch_period, value=1)
r.set('timer1_val', value=int(float(time.time()*scale)))




while True:
    # time.sleep(.5)
    # ret = r.get('timer1')
    #print(ret)
    if not r.get('timer1'):
        print('It is time to do the trigger')
        # now  = int(time.time()*scale)
        prev = int(r.get('timer1_val'))
        # nxt  = (prev + epoch_period)
        nxt  = findnxt(prev, epoch_period)
        # #print(now)
        # print(prev)
        # ttl  = int(now-prev)%(epoch_period*scale)
        # r.set('timer1', px=ttl, value=1)
        # r.set('timer1', px=int(int(time.time()*scale)-prev)%(epoch_period*scale), value=1)
        # r.set('timer1_val', value=(prev+epoch_period))
        r.set('timer1', value=1); r.pexpireat('timer1', when=nxt)
        r.set('timer1_val', value=nxt)

        #print(ttl)
        print('*'*20)
        print(time.time())

