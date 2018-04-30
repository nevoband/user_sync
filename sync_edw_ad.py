#!/usr/bin/env python

import argparse
import configparser
import Edw
import ActiveDirectory
import Filters

from edw import Edw
from edw import Filters
from ldap import ActiveDirectory
from lib import Employee

class ActiveDirectoryEDW:
	def __init__(self):


def main():
 	parser = argparse.ArgumentParser(description="Compare EDW to Active Directory Group")
	parser.add_argument("-d", "--edw-config", dest="edwConfigFile", type=str, required=True, help="Config file for EDW connection"))
	parser.add_argument("-a", "--ad-config", dst="adConfigFile", type=str, required=True, help="Config file for AD connection")
	parser.add_argument("-g", "--ad-guid", dst="adGroupGuid", type=str, required=True, help="GUID number for AD group to compare")
	parser.add_argument("-o", "--org-code", dst="edwOrgCode", type=str, required=False, help="Organization code to filter on optional")
	parser.add_argument("--academic", dest="edwAcademicFilter", action="store_true", help="filter only academic positions")
        parser.add_argument("--staff", dest="edwStaffFilter", action="store_true", help="filter only Staff filter")
        args = parser.parse_args()
	


if __name__ = "__main__":
	main()

