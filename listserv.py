#!/usr/bin/env python

import smtplib
import argparse
import re
from email.mime.text import MIMEText

class ListServ:
    def __init__(self, server, listName, owner, password, debug):
        self.server = server
        self.owner = owner
        self.password = password
        self.listName = listName
        self.debug = debug
        self.commands = []
        self.subscribers = []

    def AddFromFile(self, subscribersFile):
        subscribers = []
        addEmailList = "QUIET ADD " + self.listName + " DD=USERS IMPORT PW=" + self.password + "\r\n//USERS DD *\r\n"
        for subscriber in subscribersFile:
            user = subscriber.split()
            if re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)",user[0]):
                self.subscribers.append(" ".join(user))
            else:
                print user[0] + " is not a valid email"
        addEmailList = addEmailList + "\r\n".join(self.subscribers) + "\r\n/*"
        self.commands.append(addEmailList)
    
    def AddFromEmployees(self, employees):
        subscribers = []
        for employee in employees:
            if re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)",employee.email):
                self.subscribers.append(employee.email)
        addEmailList = addEmailList + "\r\n".join(self.subscribers) + "\r\n/*"
                self.commands.append(addEmailList)            

    def ClearSubscribers(self):
        clearEmailList = "QUIET DELETE " + self.listName + " *@* PW=" + self.password
        self.commands.append(clearEmailList)

    def Verify(self):
        if len(self.subscribers) == 0:
            print "No subscribers"
            return false
        if len(self.listName) < 2:
            print "list name length is less than 2 charecters"
            return false
        return true
        
    def Update(self):
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
    parser = argparse.ArgumentParser(description="Update listserv subscribers from a text file")
    parser.add_argument("--add", dest="addList", action="store_true")
    parser.add_argument("--clear", dest="deleteList", action="store_true")
    parser.add_argument("--debug", dest="debug", action="store_true")
    parser.add_argument("-s", "--list-serv", dest="listserv", type=str, required=True, help="The listserv address EX: listserv@listserv.uic.edu")
    parser.add_argument("-l", "--list-name", dest="list", type=str, required=True, help="Which list should we manage EX: copstaff ")
    parser.add_argument("-o", "--owner-email", dest="owner", type=str, required=True,help="The owner of the list EX: nevoband@uic.edu")
    parser.add_argument("-p", "--password" , dest="ownerPass", type=str, required=True, help="The owners listserv password")
    parser.add_argument("listFile", type=argparse.FileType("r"))
    args = parser.parse_args()

    listserv = ListServ(args.listserv,args.list, args.owner, args.ownerPass, args.debug)
    if args.deleteList:    
        listserv.ClearSubscribers()
        if args.addList:
        listserv.AddFromFile(args.listFile)
    if listserv.Verify:
        listserv.Update()

if __name__ == "__main__":
    main()
