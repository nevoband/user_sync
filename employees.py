#!/usr/bin/env python

import argparse
import configparser

from edw import Edw
from edw import Filters
from ldap import Ldap
from lib import Employee

class Employees:
    
    def __init__(self):
        self.ldapGuid = None
        self.orgCode = None
        self.collegeCode = None
        self.employeeTypeFilter = None
	self.edwEmployees = None
	self.ldapEmployees = None
        self.sender = None
        self.recipient = None

    def MissingFromLdap(self):
        missing = set(self.edwEmployees) - set(self.ldapEmployees)
	for employee in missing:
            print("off-board: " + employee.netid)
    def MissingFromEdw(self):
        missing = set(self.ldapEmployees) - set(self.edwEmployees)
        for employee in missing:
            print("on-board: " + employee.netid)

    def LoadEmployees(self):
        self.LoadEdwEmployees()
        self.LoadLdapEmployees()
 
    def LoadEdwEmployees(self):
	#filters
        if self.orgCode is not None:
                self.edw.FilterOrganization(self.orgCode)

        self.edw.FilterCollege(self.colCode)
	
        if self.employeeTypeFilter == "Staff":
            self.edw.FilterStaff()
        elif self.employeeTypeFilter == "Academic":
            self.edw.FilterFaculty()

        #print employees
        self.edwEmployees = self.edw.GetEmployees()

    def LoadLdapEmployees(self):
        self.ldapEmployees = self.ldap.GetGroupByGuid(self.ldapGuid)
 
    def ConnectLdap(self,server,domain,account,password,authentication,path_root):
        self.ldap = Ldap(server,domain,account,password,authentication,path_root)
	self.ldap.Connect()

    def ConnectEDW(self, username, password, host, port, database):
        #setup EDW connection
        self.edw = Edw( username, password, host, port,database)
        self.edw.Connect()
    
    def CloseConnections(self):
        self.edw.CloseConnection()
        self.ldap.CloseConnection()

    def Notify():
        commands = "\r\n".join(self.commands)
        msg = MIMEText(commands ,"plain")
        msg["Subject"] = "auto script"
        msg["FROM"] = self.sender
        msg["To"] = self.recipient
        if self.debug:
            print msg.as_string()
        else:
            print "sending email"
            s = smtplib.SMTP("localhost")
            s.sendmail(self.sender, self.recipient, msg.as_string())
            s.quit()

def main():
    parser = argparse.ArgumentParser(description="Compare EDW to Active Directory Group")
    parser.add_argument("-d", "--edw-config", dest="edwConfigFile", type=str, required=True, help="Config file for EDW connection")
    parser.add_argument("-a", "--ad-config", dest="adConfigFile", type=str, required=True, help="Config file for AD connection")
    parser.add_argument("-n", "--notify-config", dest="notifyConfig", type=str, required=True, help="Config file for notification recipients")
    parser.add_argument("-g", "--ad-guid", dest="ldapGroupGuid", type=str, required=True, help="GUID number for AD group to compare")
    parser.add_argument("-o", "--org-code", dest="edwOrgCode", type=str, required=False, help="Organization code to filter on optional")
    parser.add_argument("-c", "--col-code", dest="edwColCode", type=str, required=True, help="College Code EX: pharmacy is FX")
    parser.add_argument("--academic", dest="edwAcademicFilter", action="store_true", help="filter only academic positions")
    parser.add_argument("--staff", dest="edwStaffFilter", action="store_true", help="filter only Staff filter")
    parser.add_argument("--notify", dest="notify", action="store_true", help="Trigger a notification to recipients in the notify config file")
    args = parser.parse_args()

    employees = Employees()

    edwConfig = configparser.ConfigParser()
    adConfig = configparser.ConfigParser()
    
    adConfig.read(args.adConfigFile)
    employees.ConnectLdap(adConfig.get('AD','server'),
        adConfig.get('AD','domain'),
        adConfig.get('AD','account'),
        adConfig.get('AD','password'),
        adConfig.get('AD','authentication'),
        adConfig.get('AD','path_root'))
   
    edwConfig.read(args.edwConfigFile)
    employees.ConnectEDW(edwConfig.get('EDW_DB', 'username'), 
        edwConfig.get('EDW_DB', 'password'),
        edwConfig.get('EDW_DB', 'host'),
        edwConfig.get('EDW_DB', 'port'),
        edwConfig.get('EDW_DB', 'database'))
    
    if args.ldapGroupGuid:
        employees.ldapGuid = args.ldapGroupGuid

    if args.edwOrgCode:
        employees.orgCode = args.edwOrgCode
    
    if args.edwColCode:
        employees.colCode = args.edwColCode

    if args.edwAcademicFilter == True and args.edwStaffFilter == True:
        sys.exit("Please choose either academic or staff not both")
    else:
        if args.edwAcademicFilter:
            employees.employeeTypeFilter = "Academic"
        if args.edwStaffFilter:
            employees.employeeTypeFilter = "Staff"
            
    employees.LoadEmployees()
    employees.MissingFromLdap()
    employees.MissingFromEdw()
    
    employees.CloseConnections()

if __name__ == "__main__":
    main()

