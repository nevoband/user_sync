#! /usr/bin/env python
class Employee:
        def __init__(self, email, firstName=None, lastName=None, middleName=None):
		self.netid = email.split('@')[0]
                self.email = email
                self.firstName = firstName
                self.lastName = lastName
                self.middleName = middleName
                self.departments = []

        def AddDepartment(self, department):
                self.departments.append(department)
