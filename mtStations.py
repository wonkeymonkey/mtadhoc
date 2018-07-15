import sys

from mtRouteBuilder import RouteBuilder
from mtPackets import Packet


class Station:

    def __init__(self, mysid):
        self.mysid = mysid
        self.router = RouteBuilder(mysid)
        self.Packets = Packet

        self.inqueue = None
        self.outqueue = None

        self.clock = 0


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



    def __call__(self):
        self.clock += 1

        if not self.inqueue.empty():
            try:
                p = self.Packets(self.inqueue.get())
                self.processPacket(p)
            except Exception as e:
                print(f"Error working with packet on ${self.mysid}, {e}", file=sys.stderr)
        
        
    def processPacket(self, p):
        mysid = self.mysid
        if p.header['dest'] == mysid:
            if p.routing[-1] == mysid:
                #This packet is for us! Process it
                resp = self.incoming(p.body)
                self.send(self.Packets(resp))
            else:
                if p.routing[0] == mysid:
                    #Relay the packet along the chain
                    p.routing = p.routing[1:]
                    self.send(p)


    def incoming(self, data):
        pass


















        
