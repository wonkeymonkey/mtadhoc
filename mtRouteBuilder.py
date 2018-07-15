import networkx as nx
import matplotlib.pyplot as plt
import json
from math import sqrt

from secrets import SystemRandom
sr = SystemRandom()


class RouteBuilder:
    def __init__(self, mysid):

        self.mysid = mysid

        # sid -> [stationinrange,]
        self.routeables = {}
        # sid -> [possibleroutes,]
        self.builtRoutes = {}
        
        # sid -> sessionID
        self.sessions = {} # This isn't used right now, but once encryption is implemented session data will be important

        



    def rebuildRoutes(self):
        routes = self.routeables.copy()
        mysid = self.mysid
        g = nx.empty_graph()
        
        for sid, othernodes in routes.items():
            for othernode in othernodes:
                g.add_edge(sid, othernode)

        self.builtRoutes.clear()
        for sid in routes.keys():
            if sid != mysid:
                #paths = list(nx.all_simple_paths(g, mysid, sid))
                paths = list(nx.all_shortest_paths(g, mysid, sid))

                for path in paths:
                    path.remove(mysid)
                self.builtRoutes[sid] = paths


    def updateRouteable(self, sid, updated):
        if isinstance(updated, list):
            self.routeables[sid] = updated
            self.rebuildRoutes()
        else:
            raise TypeError


    def newSession(self, sid, sessionID):
        self.sessions[sid] = sessionID


    def hasSession(self, sid):
        if sid == self.mysid:
            return True
        if self.sessions.get(sid, -1) >= 0:
            return True
        else:
            return False


    def getMissingSessions(self, stations):
        return [ sid for sid in stations if not self.hasSession(sid) ]
            
            
    def getRoute(self, destination, onlyReturnActiveSessions=False):

        if self.builtRoutes.get(destination):
            routes = self.builtRoutes[destination].copy()
            if not onlyReturnActiveSessions:
                return sr.choice(routes)
            else:
                routes = [ route for route in routes if not self.getMissingSessions(route) ]
                if len(routes) > 0:
                    return sr.choice(routes)
        return []

        


class AirspaceRouteBuilder:

    def __init__(self, positionDict, transmitRange):
        self.positionDict = positionDict
        self.transmitRange = transmitRange

        self.ranges = {}

    @staticmethod
    def distance(sourcexy, destxy):
        (sx,sy), (dx,dy) = sourcexy, destxy
        d = sqrt(((sx-dx)**2) + ((sy-dy)**2) )
        return d

    def updateRanges(self):
        self.ranges.clear()
        for sid, sxy in self.positionDict.items():
            self.ranges[sid] = []
            for did, dxy in self.positionDict.items():
                if did != sid:
                    if self.distance(sxy, dxy) < self.transmitRange:
                        self.ranges[sid].append(did)


    def inRange(self, sid):
        return self.ranges.get(sid, [])
