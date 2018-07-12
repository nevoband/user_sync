#!/usr/bin/env python

import argparse
import configparser
import sys
import json

from ldap3 import Server, Connection, SIMPLE, SYNC, ALL, SASL, SUBTREE, NTLM, BASE, ALL_ATTRIBUTES, Entry, Attribute, \
    MODIFY_ADD, MODIFY_DELETE, MODIFY_REPLACE
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
        self.connection = None

    def connect(self):
        ad_server = Server(self.server, get_info=ALL)
        self.connection = Connection(ad_server, user=self.domain + "\\" + self.account, password=self.password,
                                     authentication=self.auth, raise_exceptions=True)
        try:
            self.connection.bind()
        except Exception as e:
            raise

    def exists(self, net_id):
        if self.get_employee(net_id):
            return True

        return False

    def get_employee(self, net_id):
        filters = "(&(objectClass=user)(sAMAccountName=" + net_id + "))"

        self.connection.search(search_base=self.pathRoot, search_filter=filters, search_scope=SUBTREE,
                               attributes=[ALL_ATTRIBUTES], size_limit=0)

        if self.connection.entries and len(self.connection.entries) > 0:
            employee = Employee(str(self.connection.entries[0].mail), str(self.connection.entries[0].givenName),
                                str(self.connection.entries[0].sn))
            employee.dn = str(self.connection.entries[0].distinguishedName)

            if hasattr(self.connection.entries[0], 'managedObjects'):
                for group in self.connection.entries[0].managedObjects:
                    employee.add_managed_group(str(group))

            if hasattr(self.connection.entries[0], 'memberOf'):
                for group in self.connection.entries[0].memberOf:
                    employee.add_member_of(str(group))

            return employee

        return False

    def get_group(self, net_id):
        groups = []

        filters = "(member:1.2.840.113556.1.4.1941:={0})".format(
            escape_filter_chars("CN=" + net_id + "," + self.user_dn))

        if self.connection.bind():
            self.connection.search(search_base=self.pathRoot,
                                   search_filter=filters,
                                   search_scope=SUBTREE,
                                   attributes=["cn", "distinguishedName", "description"], size_limit=0)

            if self.connection.entries and len(self.connection.entries) > 0:
                for group in self.connection.entries:
                    groups.append(group.cn)

        return groups

    def get_employees_by_guid(self, group_guid):
        return self.get_group_by_guid(group_guid).employees

    def get_managed_groups_dn(self):
        employee = self.get_employee(self.account)
        return employee.managedGroups

    def get_group_by_dn(self, group_dn):
        ldap_filters = "(distinguishedName=" + str(group_dn) + ")"
        return self.get_group_by_filter(ldap_filters)

    def get_group_by_guid(self, group_guid):
        ldap_filters = "(objectGuid=" + str(group_guid) + ")"
        return self.get_group_by_filter(ldap_filters)

    def get_group_by_filter(self, ldap_filter):
        self.connection.search(search_base=self.pathRoot,
                               search_filter=ldap_filter,
                               search_scope=SUBTREE,
                               attributes=["objectGuid", "cn", "distinguishedName", "info", "member", "mail"],
                               # attributes = [ALL_ATTRIBUTES],
                               size_limit=0)

        if self.connection.entries and len(self.connection.entries) > 0:
            group = Group(str(self.connection.entries[0].distinguishedName), str(self.connection.entries[0].objectGuid))
            if self.connection.entries[0].info:
                try:
                    settings = json.loads(str(self.connection.entries[0].info))
                    if self.debug:
                        print(self.connection.entries[0])
                    group.settings = settings
                except ValueError as e:
                    e.message = "Group's Note field does not contain a valid json: " + e.message
                    raise

            if self.connection.entries[0].mail:
                group.mail = self.connection.entries[0].mail

            if self.connection.entries[0].member:
                for member in self.connection.entries[0].member:
                    employee = Employee(member.split(',')[0].split('=')[1] + '@uic.edu')
                    employee.dn = member
                    group.add_employee(employee)

            if self.debug:
                print("request: " + str(self.connection.request))
                print("response: " + str(self.connection.response))

            return group

        else:
            raise Exception("Group not found")

        return False

    def update_group_attribute(self, group_dn, attribute, value):
        if self.connection.bind():
            self.connection.modify(group_dn, {attribute: [(MODIFY_REPLACE, [value])]})

    def add_users_to_group(self, employees, group_dn):
        try:
            self.group_actions(employees, group_dn, 'add')
        except Exception as e:
            raise

    def delete_users_from_group(self, employees, group_dn):
        try:
            self.group_actions(employees, group_dn, 'delete')
        except Exception as e:
            raise

    def group_actions(self, employees, group_dn, action):
        if self.connection.bind():

            distinguished_names = []

            for employee in employees:
                if not employee.dn:
                    distinguished_names.append("CN=" + employee.netid + "," + self.user_dn)
                else:
                    distinguished_names.append(employee.dn)

            if action == 'delete':
                try:
                    self.connection.modify(group_dn, {'member': [(MODIFY_DELETE, distinguished_names)]})
                except Exception as e:
                    raise

            if action == 'add':
                try:
                    self.connection.modify(group_dn, {'member': [(MODIFY_ADD, distinguished_names)]})
                except Exception as e:
                    raise

            if self.debug:
                print("request" + str(self.connection.request))
                print("response" + str(self.connection.response))
        else:
            sys.exit("Failed LDAP Bind")

    def close_connection(self):
        try:
            self.connection.unbind()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Query Active directory")
    parser.add_argument("-c", "--config", dest="configFilePath", type=str, required=True, help="config.ini file path")
    parser.add_argument("-g", "--guid", dest="groupGuid", type=str, required=False,
                        help="get GUID of group you would like to pull members for")
    parser.add_argument("-n", "--netid", dest="netid", type=str, required=False,
                        help="if GUID is provided get all groups this netid is a member of otherwise get get ldap info of user")
    parser.add_argument("-l", "--groups-managed-by", dest="managedBy", type=str, required=False,
                        help="List groups managed by given netid")
    parser.add_argument("--debug", dest="debug", action="store_true", help="Print email message to stdout")
    parser.add_argument("--add-users", dest="addUsers", type=str, required=False,
                        help="provide a comma sperated list of netids to add to the group")
    parser.add_argument("--delete-users", dest="delUsers", type=str, required=False,
                        help="provide a comma sperated list of netids to remove from the group")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.configFilePath)

    ldap = Ldap(config.get('AD', 'server'),
                config.get('AD', 'domain'),
                config.get('AD', 'account'),
                config.get('AD', 'password'),
                config.get('AD', 'authentication'),
                config.get('AD', 'path_root'))

    ldap.user_dn = config.get('AD', 'user_dn')

    ldap.connect()

    if args.debug:
        ldap.debug = args.debug

    if args.addUsers:
        if args.groupGuid:
            employees = []
            for user in args.addUsers.split(','):
                employee = Employee(user)
                employees.append(employee)
                print(user)
            ldap.add_users_to_group(employees, args.groupGuid)
        else:
            print("no group guid given")

    if args.delUsers:
        if args.groupGuid:
            employees = []
            for user in args.delUsers.split(','):
                employee = Employee(user)
                employees.append(employee)
                print(user)
            ldap.delete_users_from_group(employees, args.groupGuid)
        else:
            print("no group guid given")

    if args.managedBy:
        if ldap.exists(args.managedBy):
            managedGroupsDN = ldap.get_managed_groups_dn(args.managedBy)
            if managedGroupsDN:
                managedGroups = []
                for groupDN in managedGroupsDN:
                    managedGroups.append(ldap.get_group_by_dn(groupDN))

                print(managedGroups)
            else:
                print("No groups managed by user")
        else:
            print("No AD account exists for: " + args.managedBy)

    if args.netid:
        if ldap.exists(args.netid):
            if args.groupGuid:
                ldap.get_group(args.netid)
            ldap.get_employee(args.netid)
        else:
            print("No AD account exists for: " + args.netid)
    else:
        if args.groupGuid:
            group = ldap.get_group_by_guid(args.groupGuid)
            print(str(group.dn))

    if args.netid:
        ldap.exists(args.netid)

    ldap.close_connection()

    # for employee in employees:
    # print(employee.email)


if __name__ == "__main__":
    main()
