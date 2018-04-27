#!/usr/bin/env python

from ldap3 import Server, Connection, ALL
import argparse
import configparser

class ActiveDirectoryGroup:
	def __init__(self):
		self.objectGuid = ""
		self.cn = ""
		self.dn = ""
		self.member = []

class ActiveDirectory:
	def __init__(self, server, domain, account, password, auth, pathRoot):
		self.server = server
		self.domain = domain
		self.account = account
		self.password = password
		self.auth = auth
		self.pathRoot = pathRoot

	def Connect(self):
		adServer = Server(self.server, port=3268, get_info=ALL)
		self.connection = Connection(adServer, user=self.account, password=self.password, authentication=self.auth)

	def GetGroupByGuid(self, objectguid):
		filter = "(objectGuid=" + self.ad_endian_srch_format(objectuid) + ")"
		if self.connection.bind():
			self.connection.search(search_base=self.pathRoot, 
					search_filter=filter, 
					search_scope=SUBTREE,
					attributes = ["objectGuid","cn","distinguishedName", "member"], 
					size_limit=0)
			
			print(self.connection.entries[0].entry_to_json())	

	def __ad_endian_srch_format(rdGuid):
		#Var for Return Value
		fltrGuid = ""

		#Parse into Guid
		wrkGuid = uuid.UUID('{' + rdGuid + '}')

		for wrkByte in wrkGuid.bytes_le:
			fltrGuid += "\\" + "{:02x}".format(wrkByte).upper()

		return fltrGuid


def main():
	parser = argparse.ArgumentParser(description="Query Active directory")
	parser.add_argument("-c", "--config", dest="configFilePath", type=str, required=True, help="config.ini file path ")
	args = parser.parse_args()
	config = configparser.ConfigParser()
	config.read(args.configFilePath)
	activeDirectory = ActiveDirectory(config.get('AD','server'),
					config.get('AD','domain'),
					config.get('AD','account'),
					config.get('AD','password'),
					config.get('AD','authentication'),
					config.get('AD','path_root'))
	activeDirectory.Connect()

if __name__=="__main__":
	main()
