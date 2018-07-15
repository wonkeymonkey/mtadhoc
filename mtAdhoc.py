import dill

from multiprocessing import Process, Queue
from time import sleep, time
import sys


from mtStations import Station
from mtRouteBuilder import AirspaceRouteBuilder



class Airspace:

    def __init__(self, transmitRange=150):

        self.stations = []
        self.frozenStations = []

        self.inputQueues = {} # sid --> inputqueue
        self.outputQueues = {} # sid --> outputqueue
        
        self.positions = {} # sid --> (x,y)
        self.routes = AirspaceRouteBuilder(self.positions, transmitRange)

        self.multithread = True
        self.clock = 0

    def __repr__(self):
        return str(self.stations)

    def __iter__(self):
        return self.stations.__iter__()

    def __getitem__(self, key):
        return self.stations[key]

    def __len__(self):
        return len(self.stations)

    @staticmethod
    def stationThread(frozenStation, stationQueues, returnQueue, stopQueue):
        """each station runs in this thread, if needed we can make multiple stations run per thread"""

        station = dill.loads(frozenStation)
        station._unfreeze(stationQueues)
        sid = station.mysid

        while stopQueue.empty():
            try:
                station()
                sleep(0.1)
            except KeyboardInterrupt:
                pass

        station._freeze()
        frozenStation = dill.dumps(station)
        returnQueue.put((frozenStation, sid))
        return 0


    def _freeze(self):
        self.frozenStations.clear()
        for station in self.stations:
            sid = station.mysid
            station._freeze()
            self.frozenStations.append((dill.dumps(station), sid))
        self.frozenStations.sort(key=(lambda x: x[-1]))


    def _unfreeze(self):
        self.stations.clear()
        for station, sid in self.frozenStations:
            s = dill.loads(station)
            s._unfreeze()
            self.stations.append(s)
        self.stations.sort(key=(lambda x: x.mysid))


    def _makeThreads(self, rtrnq, stopq):
        threads = []
        for frozenStation, sid in self.frozenStations:
            inputq, outputq = Queue(), Queue()
            self.inputQueues[sid] = inputq
            self.outputQueues[sid] = outputq
            threads.append( Process(target=self.stationThread, args=(frozenStation, (inputq,outputq), rtrnq, stopq)) )
        return threads

    def _goMultithread(self, seconds):
        print("Making threads...")
        returnQueue = Queue()
        stopQueue = Queue()
        threads = self._makeThreads(returnQueue, stopQueue)
        [ thr.start() for thr in threads ]

        print("Starting!")
        endtime = time() + seconds
        try:
            while time() < endtime:
                self.processPackets()
        except KeyboardInterrupt:
            print("Keyboard Interrupt!")

        while len([thr for thr in threads if thr.is_alive()]) > 0:
            stopQueue.put("STOP")
            print("Waiting for threads to stop...")
            sleep(1)

        recoveredStationCount = 0
        self.frozenStations.clear()

        #Todo, add a try except statment here
        print("Retrieving Stations")
        while recoveredStationCount < len(threads):
            frozenStation, sid = returnQueue.get(timeout=20)
            self.frozenStations.append((frozenStation, sid))
            recoveredStationCount += 1
            print(recoveredStationCount,end=' ', flush=True)
        print("Stopped!")

                

        
    def __call__(self, seconds=300):

        self._freeze()

        if self.multithread:
            if "idlelib.run" in sys.modules:
                print("Can't multiprocess while running in IDLE! Dropping to a single thread...", file=sys.stderr)
                print("To go multiprocess run this in a terminal, works best on linux. Windows uses might have issues with multiprocessing either way")
                self.multithread = False

        self.routes.updateRanges()
        if self.multithread:
            self._goMultithread(seconds)
        else:
            raise NotImplemented
            #self._goSinglethread(seconds)

        self._unfreeze()


        

    def processPackets(self):
        for sid, que in self.outputQueues.items():
            if not que.empty():
                packet = que.get()
                self.send(packet, sid)

    def send(self, packet, sid):
        #Debugging messages can go here
        
        for destination in self.routes.inRange(sid):
            self.inputQueue[destination].put(packet)
        

    def makeStations(self, pos):
        if not isinstance(pos, list):
           pos = [pos]
        for p in pos:
            sid = len(self.stations)
            s = Station(sid)
            self.stations.append(s)
            self.positions[sid] = p
        self.routes.updateRanges()






if __name__ == "__main__":

    
    a = Airspace()
    a.makeStations( [(0,0), (100,100)] )









