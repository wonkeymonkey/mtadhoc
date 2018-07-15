import json

class Packet:
    def __init__(self, data=None):

        self.header = {}
        self.routing = []
        self.body = {}
        self.router = None
        if isinstance(data, str):
            self.unpack(data)
        if isinstance(data, dict):
            self.body = data

    def unpack(self, rawData):
        contents = json.loads(rawData)
        self.header.update(contents['header'])
        self.routing = contents['routing']
        self.body.update(contents['body'])

    def pack(self):
        body = self.body.copy()
        routing = self.routing.copy()
        header = self.header.copy()
        router = self.router

        if not routing:
            dst = body['dst']
            routing = router.getRoute(dst)
            if not routing:
                raise ValueError("Can't find route!")
            
        header['dst'] = routing[0]
        header['src'] = router.mysid
        return json.dumps({'header': header, 'routing': routing, 'body': body})
