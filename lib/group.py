#! /usr/bin/env python


class Group:

    def __init__(self, dn, guid):
        self.dn = dn
        self.guid = guid
        self.employees = []
        self.settings = ""
        self.mail = ""

    def add_employee(self, employee):
        self.employees.append(employee)

    def to_string(self):
        group_string = "\nGROUP DETAILS:\n" + "Group DN: " + self.dn + "\n" + "Group GUID: " + self.guid + "\n" + "Group Json Settings: " + str(self.settings) + "\n"

        group_string += "\nEMPLOYEES:\n"
        if self.employees:
            for employee in self.employees:
                group_string += str(employee) + "\n"
       
        return group_string

    @staticmethod
    def __get_default_config():
        return { 'script_status' : 'disabled', 'checksum' : '', 'updated' : '', 'listserv' : { 'include' : [], 'exclude' : [] }, 'members' : { 'class_code' : [], 'college_code' : [], 'organization_codes' : [], 'include' : [], 'exclude' : [], 'grace_period_days' : 0 } }       
 
    def __str___(self):
        return self.to_string()

    def __repr__(self):
        return self.to_string()

