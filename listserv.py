#!/usr/bin/env python

import smtplib
import argparse
import re
from email.mime.text import MIMEText


class ListServ:

    def __init__(self, server, list_name, owner, password, debug):
        self.server = server
        self.owner = owner
        self.password = password
        self.listName = list_name
        self.debug = debug
        self.commands = []

    def add_from_file(self, subscribers_file, list_name):
        subscribers = []
        add_email_list = "QUIET ADD " + list_name + " DD=USERS IMPORT PW=" + self.password + "\r\n//USERS DD *\r\n"
        for subscriber in subscribers_file:
            user = subscriber.split()
            if re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", user[0]):
                subscribers.append(" ".join(user))
            else:
                print user[0] + " is not a valid email"
        add_email_list = add_email_list + "\r\n".join(subscribers) + "\r\n/*"

        if self.verify_subscribers(subscribers) and self.verify_list_name(list_name):
            self.commands.append(add_email_list)
    
    def add_subscribers(self, employees, list_name):
        subscribers = []
        add_email_list = "QUIET ADD " + list_name + " DD=USERS IMPORT PW=" + self.password + "\r\n//USERS DD *\r\n"
        for employee in employees:
            if re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", employee.email):
                subscribers.append(employee.email)
        add_email_list += "\r\n".join(subscribers) + "\r\n/*"

        if self.verify_subscribers(subscribers) and self.verify_list_name(list_name):
            self.commands.append(add_email_list)

    def delete_subscribers(self, employees, list_name):
        subscribers = []
        delete_email_list = "QUIET DELETE " + list_name + " DD=USERS IMPORT PW=" + self.password + "\r\n//USERS DD *\r\n"
        for employee in employees:
            if re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", employee.email):
                subscribers.append(employee.email)
        delete_email_list += "\r\n".join(subscribers) + "\r\n/*"

        if self.verify_subscribers(subscribers) and self.verify_list_name(list_name):
            self.commands.append(delete_email_list)

    def delete_all_subscribers(self, list_name):
        clear_email_list = "QUIET DELETE " + list_name + " *@* PW=" + self.password
        if self.verify_list_name(list_name):
            self.commands.append(clear_email_list)

    @staticmethod
    def verify_subscribers(subscribers):
        if len(subscribers) == 0:
            print "No subscribers"
            return False
        return True

    @staticmethod
    def verify_list_name(list_name):
        if len(list_name) < 2:
            print "list name length is less than 2 charecters"
            return False
        return True
        
    def update(self):
        commands = "\r\n".join(self.commands)
        msg = MIMEText(commands ,"plain")
        msg["Subject"] = "auto script"
        msg["FROM"] = self.owner
        msg["To"] = self.server
        if self.debug:
            print msg.as_string()
        else:
            print "sending email"
            s = smtplib.SMTP("localhost")
            s.sendmail(self.owner, self.server, msg.as_string())
            s.quit()


def main():
    parser = argparse.ArgumentParser(description="update listserv subscribers from a text file")
    parser.add_argument("--add", dest="addList", action="store_true")
    parser.add_argument("--clear", dest="deleteList", action="store_true")
    parser.add_argument("--debug", dest="debug", action="store_true")
    parser.add_argument("-s", "--list-serv", dest="listserv", type=str, required=True, help="The listserv address EX: listserv@listserv.uic.edu")
    parser.add_argument("-l", "--list-name", dest="list", type=str, required=True, help="Which list should we manage EX: copstaff ")
    parser.add_argument("-o", "--owner-email", dest="owner", type=str, required=True,help="The owner of the list EX: nevoband@uic.edu")
    parser.add_argument("-p", "--password" , dest="ownerPass", type=str, required=True, help="The owners listserv password")
    parser.add_argument("listFile", type=argparse.FileType("r"))
    args = parser.parse_args()

    list_serv = ListServ(args.listserv, args.owner, args.ownerPass, args.debug)

    if args.deleteList:    
        list_serv.delete_all_subscribers(args.list)

    if args.addList:
        list_serv.add_from_file(args.listFile, args.list)

    list_serv.update()


if __name__ == "__main__":
    main()
