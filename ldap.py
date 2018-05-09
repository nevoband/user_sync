#!/usr/bin/env python

from ldap3 import Server, Connection, SIMPLE, SYNC, ALL, SASL, SUBTREE, NTLM, BASE, ALL_ATTRIBUTES, Entry, Attribute
from ldap3.utils.conv import escape_filter_chars
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
        self.user_dn = None

    def Connect(self):
        adServer = Server(self.server, port=3268, get_info=ALL)
        self.connection = Connection(adServer, user=self.domain + "\\" + self.account, password=self.password, authentication=self.auth)

    def GetMembership(self,netid):
        groups = []

        filter = "(member:1.2.840.113556.1.4.1941:={0})".format(escape_filter_chars("CN="+netid+","+self.user_dn))

        if self.connection.bind():
            self.connection.search(search_base=self.pathRoot, 
            search_filter=filter, 
            search_scope=SUBTREE,
            attributes = ["cn", "distinguishedName","description"], size_limit=0)
            if self.connection.entries and len(self.connection.entries) > 0:
                 for group in self.connection.entries:
                     groups.append(group.cn)
        return groups

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
                        employee = Employee(member.split(',')[0].split('=')[1]+'@uic.edu')
                        employee.dn = member
                        employees.append(employee)

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
    parser.add_argument("-n", "--netid", dest="netid", type=str, required=True, help="get all groups this netid is a member of")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.configFilePath)

    ldap = Ldap(config.get('AD','server'),
                config.get('AD','domain'),
                config.get('AD','account'),
                config.get('AD','password'),
                config.get('AD','authentication'),
                config.get('AD','path_root'))

    ldap.user_dn = config.get('AD','user_dn')

    ldap.Connect()
    #adMembers = ldap.GetGroupByGuid('91957082-fc72-4987-82d5-896560930029')

    if args.netid:
        ldap.GetMembership(args.netid)

    employees = ldap.GetGroupByGuid(args.groupGuid)
    ldap.CloseConnection()
        
    #for employee in employees:
    #    print(employee.email)
    
if __name__=="__main__":
    main()
