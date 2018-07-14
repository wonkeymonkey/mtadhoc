#!/usr/bin/env python3
from json import loads, dumps
from multiprocessing import Queue
from random import randint


class ImaginaryStation:
    def __init__(self, sid, broadcasts=-1):
        self.sid = sid
        self.broadcasts = broadcasts

    def __repr__(self):
        if self.routable:
            return f"${self.sid}"
        else:
            return f"~${self.sid}"

    @property
    def routable(self):
        if self.broadcasts > 0:
            return True
        else:
            return False

    def broadcast(self):
        if self.broadcasts <= 0:
            self.broadcasts = 0
        self.broadcasts += 1

class Station:

    def __init__(self, sid):
        self.sid = sid
        self.clock = 0
        
        self.inqueue = None
        self.outqueue = None


        self.resender = {
            sid+0: lambda s: {'typ': 'discovery-request', 'data':list(s.known.keys()), 'dst': '*'},
            sid+1: lambda s: {'typ': 'known-request', 'data': list(s.known.keys()), 'dst': list(s.known.keys())},
            #sid+2: {'typ': '-----'},
            }
        
        self.known = {}
        

    def __repr__(self):
        return f"${self.sid}"

    def unfreeze(self, queues=(None,None)):
        self.inqueue, self.outqueue = queues
           

    def freeze(self):
        del self.inqueue
        del self.outqueue


    class Packet:
        def __init__(self, data=None):
            self.__dict__.update({
                'src': None,
                'typ': None,
                'dst': None,
                'data': None,
                })
            if data:
                self.parse(data)

        def parse(self, data):
            if isinstance(data, str):
                data = loads(data)
            self.__dict__.update({k:p for k,p in data.items() if k!='self'})

        def out(self):
            return dumps({ k:p for k,p in self.__dict__.items() if k!='self'})
            

    def send(self, data):
        dst = data.get('dst')            
        if not isinstance(dst, list):
            dst = [dst]
        for d in dst:
            p = self.Packet(data)
            p.src = self.sid
            p.dst = d
            self.outqueue.put(p.out())


    def __call__(self):
        self.clock += 1
        inq = self.inqueue
        send = self.send
        while not inq.empty():
            try:
                resp = self.incoming(self.Packet(inq.get()))
                if resp:
                    send(resp)
            except Exception as e:
                print(f"Error handeling packet on ${self.sid}, {e}")

        tick = self.clock % 50
        if tick in self.resender.keys():
            message = self.resender[tick](self)
            send(message)
    

    def incoming(self, packet):
        resp = None
        sid = self.sid
        known = list(self.known.keys())
        src = replyto = packet.src
        typ = packet.typ
        dst = packet.dst
        data = packet.data

        if src not in known:
            self.known[src] = ImaginaryStation(src, 1)

        #Multicast
        if dst=="*":            

            if typ=='discovery-request':
                if sid not in data:
                    resp = {'typ': 'discovery-response'}



        #Aimed at us
        elif dst==sid:

            if typ=='discovery-response':
                pass

            elif typ=='known-request':
                resp = {'typ': 'known-response', 'data': known}
            
            elif typ=='known-response':
                for s in data:
                    if s not in known:
                        self.known[s] = ImaginaryStation(s, -1)
        


        if resp:
            resp['dst'] = replyto
            return resp
        return None
        
        
