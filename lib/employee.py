#! /usr/bin/env python

class Employee:

    def __init__(self, email, firstName=None, lastName=None, middleName=None):
        self.netid = email.split('@')[0]
        self.email = email
        self.firstName = firstName
        self.lastName = lastName
        self.middleName = middleName
        self.firstDay = None
        self.dn = None
        self.departments = []
        self.managedGroups = []

    def AddDepartment(self, department):
        self.departments.append(department)

    def AddManagedGroup(self, groupDN):
        self.managedGroups.append(groupDN)

    def __eq__(self, other):
        return (self is other) or (self.netid ==other.netid)

    def __hash__(self):
        return hash(self.netid)

    def __str___(self):
        return str(self.netid)

    def __repr__(self):
        return str(self.netid)
