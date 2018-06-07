#!/usr/bin/env python

import argparse
import configparser
import sys
import logging

from ldap3 import Server, Connection, SIMPLE, SYNC, ALL, SASL, SUBTREE, NTLM, BASE, ALL_ATTRIBUTES, Entry, Attribute, MODIFY_ADD, MODIFY_DELETE
from ldap3.utils.conv import escape_filter_chars

from lib import Employee
from lib import Group

class Ldap:

    def __init__(self, server, domain, account, password, auth, pathRoot):
        self.server = server
        self.domain = domain
        self.account = account
        self.password = password
        self.auth = auth
        self.pathRoot = pathRoot
        self.user_dn = None
        self.debug = False

    def Connect(self):
        adServer = Server(self.server, get_info=ALL)
        self.connection = Connection(adServer, user=self.domain + "\\" + self.account, password=self.password, authentication=self.auth)

    def Exists(self, netid):
        if self.GetEmployee(netid, True):
            return True

        return False

    def GetEmployee(self, netid, existance = None):

        filter = "(&(objectClass=user)(sAMAccountName=" + netid + "))"

        if self.connection.bind():
            self.connection.search(search_base=self.user_dn,
            search_filter=filter,
            search_scope=SUBTREE,
            attributes = [ALL_ATTRIBUTES], size_limit=0)
            if self.connection.entries and len(self.connection.entries) > 0:
                if existance:
                    return True
                employee = Employee(self.connection.entries[0].mail,self.connection.entries[0].givenName, self.connection.entries[0].sn)
                if self.debug:
                    print(self.connection.entries)
                return employee

        return False

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
    def GetEmployeesByGuid(self, objectguid):
        return self.GetGroupByGuid(objectguid).employees
 
    def GetGroupByGuid(self, objectguid):
        employees = []
        filter = "(objectGuid=" + str(objectguid) + ")"
        if self.connection.bind():
            self.connection.search(search_base=self.pathRoot, 
            search_filter=filter, 
            search_scope=SUBTREE,
            attributes = ["objectGuid","cn","distinguishedName", "member"], size_limit=0)
            if self.connection.entries and len(self.connection.entries) > 0:
                group = Group(str(self.connection.entries[0].distinguishedName), str(self.connection.entries[0].objectGuid))
                if self.connection.entries[0].member:
                    for member in self.connection.entries[0].member:
                        employee = Employee(member.split(',')[0].split('=')[1]+'@uic.edu')
                        employee.dn = member
                        group.AddEmployee(employee)
                return group 
            else:
                sys.exit("Group not found")
             
        else:
            #print("request" + str(self.connection.request))
            #print("response" + str(self.connection.response))
            sys.exit("Failed to LDAP Bind")

    def AddUsersToGroup(self, employees, objectguid):
        self.GroupActions(employees, objectguid,'add')

    def DeleteUsersFromGroup(self, employees, objectguid):
        self.GroupActions(employees,objectguid, 'delete')
    
    def GroupActions(self, employees, objectguid, action):
        if self.connection.bind():
            distinguishedNames = []
            for employee in employees:
                if not employee.dn:
                    distinguishedNames.append("CN=" + employee.netid + "," + self.user_dn)
                else:
                    distinguishedNames.append(employee.dn)
            print("group action " + action)
            group = self.GetGroupByGuid(objectguid)
            if action == 'delete':
                print("deleting" + str(distinguishedNames))
                self.connection.modify(group.dn, {'member': [(MODIFY_DELETE,distinguishedNames)]})
            if action == 'add':
                print("adding" + str(distinguishedNames))
                print("print group" + str(group))
                self.connection.modify(group.dn, {'member': [(MODIFY_ADD,distinguishedNames)]}) 
                #self.connection.extend.microsoft.add_members_to_groups(distinguishedNames, [group.dn])
                print("result" + str(self.connection.result))
            print("request" + str(self.connection.request))
            print("response" + str(self.connection.response))

    def CloseConnection(self):
        self.connection.unbind()

def main():
    parser = argparse.ArgumentParser(description="Query Active directory")
    parser.add_argument("-c", "--config", dest="configFilePath", type=str, required=True, help="config.ini file path")
    parser.add_argument("-g", "--guid", dest="groupGuid", type=str, required=False, help="get GUID of group you would like to pull members for")
    parser.add_argument("-n", "--netid", dest="netid", type=str, required=False, help="if GUID is provided get all groups this netid is a member of otherwise get get ldap info of user")
    parser.add_argument("--debug", dest="debug", action="store_true", help="Print email message to stdout")
    parser.add_argument("--add-users", dest="addUsers", type=str, required=False, help="provide a comma sperated list of netids to add to the group")
    parser.add_argument("--delete-users", dest="delUsers", type=str, required=False, help="provide a comma sperated list of netids to remove from the group")
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

    if args.debug:
        ldap.debug = args.debug

    if args.addUsers:
        if args.groupGuid:
            employees = []
            for user in args.addUsers.split(','):
                employee = Employee(user)
                employees.append(employee)
                print(user)
            ldap.AddUsersToGroup(employees, args.groupGuid) 
        else:
            print("no group guid given")

    if args.delUsers:
        if args.groupGuid:
            employees = []
            for user in args.delUsers.split(','):
                employee = Employee(user)
                employees.append(employee)
                print(user)
            ldap.DeleteUsersFromGroup(employees, args.groupGuid)
        else:
            print("no group guid given")
    #if args.netid:
    #    if ldap.Exists(args.netid):
    #        if args.groupGuid:
    #            ldap.GetMembership(args.netid)
    #        ldap.GetEmployee(args.netid)
    #    else:
    #        print("No AD account exists for: " + args.netid)
    #else:
    #    if args.groupGuid:
    #        group = ldap.GetGroupByGuid(args.groupGuid)
            #print(str(group.dn))

    #if args.netid:
    #    ldap.Exists(args.netid)
    
        
    #ldap.CloseConnection()
        
    #for employee in employees:
    #    print(employee.email)
    
if __name__=="__main__":
    main()
