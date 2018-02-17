# -*- coding: utf-8 -*-
import os, sys
path = os.path.join(os.path.dirname(__file__), '../lib/')
sys.path.insert(0, path)

import requests, rsa

from thrift.transport import THttpClient
from thrift.protocol import TCompactProtocol

from curve import LineService
from curve.ttypes import *

class Talk:
  client = None

  auth_query_path = "/api/v4/TalkService.do";
  http_query_path = "/S4";
  wait_for_mobile_path = "/Q";
  host = "gw.line.naver.jp";
  port = 443;

  UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36"
  LA = "DESKTOPMAC	7.18.1	Tanysyz	11.2.5"

  authToken = None
  cert = None
  Headers = {}

  def __init__(self):
    self.transport = THttpClient.THttpClient('https://gw.line.naver.jp:443'+self.auth_query_path)
    self.transport.setCustomHeaders({
      "User-Agent" : self.UA,
      "X-Line-Application" : self.LA,
    })
    self.transport.open()
    self.protocol = TCompactProtocol.TCompactProtocol(self.transport);
    self.client = LineService.Client(self.protocol)

  def login(self, mail, passwd, cert=None, callback=None):
    self.transport.path = self.auth_query_path
    rsakey = self.client.getRSAKeyInfo(IdentityProvider.LINE)
    crypt = self.__crypt(mail, passwd, rsakey)

    result = self.client.loginWithIdentityCredentialForCertificate(
      IdentityProvider.LINE,
      rsakey.keynm,
      crypt,
      True,
      '127.0.0.1',
      'http://dg.b9dm.com/KoenoKatachi.mp4',
      cert
    )

    if result.type == 3:
      callback(result.pinCode)
      header = {"X-Line-Access": result.verifier}
      r = requests.get(url="https://" + self.host + self.wait_for_mobile_path, headers=header)

      result = self.client.loginWithVerifierForCerificate(r.json()["result"]["verifier"])
      self.transport.setCustomHeaders({
			 "X-Line-Application" : self.LA,
			 "User-Agent" : self.UA,
       "X-Line-Access" : result.authToken
      })

      self.authToken = result.authToken
      self.set_Headers('X-Line-Access',self.authToken)
      self.cert = result.certificate
      self.transport.path = self.http_query_path

    elif result.type == 1:
      self.authToken = result.authToken
      self.cert = result.certificate
      self.transport.setCustomHeaders({
			 "X-Line-Application" : self.LA,
			 "User-Agent" : self.UA,
       "X-Line-Access" : result.authToken
      })
      self.set_Headers('X-Line-Access',self.authToken)
      self.transport.path = self.http_query_path

  def TokenLogin(self, authToken):
    self.transport.setCustomHeaders({
			"X-Line-Application" : self.LA,
			"User-Agent" : self.UA,
      "X-Line-Access" : authToken,
    })
    self.authToken = authToken
    self.set_Headers('X-Line-Access',self.authToken)
    self.transport.path = self.http_query_path

  def qrLogin(self, callback):
    self.transport.path = self.auth_query_path

    qr = self.client.getAuthQrcode(True, "TGB-CHROME")
    callback("Copas Link dibawah ini ke LINE\nline://au/q/" + qr.verifier)

    r = requests.get("https://" + self.host + self.wait_for_mobile_path, headers={
      "X-Line-Application": self.LA,
      "X-Line-Access": qr.verifier,
    })

    vr = r.json()["result"]["verifier"]
    lr = self.client.loginWithVerifierForCerificate(vr)
    self.transport.setCustomHeaders({
			"X-Line-Application" : self.LA,
			"User-Agent" : self.UA,
      "X-Line-Access": lr.authToken
    })
    self.authToken = lr.authToken
    self.set_Headers('X-Line-Access',self.authToken)
    self.cert = lr.certificate
    self.transport.path = self.http_query_path
    
  def set_Headers(self, argument, value):
    self.Headers[argument] = value
  
  def __crypt(self, mail, passwd, RSA):
    message = (chr(len(RSA.sessionKey)) + RSA.sessionKey +
                   chr(len(mail)) + mail +
                   chr(len(passwd)) + passwd).encode('utf-8')

    pub_key = rsa.PublicKey(int(RSA.nvalue, 16), int(RSA.evalue, 16))
    crypto = rsa.encrypt(message, pub_key).encode('hex')

    return crypto
