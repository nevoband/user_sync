#!/usr/bin/env python

from ldap3 import Server, Connection, SIMPLE, SYNC, ALL, SASL, SUBTREE, NTLM, BASE, ALL_ATTRIBUTES, Entry, Attribute
import argparse
import configparser
import sys

from lib import Employee

class Ldap:
    def __init__(self, server, domain, account, password, auth, pathRoot):
        self.server = server
        self.domain = domain
        self.account = account
        self.password = password
        self.auth = auth
        self.pathRoot = pathRoot

    def Connect(self):
        adServer = Server(self.server, port=3268, get_info=ALL)
        self.connection = Connection(adServer, user=self.domain + "\\" + self.account, password=self.password, authentication=self.auth)

    def GetGroupByGuid(self, objectguid):
        employees = []
        filter = "(objectGuid=" + objectguid + ")"
        if self.connection.bind():
            self.connection.search(search_base=self.pathRoot, 
            search_filter=filter, 
            search_scope=SUBTREE,
            attributes = ["objectGuid","cn","distinguishedName", "member"], size_limit=0)
            
            if self.connection.entries and len(self.connection.entries) > 0:
                #print('entries exist')
                if self.connection.entries[0].member:
                    for member in self.connection.entries[0].member:
                        employees.append(Employee(member.split(',')[0].split('=')[1]+'@uic.edu'))

                    return employees
    
            else:
                sys.exit("Group not found")
             
        else:
            sys.exit("Failed to LDAP Bind")
    def CloseConnection(self):
        self.connection.unbind()
    
def main():
    parser = argparse.ArgumentParser(description="Query Active directory")
    parser.add_argument("-c", "--config", dest="configFilePath", type=str, required=True, help="config.ini file path")
    parser.add_argument("-g", "--guid", dest="groupGuid", type=str, required=True, help="get GUID of group you would like to pull members for")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.configFilePath)

    ldap = Ldap(config.get('AD','server'),
                config.get('AD','domain'),
                config.get('AD','account'),
                config.get('AD','password'),
                config.get('AD','authentication'),
                config.get('AD','path_root'))
    ldap.Connect()
    #adMembers = ldap.GetGroupByGuid('91957082-fc72-4987-82d5-896560930029')
    employees = ldap.GetGroupByGuid(args.groupGuid)
    ldap.CloseConnection()
    for employee in employees:
        print(employee.email)
    
if __name__=="__main__":
    main()
