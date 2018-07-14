#!/usr/bin/env python3
from json import loads, dumps
from multiprocessing import Process, Queue
from math import sqrt, pi, log
from time import sleep, time
import dill

from mtstations import Station, ImaginaryStation
    

class Airspace:

    @staticmethod
    def distance(sourcexy, destxy):
        (sx,sy), (dx,dy) = sourcexy, destxy
        d = sqrt( ((sx-dx)**2) + ((sy-dy)**2) )
        return d

    #This is very much NOT representative of the real world
##    @staticmethod
##    def rxpower(d, Ptx, Dtx, Drx):
##       _ = Ptx + Dtx + Drx + 20 * log( (WL / (4*pi*d)) , 10)
##       return _

    @staticmethod
    def threadp(frozenStation, queues, processQueue, stopQueue):
        """This is the function called as a seperate process for each station"""
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
        """freeze and then dill-pickle each station/node, then move them to frozenStations. After this we should be ready for going multiprocess"""
        self.frozenStations.clear()
        for station in self.stations:
            station.freeze()
            sid = station.sid
            self.frozenStations.append((dill.dumps(station), sid))


    def unfreeze(self):
        """ unfreeze each station, that way we can interact with them on the main thread """
        self.stations.clear()
        for station, sid in self.frozenStations:
            self.stations.append( dill.loads(station) )
            self.stations[-1].unfreeze()


    def __call__(self, seconds=120):

        self.freeze()
        #Prepare queues for each process and station, prepare multithreads
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
        #Start the station's threads
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
            stopq.put("STOP") #There's litterally no reason to put "STOP" multiple times if everything goes as expected
            print("Waiting for threads to stop...")
            sleep(1)

        self.frozenStations.clear()
        for q in procqueues:
            if not q.empty():
                frozen, sid = q.get()
                self.frozenStations.append((frozen, sid))

        #TODO: check for lost stations here,
        #If a station isn't returned for whatever reason
        #don't overwrite the unfrozen copy
        #this will revert all of it's data to the last time we unfroze
        #but thats better than losing it completely

        self.unfreeze()
                
        
    def packetHandler(self):
        """check for new outbound packets, and send them on their way using 'send'"""
        for sid, q in self.outqdict.items():
            if not q.empty():
                packet = q.get()
                self.send(packet, sid)
                
                
    def send(self, packet, sid):
        """add packets to all nodes within broadcasting range of the sending station, also: here is were any debugging messages are printed"""
        d = loads(packet)
        dst = d.get('dst')
        typ = d.get('typ')
        data = d.get('data')
        print(f"{sid} --> {dst} [{typ}]--|{data}")
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
                    rxpower = 1 #In the future rxpower will be a function of distance, which will impact packet delivery
                    rdict[srcsid].append((destsid, rxpower))
        

    #This really shouldn't ever be needed,
    #But dedup values that could possibly be filled with duplicates if i make a mistake
    def dedup(self):
        pass

    def checkStationKnownRoutes(self):
        count = len(self.stations)
        for s in self.stations:
            if len(s.known.keys()) != count:
                break
        else:
            print("All stations have found each other!")
            return
        


if __name__ == "__main__":

    import sys
    if "idlelib.run" in sys.modules:
        print("Can't multiprocess while running in IDLE! Run this from a terminal", file=sys.stderr)

    if (sys.version_info.major < 3) or (sys.version_info.minor < 6):
        print("Oh yeah, also I used that fancy new string formatting in Python3.6, It looks like this is an older version that that", file=sys.stderr)
        print("Those print(f\"{variable}\") are the only new feature I used, I think, but either way It probably won't work with the version you're using", file=sys.stderr)
    
    a = Airspace()

    #The transmit limit is about 150 units, so these nodes can only transmit 1 hop away
    a.makeStation([ (i,i) for i in range(0,800,100) ])
    #a.makeStation([(0,0),(100,100), (200,200), (300,300)])

    print({ k:[sid for sid,rxpower in p] for k,p in a.rdict.items() })
    sleep(2)
      
    a(60) #Run for a minute
    print(a.checkStationKnownRoutes()) #Check if all of the stations have discovered each other
    a(300) #Run for 5 minutes
    print(a.checkStationKnownRoutes())
