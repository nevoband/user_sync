#! /usr/bin/env python


class Group:

    def __init__(self, dn, guid):
        self.dn = dn
        self.guid = guid
        self.employees = []
        self.settings = None
        self.mail = ""

    def add_employee(self, employee):
        self.employees.append(employee)

    def verify_settings(self):
        json_errors = []
        if self.settings is None:
            json_errors.append('no json settings found')
        if 'script_enabled' not in self.settings:
            json_errors.append('no script_enabled attribute found')
        if 'members' not in self.settings:
            json_errors.append('members attribute is missing from json settings')
        if 'college_code' not in self.settings['members']:
            json_errors.append("college_code attribute is missing")
        if 'college_code' in self.settings['members']:
            if self.settings['members'].get('college_code') is None:
                json_errors.append("college_Code attribute does not have a value")
        if 'sharepoint' in self.settings:
            if 'list_name' not in self.settings['sharepoint']:
                json_errors.append("sharepoint missing list_name in sharepoint")
            if 'subsite_name' not in self.settings['sharepoint']:
                json_errors.append("sharepoint missing subsite_name from sharepoint settings")
            if 'columns' not in self.settings['sharepoint']:
                json_errors.append("sharepoint missing columns in sharepoint settings")
            if 'user_added' not in self.settings['sharepoint']['columns']:
                json_errors.append("sharepoint missing user_added section in columns")
            if 'user_removed' not in self.settings['sharepoint']['columns']:
                json_errors.append("sharepoint missing user_removed section in columns")
        if 'listserv' in self.settings:
            if 'list_name' not in self.settings['listserv']:
                json_errors.append("missing list_name attribute for listserv")
        return json_errors

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

