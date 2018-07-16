import sys

from mtRouteBuilder import RouteBuilder
from mtPackets import Packet

from secrets import SystemRandom
sr = SystemRandom()

class Station:

    def __init__(self, mysid):
        self.mysid = mysid
        self.router = RouteBuilder(mysid)
        self.Packets = Packet

        self.inqueue = None
        self.outqueue = None

        self.clock = 0

    
        self.resenderdict = {
                0: self.voidcast,
                1: self.nearestRoutes,
            }
        self.resenderlist = [mysid]*len(self.resenderdict)


    def __repr__(self):
        return f"${self.mysid}"
    

    def _unfreeze(self, queues=(None,None)):
        self.inqueue, self.outqueue = queues
        

    def _freeze(self):
        #Queues can't be passed along with a Object during multithreading
        del self.inqueue
        del self.outqueue


    def send(self, packets):
        if not isinstance(packets, list): packets = [packets]
        for packet in packets:
            packet.router = self.router
            data = packet.pack()
            self.outqueue.put(data)

    #Reoccuring Packet Wrappers go here
    def voidcast(self, tickcount):
        p = self.Packets()
        p.routing = [-1]
        self.send(p)
        return tickcount + (120 * 10)

    def nearestRoutes(self, tickcount):
        mysid = self.router.mysid
        for othersid in self.router.routeables[mysid]:
            if othersid not in self.router.routeables.keys():
                p = self.Packets()
                p.routing = [othersid]
                p.body = {'typ': 'routeable-request'}
                self.send(p)
                break
        else:
            return tickcount + (10 * 10)
        return tickcount + (1 * 10)
        

    #End Wrappers


    def __call__(self):
        self.clock += 1
        clock = self.clock
        
        
        if not self.inqueue.empty():
            try:
                p = self.Packets(self.inqueue.get())
                self.processPacket(p)
            except Exception as e:
                print(f"Error working with packet on ${self.mysid}, {e}", file=sys.stderr)


        for num, t in enumerate(self.resenderlist):
            if t < clock:
                self.resenderlist[num] = self.resenderdict[num](clock)

        


    def processPacket(self, p):
        mysid = self.mysid
        router = self.router


        router.countRecieve(p.header.get('src'))
        
        if p.header['dst'] == mysid:
            if p.routing[-1] == mysid:
                resp = self.incoming(p.body)
                if resp:
                    self.send(self.Packets(resp))
            else:
                if p.routing[0] == mysid:
                    p.routing = p.routing[1:]
                    self.send(p)
            




    def incoming(self, data):
        resp=None
        mysid = self.mysid
        router = self.router

        src = replyto = data['src']
        typ = data['typ']

        payload = data.get('payload')
        
        if typ == 'routeable-request':
            resp = {'typ': 'routeable-response', 'payload': self.router.routeables[mysid]}

        elif typ == 'routeable-response':
            self.router.updateRouteable(src, payload, clearPrevious=True)


        if resp:
            resp['dst'] = replyto
            resp['src'] = mysid
        return resp















        
