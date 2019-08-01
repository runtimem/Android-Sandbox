from mitmproxy import ctx

class Addon():

    def request(self, flow):
        url_b = flow.request.url

        with open("tmp/urls.txt","a") as f:
            ctx.log.info(f"Writing url : {url_b}")
            f.write(url_b +'\n')

    def response(self, flow):
        pass

addons = [
    Addon()
]