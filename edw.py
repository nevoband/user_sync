#!/usr/bin/env python
import configparser
import argparse
import cx_Oracle
import smtplib
import sys

from lib import Employee

class Filters:
    def __init__(self):
        self.conditionals = []
        self.filterDict = {}
        self.filterInc = 0

    def AddFilter(self, conditional, filterDict = None):
        self.conditionals.append(conditional)

        if filterDict:
            self.filterDict.update(filterDict)

        self.filterInc += 1
    
class Edw:
    def __init__(self, username, password, host, port, database):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.database = database
        self.filters = Filters()
        self.gracePeriodDays = 0

    def Connect(self):

        try: 
            self.edwDB = cx_Oracle.connect(self.username, self.password, self.host + ':' + self.port + '/' + self.database)
        except cx_Oracle.DatabaseError as e:
            raise

        self.edwCursor = self.edwDB.cursor()

    def FilterCollege(self, collegeCode ):
        collegeConditional = "V_JOB_DETL_HIST_1.JOB_DETL_COLL_CD = :coll_code"
        collegeFilterDict = { "coll_code":collegeCode }
        self.filters.AddFilter(collegeConditional, collegeFilterDict)

    def FilterFaculty(self):
        facultyConditional = "(\
                                 V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD LIKE 'A%' OR V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD = 'HA' OR\
                                 V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD LIKE 'P%' OR V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD LIKE 'R%'\
                                )"
        self.filters.AddFilter(facultyConditional)

    def FilterStaff(self):
        staffConditional = "( \
                   V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD LIKE 'B%' OR V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD LIKE 'C%' OR \
                   V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD LIKE 'D%' OR V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD LIKE 'E%'\
                  )"
        self.filters.AddFilter(staffConditional)

    def FilterOrganization(self, orgCodeFilter):
        orgConditional = "V_JOB_DETL_HIST_1.ORG_CD = :org_code_" + str(self.filters.filterInc)
        orgFilterDict = { "org_code_" + str(self.filters.filterInc):orgCodeFilter }
        self.filters.AddFilter(orgConditional, orgFilterDict)
        
    def GetEmployees(self):
        employees = []
        if self.filters.conditionals > 0:
            self.filters.filterDict.update({'grace_period':self.gracePeriodDays})
            queryEmployees = "SELECT\
                    DISTINCT V_EMPEE_CAMPUS_EMAIL_ADDR.EMAIL_ADDR, V_EMPEE_PERS_HIST_1.PERS_FNAME, V_EMPEE_PERS_HIST_1.PERS_LNAME, V_EMPEE_PERS_HIST_1.PERS_MNAME, V_EMPEE_HIST_1.FIRST_WORK_DT\
                FROM\
                    V_JOB_DETL_HIST_1,\
                    V_EMPEE_HIST_1,\
                    V_EMPEE_CAMPUS_EMAIL_ADDR,\
                    V_EMPEE_PERS_HIST_1\
                WHERE\
                    V_JOB_DETL_HIST_1.EDW_PERS_ID =  V_EMPEE_HIST_1.EDW_PERS_ID\
                      AND\
                    V_EMPEE_CAMPUS_EMAIL_ADDR.EDW_PERS_ID = V_JOB_DETL_HIST_1.EDW_PERS_ID\
                      AND\
                    V_JOB_DETL_HIST_1.EDW_PERS_ID = V_EMPEE_PERS_HIST_1.EDW_PERS_ID\
                      AND\
                    V_EMPEE_HIST_1.EMPEE_CUR_INFO_IND = 'Y'\
                      AND\
                    (V_EMPEE_HIST_1.EMPEE_STATUS_CD = 'A' OR (V_EMPEE_HIST_1.EMPEE_STATUS_CD = 'T' AND V_EMPEE_HIST_1.LAST_WORK_DT >= TRUNC(SYSDATE) - :grace_period ))\
                      AND\
                    V_EMPEE_HIST_1.EMPEE_DATA_STATUS_DESC = 'Current'\
                      AND\
                    V_JOB_DETL_HIST_1.JOB_DETL_CUR_INFO_IND = 'Y'\
                      AND\
                    V_JOB_DETL_HIST_1.JOB_DETL_DATA_STATUS_DESC = 'Current'\
                      AND\
                    (V_JOB_DETL_HIST_1.JOB_DETL_STATUS_DESC = 'Active' OR V_JOB_DETL_HIST_1.JOB_DETL_STATUS_DESC = 'Terminated')\
                      AND\
                        V_EMPEE_PERS_HIST_1.PERS_CUR_INFO_IND = 'Y'\
                      AND\
                    V_EMPEE_CAMPUS_EMAIL_ADDR.EMAIL_UI_RPT_IND = 'Y'\
                      AND\
                    V_EMPEE_CAMPUS_EMAIL_ADDR.EMAIL_STATUS_IND = 'A'\
                      AND\
                    " + ' AND '.join(self.filters.conditionals) + "\
                ORDER BY\
                    V_EMPEE_CAMPUS_EMAIL_ADDR.EMAIL_ADDR"
            try:
                self.edwCursor.execute(queryEmployees, self.filters.filterDict)
            except cx_Oracle.DatabaseError as e:
                print("Database execution error: " + str(e))
                raise
        else:
            sys.exit("no conditionals set")

        for employeeAttrib in self.edwCursor:
            employee = Employee(employeeAttrib[0], employeeAttrib[1], employeeAttrib[2], employeeAttrib[3])
            employee.firstDay = employeeAttrib[4]
            employees.append(employee)

        return employees        

    def CloseConnection(self):
        try:
            self.edwCursor.close()
            self.edwDB.close()
        except cx_Oracle.DatabaseError:
            pass
        
def main():
    parser = argparse.ArgumentParser(description="Update listserv subscribers from a text file")
    parser.add_argument("-c", "--config", dest="configFilePath", type=str, required=True, help="config.ini file path ")
    parser.add_argument("-o", "--org-code", dest="orgCode" , type=str, required=False, help="Organization Code to filter employees by")
    parser.add_argument("-d", "--col-code", dest="colCode" , type=str, required=True, help="College Code")
    parser.add_argument("-p", "--grace-period", dest="grace", type=int, required=False, help="Grace period in days after a person is terminated to still pull them as active")
    parser.add_argument("--academic", dest="academicFilter", action="store_true", help="filter only academic positions")
    parser.add_argument("--staff", dest="staffFilter", action="store_true", help="filter only Staff filter")

    
    args = parser.parse_args()

    #parse the config ini file
    config = configparser.ConfigParser()
    config.read(args.configFilePath)
    
    #setup EDW connection
    edw = Edw( config.get('EDW_DB', 'username'), config.get('EDW_DB', 'password'),config.get('EDW_DB', 'host'),config.get('EDW_DB', 'port'),config.get('EDW_DB', 'database'))
    edw.Connect()
    
    #set grace period if user requested
    if args.grace:
        edw.gracePeriodDays = args.grace

    #filters
    if args.orgCode:
        edw.FilterOrganization(args.orgCode)

    edw.FilterCollege(args.colCode)

    if args.staffFilter:
        edw.FilterStaff()
    
    if args.academicFilter:
        edw.FilterFaculty()

    #print employees
    try:
        #print employees 
        employees = edw.GetEmployees()
        for employee in employees:
            print(employee.netid +";")
    finally:
        #close connection to EDW
        edw.CloseConnection()

if __name__ == "__main__":
    main()
