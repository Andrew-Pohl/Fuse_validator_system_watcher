import ezgmail
import os.path
import pickle
import threading
import time
from PyQt5 import QtCore

recieveKeywords = ['KILL', 'STATUS', 'THRESHOLD_SET', 'THRESHOLD_GET']

class emailThread(QtCore.QThread):


    def __init__(self, emailClient, sendQueue, receiveQueue, config):
        self.emailClient = emailClient
        self.sendQueue = sendQueue
        self.receiveQueue = receiveQueue
        self.emailAddress = config['emailAddressToSend']
        self.AuthorisedReceiver = config['authorisedReceiver']
        QtCore.QThread.__init__(self)

    def run(self):
        while(True):
            if (self.sendQueue.qsize() != 0):
                while (self.sendQueue.qsize() != 0):
                    message = self.sendQueue.get()
                    if(message['reportType'] == 'error'):
                        ezgmail.send(self.emailAddress ,'ALERT ' + str(message['type']) , 'warning triggered for ' + str(message['type']) + ' value = ' + str(message['value']))
                    elif(message['reportType'] == 'STATUS' or message['reportType'] == 'THRESHOLD_GET'):
                        ezgmail.send(self.emailAddress, message['reportType'], message['value'])


            #check any inbound emails
            unreadThreads = ezgmail.unread()
            if(len(unreadThreads) != 0):
                for email in unreadThreads:
                    msg = email.messages[0]
                    if(int(self.AuthorisedReceiver) == 1):
                        address = msg.sender[msg.sender.index('<') + 1:msg.sender.index('>')]
                        if address != self.emailAddress:
                            continue
                    if msg.subject in recieveKeywords:
                        self.receiveQueue.put(msg)

                ezgmail.markAsRead(unreadThreads)

            time.sleep(10)

class email_client():
    def __init__(self, sendQueue, recieveQueue, config):
        ezgmail.init()

        self.service = 1
        self.thread = QtCore.QThread()
        self.thread.name = "auto_refresh"
        self.worker = emailThread(self.service, sendQueue, recieveQueue, config)
        self.worker.moveToThread(self.thread)
        self.worker.start()