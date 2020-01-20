from __future__ import print_function
from emailClient import email_client
from PyQt5 import QtWidgets
import sys
import queue
import time
from web3 import Web3
import configparser
import sched, time
import psutil
import os
import shutil
import subprocess
from Fuse_Explorer_API.account import Account
from sys import platform

statusTypes = ['RAM', 'HDD', 'CPU', 'ETHBalance', 'FuseBalance', 'validating', 'dockerRunning']
subKeys = ['value', 'report', 'timeStamp']
recieveKeywords = ['KILL', 'STATUS', 'THRESHOLD_SET', 'THRESHOLD_GET']

class Main():
	status = {}

	def checkSystemAttributes(self):
		total, used, free = shutil.disk_usage("/")
		self.table['HDD']['value'] = free/(1024*1024)
		self.table['RAM']['value'] = psutil.virtual_memory().free/(1024*1024)
		oneMin, fiveMin, tenMin = [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()]
		self.table['CPU']['value'] = fiveMin
		self.table['FuseBalance']['value'] = float(int(self.apiFuseAccount.get_balance()) * 1e-18)
		if platform == "linux" or platform == "linux2":
			s = subprocess.check_output('docker ps', shell=True)
			if str(s).find('fusenet') != -1:
				self.table['dockerRunning']['value'] = 1
			else:
				self.table['dockerRunning']['value'] = 0

		for key in self.table:
			if key != "ETHBalance" and key in self.ThresholdDict and self.ThresholdDict[key] != '0':
				if key == 'CPU':
					if self.table[key]['value'] > (type(self.table[key]['value'])(self.ThresholdDict[key])):
						self.table[key]['report'] = 1
					else:
						self.table[key]['report'] = 0
						self.table[key]['timeStamp'] = 0
				else:
					if self.table[key]['value'] < (type(self.table[key]['value'])(self.ThresholdDict[key])):
						self.table[key]['report'] = 1
					else:
						self.table[key]['report'] = 0
						self.table[key]['timeStamp'] = 0

		self.sendErrorReport()

	def checkEthBalance(self):
		self.table['ETHBalance']['value'] = float(self.web3.eth.getBalance(self.address) / 1e18)
		if self.table['ETHBalance']['value'] < (type(self.table['ETHBalance']['value'])(self.ThresholdDict['ETHBalance'])):
			self.table['ETHBalance']['report'] = 1
		else:
			self.table['ETHBalance']['report'] = 0
			self.table['ETHBalance']['timeStamp'] = 0

		self.sendErrorReport()

	def sendErrorReport(self):
		for key in self.table:
			if self.table[key]['report'] != 0:
				#resend every hour
				if int(time.time()) - self.table[key]['timeStamp'] >= 60*60:
					Report = {}
					Report['type'] = key
					Report['value'] = self.table[key]['value']
					Report['reportType'] = 'error'
					self.sendQueue.put(Report)
					self.table[key]['timeStamp'] = int(time.time())


	def checkIndoundEmails(self):
		if (self.recieveQueue.qsize() != 0):
			message = self.recieveQueue.get()
			subject = message.subject
			Report = {}
			Report['reportType'] = subject
			if subject == 'KILL':
				exit(0)
			elif subject == 'STATUS':
				string = ''
				for key in self.table:
					string += key + '=' + str(self.table[key]['value']) + '\n'
				Report['value'] = string
				self.sendQueue.put(Report)
			elif subject == 'THRESHOLD_GET':
				string = ''
				for key in self.ThresholdDict:
					string += key + '=' + str(self.ThresholdDict[key]) + '\n'
				Report['value'] = string
				self.sendQueue.put(Report)
			elif subject == 'THRESHOLD_SET':
				snippet = message.snippet
				split = snippet.split('=')
				if(len(split) > 1):
					type = split[0]
					if type in statusTypes:
						self.ThresholdDict[type] = split[1]


	def periodic(self, scheduler, interval, action, actionargs=()):
		scheduler.enter(interval, 1, self.periodic,
						(scheduler, interval, action, actionargs))
		action(*actionargs)

	def main(self):
		self.table = {}
		for keys in statusTypes:
			self.table[keys] = {}
			for subKeysItr in subKeys:
				self.table[keys][subKeysItr] = 0
		s = sched.scheduler(time.time, time.sleep)


		config = configparser.ConfigParser()
		config.optionxform=str
		config.read("config.ini")

		self.sendQueue = queue.Queue()
		self.recieveQueue = queue.Queue()
		ui = email_client(self.sendQueue, self.recieveQueue, dict(config['SETUP']))

		self.ThresholdDict = dict(config.items('THRESHOLDS'))

		for keys in self.ThresholdDict:
			if keys not in statusTypes:
				print("Error in config file ", keys, " not a valid type")
				exit(1)

		self.web3 = Web3(Web3.HTTPProvider(config['SETUP']['infura']))
		self.address = config['SETUP']['address']
		self.apiFuseAccount = Account(address=config['SETUP']['address'])
		print(self.web3.eth.getBalance(self.address)/1e18)

		self.periodic(s, 10, self.checkSystemAttributes)
		self.periodic(s, 10, self.checkIndoundEmails)
		self.periodic(s, 60*60, self.checkEthBalance)


		s.run()

if __name__ == "__main__":
    Main().main()