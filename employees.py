#!/usr/bin/env python

import argparse
import configparser
import smtplib
import sys

from email.mime.text import MIMEText

from edw import Edw
from lib import EdwFilter
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
        self.ldap = None
        self.edw = None
        self.message = []
        self.debug = False
        self.sync_employees = False
        self.gracePeriodDays = 0

    def auto(self):
        admin_notifications = []

        try:
            managed_ldap_groups = self.ldap.get_managed_groups_dn()
        except Exception as e:
            print("failed to get managed groups")
            admin_notifications.append("Failed to get managed groups: " + str(e))

        for ldapGroupDN in managed_ldap_groups:
            common_name = str(ldapGroupDN).split(",")[0].split("=")[1]
            group_notifications = []
            ldap_group = None
            try:
                ldap_group = self.ldap.get_group_by_dn(ldapGroupDN)
                if ldap_group is not None:
                    json_settings_errors = ldap_group.verify_settings()
                    if len(json_settings_errors) == 0:
                        if ldap_group.settings['script_enabled'] is True:
                            self.sync_group(ldap_group, group_notifications)
                    else:
                        group_notifications += json_settings_errors
            except Exception as e:
                if self.debug:
                    print("failed to load ldap group " + str(e))
                group_notifications.append("Failed to load group :" + str(e))

            subject = "AD Group update: " + common_name
            group_content = "\r\n".join(group_notifications)
            if self.debug:
                print("Group Email: " + common_name)
            if ldap_group.mail:
                self.send_email(str(ldap_group.mail), self.sender, subject, group_content)
            if len(group_notifications) > 0:
                group_notifications = ["Group Name: " + common_name] + group_notifications
            admin_notifications += group_notifications

        subject = "AD Admin Group Updates"
        content = "\r\n".join(admin_notifications)
        self.send_email(self.recipient, self.sender, subject, content)

    def sync_group(self, ldap_group, group_notifications):
        edw_filters = EdwFilter()
        edw_filters.filter_class_codes(ldap_group.settings['members']['class_code'])
        edw_filters.filter_college(ldap_group.settings['members']['college_code'])
        edw_filters.filter_organization_codes(ldap_group.settings['members']['organization_codes'])
        edw_filters.filter_exclude_netids(ldap_group.settings['members']['exclude'])
        edw_filters.filter_grace_period(ldap_group.settings['members']['grace_period_days'])

        try:
            edw_employees = self.edw.get_employees(edw_filters)
        except Exception as e:
            group_notifications.append("Failed to load EDW Employees: " + str(e))
            self.notify()
            sys.exit(1)

        self.missing_from_ldap(edw_employees, ldap_group.employees, ldap_group.dn, group_notifications)
        self.missing_from_edw(edw_employees, ldap_group.employees, ldap_group.dn, group_notifications)

    def missing_from_ldap(self, edw_employees, ldap_employees, ldap_group_dn, notifications):
        on_board_employees = []
        missing = set(edw_employees) - set(ldap_employees)

        for employee in missing:
            try:
                if self.debug:
                    print("checking if " + employee.netid + " exists")
                employee_exists = self.ldap.exists(employee.netid)
            except Exception as e:
                notifications.append("Failed to check employee LDAP existence: " + str(e))
                self.notify()
                sys.exit(1)
            if employee_exists:
                if self.debug:
                    print("on-board: " + employee.email)
                notifications.append("on-board: " + employee.email)
                on_board_employees.append(employee)

        if len(on_board_employees) > 0 and self.sync_employees == True:
            try:
                self.ldap.add_users_to_group(on_board_employees, ldap_group_dn)
            except Exception as e:
                notifications.append("Failed to add users to LDAP group: " + str(e))

    def missing_from_edw(self, edw_employees, ldap_employees, ldap_group_dn, notifications):
        off_board_employees = []
        missing = set(ldap_employees) - set(edw_employees)
        for employee in missing:
            if self.debug:
                print("off-board " + employee.netid)
            notifications.append("off-board: " + employee.netid)
            off_board_employees.append(employee)

            try:
                ldap_membership = self.ldap.get_employee(employee.netid).memberOf
            except Exception as e:
                notifications.append("Failed to check LDAP membership for " + str(employee.netid) + ": " + str(e))
                return notifications

            if len(ldap_membership) > 0:
                self.message.append("\t* Remove From:")
                for group in ldap_membership:
                    notifications.append("\t\t- " + str(group))

        if len(off_board_employees) > 0 and self.sync_employees is True:
            try:
                self.ldap.delete_users_from_group(off_board_employees, ldap_group_dn)
            except Exception as e:
                notifications.append("Failed to delete users from LDAP group: " + str(e))

    def load_employees(self):
        self.load_edw_employees()
        self.load_ldap_employees()

    def load_edw_employees(self):
        # filters
        if self.orgCode is not None:
            self.edw.FilterOrganization(self.orgCode)

        self.edw.filter_college(self.colCode)

        if self.employeeTypeFilter == "Staff":
            self.edw.filter_staff()
        elif self.employeeTypeFilter == "Academic":
            self.edw.filter_faculty()

        # print employees
        try:
            self.edwEmployees = self.edw.get_employees()
        except Exception as e:
            self.message.append("Faild to load EDW Employees: " + str(e))
            self.notify()
            sys.exit(1)

    def load_ldap_employees(self):
        try:
            self.ldapEmployees = self.ldap.get_group_by_guid(self.ldapGuid).employees
        except Exception as e:
            self.message.append("Failed to get LDAP Employees (GUID: " + self.ldapGuid + "): " + str(e))
            self.notify()
            sys.exit(1)

    def connect_ldap(self, server, domain, account, password, authentication, path_root, user_dn):
        self.ldap = Ldap(server, domain, account, password, authentication, path_root)
        self.ldap.user_dn = user_dn
        self.ldap.debug = self.debug

        try:
            self.ldap.connect()
        except Exception as e:
            self.message.append("Failed to connect to LDAP: " + str(e))
            self.notify()
            sys.exit(1)

    def connect_edw(self, username, password, host, port, database):
        # setup EDW connection
        self.edw = Edw(username, password, host, port, database)
        self.edw.gracePeriodDays = self.gracePeriodDays

        try:
            self.edw.connect()
        except Exception as e:
            self.message.append("Failed to connect to to EDW: " + str(e))
            self.notify()
            sys.exit(1)

    def close_connections(self):
        self.edw.close_connection()
        self.ldap.close_connection()

    def notify(self):
        message_content = "\r\n".join(self.message)
        subject = "AD Group update Script"
        self.send_email(self.sender, self.recipient, subject, message_content)

    def send_email(self, recipients, sender, subject, message_content):
        msg = MIMEText(message_content, "plain")
        msg["Subject"] = subject
        msg["FROM"] = sender
        msg["To"] = recipients

        if len(message_content) > 0:
            if self.debug:
                print(msg.as_string())
            else:
                recipients_array = recipients.replace(" ", "").split(",")
                print("sending email: " + recipients)
                s = smtplib.SMTP("localhost")
                s.sendmail(sender, recipients_array, msg.as_string())
                s.quit()


def main():
    parser = argparse.ArgumentParser(description="Compare EDW to Active Directory Group")
    parser.add_argument("-d", "--edw-config", dest="edwConfigFile", type=str, required=False,
                        help="Config file for EDW connection")
    parser.add_argument("-l", "--ldap-config", dest="ldapConfigFile", type=str, required=False,
                        help="Config file for AD connection")
    parser.add_argument("-n", "--notify-config", dest="notifyConfig", type=str, required=False,
                        help="Config file for notification recipients")
    parser.add_argument("-g", "--ad-guid", dest="ldapGroupGuid", type=str, required=False,
                        help="Acive Dirctory GUID number for AD group to compare")
    parser.add_argument("-o", "--org-code", dest="edwOrgCode", type=str, required=False,
                        help="Filter by EDW Organization code (optional)")
    parser.add_argument("-c", "--col-code", dest="edwColCode", type=str, required=False,
                        help="EDW College Code EX: pharmacy is FX")
    parser.add_argument("-p", "--grace-period", dest="grace", type=int, required=False,
                        help="Grace period in days to apply to terminated employees to still appear as active")

    parser.add_argument("--sync", dest="syncEmployees", action="store_true",
                        help="Write EDW employees results differences to Active Directory group")
    parser.add_argument("--auto", dest="autoSearch", action="store_true",
                        help="Automatically scan active directory and update groups according to their json config")
    parser.add_argument("--notify", dest="notify", action="store_true",
                        help="Trigger an on-boarding off-boarding notifications")
    parser.add_argument("--debug", dest="debug", action="store_true", help="Print email message to stdout")
    args = parser.parse_args()

    employees = Employees()

    edw_config = configparser.ConfigParser()
    ldap_config = configparser.ConfigParser()
    notify_config = configparser.ConfigParser()

    if args.debug:
        print("enabled debug")
        employees.debug = args.debug

    ldap_config.read(args.ldapConfigFile)
    employees.connect_ldap(ldap_config.get('AD', 'server'),
                           ldap_config.get('AD', 'domain'),
                           ldap_config.get('AD', 'account'),
                           ldap_config.get('AD', 'password'),
                           ldap_config.get('AD', 'authentication'),
                           ldap_config.get('AD', 'path_root'),
                           ldap_config.get('AD', 'user_dn'))

    edw_config.read(args.edwConfigFile)
    employees.connect_edw(edw_config.get('EDW_DB', 'username'),
                          edw_config.get('EDW_DB', 'password'),
                          edw_config.get('EDW_DB', 'host'),
                          edw_config.get('EDW_DB', 'port'),
                          edw_config.get('EDW_DB', 'database'))

    notify_config.read(args.notifyConfig)
    employees.sender = notify_config.get('NOTIFY', 'sender')
    employees.recipient = notify_config.get('NOTIFY', 'recipients')

    if args.grace:
        employees.gracePeriodDays = args.grace

    if args.syncEmployees:
        employees.sync_employees = args.syncEmployees

    if args.autoSearch:
        employees.auto()
    else:
        if args.ldapGroupGuid:
            employees.ldapGuid = args.ldapGroupGuid

        if args.edwOrgCode:
            employees.orgCode = args.edwOrgCode

        if args.edwColCode:
            employees.colCode = args.edwColCode

        print("load employees")
        employees.load_employees()
        print("check missing from ldap")
        employees.missing_from_ldap()
        print("check missing from edw")
        employees.missing_from_edw()

    if args.notify and args.notifyConfig:
        employees.notify()

    print("Close Connection")
    employees.close_connections()


if __name__ == "__main__":
    main()
