#!/usr/bin/env python
import configparser
import argparse
import cx_Oracle
import sys

from lib import Employee
from lib import EdwFilter


class Edw:
    def __init__(self, username, password, host, port, database):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.database = database
        self.gracePeriodDays = 0
        self.edw_db = None
        self.edw_cursor = None

    def connect(self):
        try: 
            self.edw_db = cx_Oracle.connect(self.username, self.password, self.host + ':' + self.port + '/' + self.database)
        except cx_Oracle.DatabaseError as e:
            raise

        self.edw_cursor = self.edw_db.cursor()

    def get_employees(self, edw_filter):
        employees = []
        if edw_filter.conditionals > 0:
            query_employees = "SELECT\
                    DISTINCT V_EMPEE_CAMPUS_EMAIL_ADDR.EMAIL_ADDR,\
                    V_EMPEE_PERS_HIST_1.PERS_FNAME,\
                    V_EMPEE_PERS_HIST_1.PERS_LNAME,\
                    V_EMPEE_PERS_HIST_1.PERS_MNAME,\
                    V_EMPEE_HIST_1.FIRST_WORK_DT,\
                    V_EMPEE_HIST_1.EMPEE_DEPT_NAME,\
                    V_JOB_DETL_HIST_1.JOB_DETL_TITLE\
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
                    " + ' AND '.join(edw_filter.conditionals) + "\
                ORDER BY\
                    V_EMPEE_CAMPUS_EMAIL_ADDR.EMAIL_ADDR"

            try:
                self.edw_cursor.execute(query_employees, edw_filter.filterDict)
            except cx_Oracle.DatabaseError as e:
                print("Database execution error: " + str(e))
                raise
        else:
            sys.exit("no conditionals set")

        for employeeAttrib in self.edw_cursor:
            employee = Employee(employeeAttrib[0], employeeAttrib[1], employeeAttrib[2], employeeAttrib[3])
            employee.firstDay = employeeAttrib[4]
            employee.department = employeeAttrib[5]
            employee.position = employeeAttrib[6]
            employees.append(employee)

        return employees        

    def close_connection(self):
        try:
            self.edw_cursor.close()
            self.edw_db.close()
        except cx_Oracle.DatabaseError:
            pass


def main():
    parser = argparse.ArgumentParser(description="update listserv subscribers from a text file")
    parser.add_argument("-c", "--config", dest="configFilePath", type=str, required=True, help="config.ini file path ")
    parser.add_argument("-o", "--org-code", dest="orgCode" , type=str, required=False, help="Organization Code to filter employees by")
    parser.add_argument("-d", "--col-code", dest="colCode" , type=str, required=True, help="College Code")
    parser.add_argument("-p", "--grace-period", dest="grace", type=int, required=False, help="Grace period in days after a person is terminated to still pull them as active")

    args = parser.parse_args()

    # parse the config ini file
    config = configparser.ConfigParser()
    config.read(args.configFilePath)
    
    # setup EDW connection
    edw = Edw( config.get('EDW_DB', 'username'), config.get('EDW_DB', 'password'),config.get('EDW_DB', 'host'),config.get('EDW_DB', 'port'),config.get('EDW_DB', 'database'))
    edw.connect()
    
    filters = EdwFilter()

    # set grace period if user requested
    if args.grace:
        filters.filter_grace_period(args.grace)

    # filters
    if args.orgCode:
        filters.FilterOrganization(args.orgCode.split(","))

    filters.filter_college(args.colCode)

    if args.staffFilter:
        filters.filter_staff()
    
    if args.academicFilter:
        filters.filter_faculty()

    # print employees
    try:
        # print employees
        employees = edw.get_employees(filters)
        for employee in employees:
            print(employee.netid +";")
    finally:
        # close connection to EDW
        edw.close_connection()


if __name__ == "__main__":
    main()
