import json

class Packet:
    def __init__(self, data=None):

        self.header = {}
        self.routing = []
        self.body = {}
        self.router = None
        if isinstance(data, str):
            self.unpack(rawData)
        if isinstance(data, dict):
            self.body = data

    def unpack(self, rawData):
        contents = json.loads(rawData)
        self.header.update(contents['header'])
        self.routing.update(contents['routing'])
        self.body.update(contents['body'])

    def pack(self):
        body = self.body.copy()
        header = self.header.copy()
        router = self.router

        if not self.routing:
            dst = body['dst']
            route = router.getRoute(dst)
            if not route:
                raise ValueError("Can't find route!")
            
        header['dst'] = route[0]
        header['src'] = router.mysid
        return json.dumps({'header': header, 'routing': route, 'body': body})
