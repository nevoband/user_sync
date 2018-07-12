#! /usr/bin/env python


class EdwFilter:

    def __init__(self):
        self.conditionals = []
        self.filterDict = {}
        self.filterInc = 0

    def add_filter(self, conditional, filter_dict=None):
        self.conditionals.append(str(conditional))

        if filter_dict:
            self.filterDict.update(filter_dict)

        self.filterInc += 1

    def filter_class_codes(self, class_codes):
        class_code_conditionals = []
        class_code_filter_dict = {}
        if len(class_codes) > 0:
            for idx, classCode in enumerate(class_codes):
                if "%" not in class_codes:
                    class_code_conditionals.append("V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD LIKE :class_code_" + str(idx))
                else:
                    class_code_conditionals.append("V_JOB_DETL_HIST_1.JOB_DETL_EMPEE_CLS_CD = :class_code_" + str(idx))
                class_code_filter_dict["class_code_" + str(idx)] = str(classCode)
            self.add_filter("( " + ' OR '.join(class_code_conditionals) + " )", class_code_filter_dict)

    def filter_college(self, college_code):
        college_conditional = "V_JOB_DETL_HIST_1.JOB_DETL_COLL_CD = :coll_code"
        college_filter_dict = {"coll_code": str(college_code)}
        self.add_filter(college_conditional, college_filter_dict)

    def filter_exclude_netids(self, netids):
        exclude_netid_conditionals = []
        exclude_netid_dict = {}
        if len(netids) > 0:
            for idx, netid in enumerate(netids):
                exclude_netid_conditionals.append("V_EMPEE_CAMPUS_EMAIL_ADDR.EMAIL_ADDR NOT LIKE :netid_exclude_" + str(idx))
                exclude_netid_dict["netid_exclude_" + str(idx)] = str(netid) + '@%'
            self.add_filter(" AND ".join(exclude_netid_conditionals), exclude_netid_dict)

    def filter_organization_codes(self, org_codes):
        org_conditionals = []
        org_dict = {}
        if len(org_codes) > 0:
            for idx, org_code in enumerate(org_codes):
                org_conditionals.append("V_JOB_DETL_HIST_1.ORG_CD = :org_code_" + str(idx))
                org_dict[":org_code_" + str(idx)] = str(org_code)
            self.add_filter("(" + " OR ".join(org_conditionals) + ")", org_dict)

    def filter_grace_period(self, days):
        self.filterDict.update({'grace_period': days})
