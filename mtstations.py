from json import loads, dumps
from multiprocessing import Queue
from random import randint

class Station:

    def __init__(self, sid):
        self.sid = sid
        self.clock = 0
        
        self.inqueue = None
        self.outqueue = None


        self.resender = {

            sid+5: {'typ': 'discovery-request'},
            
            }
        
        self.known = []
        

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
                'bod': None,
                })
            if data:
                self.parse(data)

        def parse(self, data):
            if isinstance(data, str):
                data = loads(data)
            self.__dict__.update({k:p for k,p in data.items() if k!='self'})

        def out(self):
            return dumps({ k:p for k,p in self.__dict__.items() if k!='self'})
            

    def send(self, data, dst="*"):
        p = self.Packet(data)
        p.src = self.sid
        p.dst = dst
        self.outqueue.put(p.out())


    def __call__(self):
        self.clock += 1
        inq = self.inqueue
        send = self.send
        while not inq.empty():
            resp, replyto = self.incoming(self.Packet(inq.get()))
            if resp:
                send(resp, replyto)


        tick = self.clock % 30
        if tick in self.resender.keys():
            message = self.resender[tick]
            send(message)
            


        

    def incoming(self, packet):
        resp = None
        sid = self.sid
        known = self.known
        src = replyto = packet.src
        typ = packet.typ
        dst = packet.dst
        bod = packet.bod

        #Multicast
        if dst=="*":
            

            if typ=='discovery-request':
                if src not in known:
                    known.append(src)
                    resp = {'typ': 'discovery-response'}
                else:
                    pass
            elif typ=='discovery-response':
                if src not in known:
                    known.append(src)
                else:
                    pass
                

        #Aimed at us
        elif dst==sid:
            pass
        




        return (resp, replyto)
        
        
