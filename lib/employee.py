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

	def __eq__(self, other):
		return (self is other) or (self.netid ==other.netid)

	def __hash__(self):
		return hash(self.netid)