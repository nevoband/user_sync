#!/usr/bin/env python

import configparser
import argparse
import cx_Oracle
import smtplib

class Employee:
	def __init__(self, email, firstName, lastName, middleName):
		self.email = email
		self.firstName = firstName
		self.lastName = lastName
		self.middleName = middleName
		self.departments = []
	
	def AddDepartment(self, department):
		self.departments.append(department)
		

class Edw:
	def __init__(self, username, password, host, port, database):
		self.username = username
		self.password = password
		self.host = host
		self.port = port
		self.database = database

	def Connect(self):

		try: 
			self.edwDB = cx_Oracle.connect(self.username, self.password, self.host + ':' + self.port + '/' + self.database)
		except cx_Oracle.DatabaseError as e:
			print(e)		
			raise

		self.edwCursor = self.edwDB.cursor()

	def GetFacultyUsers(self):
		facultyFilter = "(\
                             	V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD LIKE 'A%' OR V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD = 'HA' OR\
                             	V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD LIKE 'P%' OR V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD LIKE 'R%'\
                            	)"
		return self.GetEmployees(facultyFilter)

	def GetStaffUsers(self):
		staffFilter = "( \
			       V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD LIKE 'B%' OR V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD LIKE 'C%' OR \
			       V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD LIKE 'D%' OR V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD LIKE 'E%'\
			      )"
		return self.GetEmployees(staffFilter)

	def GetEmployees(self, employeeFilter):
		employees = []
		queryEmployees = "SELECT\
			    DISTINCT V_EMPEE_CAMPUS_EMAIL_ADDR.EMAIL_ADDR, V_EMPEE_PERS_HIST_1.PERS_FNAME, V_EMPEE_PERS_HIST_1.PERS_LNAME, V_EMPEE_PERS_HIST_1.PERS_MNAME\
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
			    V_EMPEE_HIST_1.ACTIVE_EMPEE_IND = 'Y'\
			      AND\
			    V_EMPEE_HIST_1.EMPEE_CUR_INFO_IND = 'Y'\
			      AND\
			    V_EMPEE_HIST_1.EMPEE_STATUS_CD = 'A'\
			      AND\
			    V_EMPEE_HIST_1.EMPEE_DATA_STATUS_DESC = 'Current'\
			      AND\
			    V_JOB_DETL_HIST_1.JOB_DETL_COLL_CD = 'FX'\
			      AND\
			    V_JOB_DETL_HIST_1.JOB_DETL_CUR_INFO_IND = 'Y'\
			      AND\
			    V_JOB_DETL_HIST_1.JOB_DETL_DATA_STATUS_DESC = 'Current'\
			      AND\
			    V_JOB_DETL_HIST_1.JOB_DETL_STATUS_DESC = 'Active'\
			      AND\
			    " + employeeFilter + "\
			      AND\
			    V_EMPEE_CAMPUS_EMAIL_ADDR.EMAIL_UI_RPT_IND = 'Y'\
			      AND\
           		    V_EMPEE_CAMPUS_EMAIL_ADDR.EMAIL_STATUS_IND = 'A'\
			ORDER BY\
			    V_EMPEE_CAMPUS_EMAIL_ADDR.EMAIL_ADDR"
		self.edwCursor.execute(queryEmployees)
		for employeeAttrib in self.edwCursor:
			employees.append(Employee(employeeAttrib[0], employeeAttrib[1], employeeAttrib[2], employeeAttrib[3]))
		return employees		

	def CloseConnection(self):
		self.edwDB.close()
		
def main():
	parser = argparse.ArgumentParser(description="Update listserv subscribers from a text file")
	parser.add_argument("-c", "--config", dest="configFilePath", type=str, required=True, help="config.ini file path ")
        args = parser.parse_args()
	config = configparser.ConfigParser()
	config.read(args.configFilePath)
	edw = Edw( config.get('EDW_DB', 'username'), config.get('EDW_DB', 'password'),config.get('EDW_DB', 'host'),config.get('EDW_DB', 'port'),config.get('EDW_DB', 'database'))
	edw.Connect()
	employees = edw.GetFacultyUsers()
	for employee in employees:
		print(employee.email)
	edw.CloseConnection()
if __name__ == "__main__":
	main()
