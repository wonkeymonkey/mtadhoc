from json import loads, dumps
from multiprocessing import Process, Queue
from math import sqrt, pi, log
from time import sleep, time
import sys
import dill

try:
    from secrets import SystemRandom
except ImportError:
    from random import SystemRandom
sr = SystemRandom()
rchoice = sr.choice


from mtstations import Station
    

class Airspace:

    @staticmethod
    def distance(sourcexy, destxy):
        (sx,sy), (dx,dy) = sourcexy, destxy
        d = sqrt( ((sx-dx)**2) + ((sy-dy)**2) )
        return d

    #This is very much NOT representative of the real world
    @staticmethod
    def rxpower(d, Ptx, Dtx, Drx):
       _ = Ptx + Dtx + Drx + 20 * log( (WL / (4*pi*d)) , 10)
       return _

    @staticmethod
    def threadp(frozenStation, queues, processQueue, stopQueue):

        station = dill.loads(frozenStation)
        del frozenStation
        station.unfreeze(queues)

        while stopQueue.empty():
            try:
                station()
                sleep(0.1)
            except KeyboardInterrupt:
                pass

        sid = station.sid
        station.freeze()
        station = dill.dumps(station)
        processQueue.put((station, sid))
        return 1
            
  
    def __init__(self, stationCount=2):

        self.stations = []
        self.frozenStations = []

        self.outqdict = {} #sid -> outqueue
        self.inqdict = {} #sid -> inqueue

        self.pdict = {} #sid --> Position
        self.rdict = {} #sid --> StationsInRange, rxdata

        self.maxrange = 150
        self.clock = 0


    def __repr__(self):
        return str(self.stations)


    def freeze(self):
        self.frozenStations.clear()
        for station in self.stations:
            station.freeze()
            sid = station.sid
            self.frozenStations.append((dill.dumps(station), sid))


    def unfreeze(self):
        self.stations.clear()
        for station, sid in self.frozenStations:
            self.stations.append( dill.loads(station) )
            self.stations[-1].unfreeze()


    def __call__(self, seconds=120):

        self.freeze()

        threads = len(self.frozenStations)
        stopq = Queue()
        procqueues = []
        procs = []        
        for fs, sid in self.frozenStations:
            iq = Queue();oq = Queue()
            self.inqdict[sid] = iq
            self.outqdict[sid] = oq
            procqueues.append(Queue())
            procs.append( Process(target=self.threadp, args=(fs, (iq, oq), procqueues[-1], stopq)) )
        [ p.start() for p in procs ]
        
        try:
            print("Starting!")
            endtime = time() + seconds        
            while time() < endtime:
                self.packetHandler()
        except KeyboardInterrupt:
            print("Keyboard Interrupt!")
        print("Stopping")

        while len([p for p in procs if p.is_alive()]) > 0:
            stopq.put("STOP")
            print("Waiting for threads to stop...")
            sleep(1)

        self.frozenStations.clear()
        for q in procqueues:
            if not q.empty():
                frozen, sid = q.get()
                self.frozenStations.append((frozen, sid))

        self.unfreeze()
                
        
    def packetHandler(self):
        for sid, q in self.outqdict.items():
            if not q.empty():
                packet = q.get()
                self.send(packet, sid)
                
                
    def send(self, packet, sid):
        d = loads(packet)
        dst = d.get('dst')
        typ = d.get('typ')
        print(f"{sid} --> {dst} [{typ}]")
        for destsid, rxpower in self.rdict[sid]:
            self.inqdict[destsid].put(packet)

                 
    def makeStation(self, pos):
        if not isinstance(pos, list):
            pos = [pos]
        for p in pos:
            sid = len(self.stations)
            s = Station(sid)
            self.stations.append(s)
            self.pdict[sid] = p
            self.rdict[sid] = []
        self.calculateRanges()
        self.dedup()


    def calculateRanges(self):
        pdict = self.pdict
        rdict = self.rdict
        distance = self.distance

        for station in self.stations:
            rdict[station.sid].clear()
        
        for source in self.stations:
            srcsid = source.sid
            srcpos = pdict[srcsid]
            for dest in [ st for st in self.stations if st!=source]:
                destsid = dest.sid
                destpos = pdict[destsid]
                if distance(srcpos, destpos) < self.maxrange:
                    rxpower = 1
                    rdict[srcsid].append((destsid, rxpower))
        

    #This really shouldn't ever be needed,
    #But dedup values that could possibly be filled with duplicates if i make a mistake
    def dedup(self):
        pass


a = Airspace()
#a.makeStation([(0,0),(100,100), (200,200)])
a.makeStation([(0,0), (100,100)])
a(120)

