import os, sys, time
path = os.path.join(os.path.dirname(__file__), '../lib/')
sys.path.insert(0, path)

from thrift.transport import THttpClient
from thrift.protocol import TCompactProtocol

from curve import LineService
from curve.ttypes import *

class Poll:

  client = None
  http_query_path = "/S4";
  polling_path = "/P4";

  UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36"
  LA = "DESKTOPMAC	7.18.1	Tanysyz	11.2.5"

  rev = 0

  def __init__(self, authToken):
    self.transport = THttpClient.THttpClient('https://gw.line.naver.jp:443'+ self.http_query_path)
    self.transport.setCustomHeaders({
      "User-Agent" : self.UA,
      "X-Line-Application" : self.LA,
      "X-Line-Access": authToken
    });
    self.protocol = TCompactProtocol.TCompactProtocol(self.transport)
    self.client = LineService.Client(self.protocol)
    self.rev = self.client.getLastOpRevision()
    self.transport.path = self.polling_path
    self.transport.open()

  def stream(self, sleep=50000):
    #usleep = lambda x: time.sleep(x/1000000.0)
    while True:
      try:
        Ops = self.client.fetchOps(self.rev, 5)
      except EOFError:
        raise Exception("It might be wrong revision\n" + str(self.rev))

      for Op in Ops:
          # print Op.type
        if (Op.type != OpType.END_OF_OPERATION):
          self.rev = max(self.rev, Op.revision)
          return Op

      #usleep(sleep)
