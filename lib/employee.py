#! /usr/bin/env python

class Employee:

    def __init__(self, email, first_name=None, last_name=None, middle_name=None):
        self.netid = email.split('@')[0]
        self.email = email
        self.firstName = first_name
        self.lastName = last_name
        self.middleName = middle_name
        self.firstDay = None
        self.dn = None
        self.departments = []
        self.managedGroups = []

    def add_department(self, department):
        self.departments.append(department)

    def add_managed_group(self, group_dn):
        self.managedGroups.append(group_dn)

    def __eq__(self, other):
        return (self is other) or (self.netid == other.netid)

    def __hash__(self):
        return hash(self.netid)

    def __str___(self):
        return str(self.netid)

    def __repr__(self):
        return str(self.netid)
