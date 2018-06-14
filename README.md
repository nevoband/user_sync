# README #

#### Read the code, do not use blindly this is super alpha code.
This project is still under construction edw.py, ldap.py and listserv.py are pretty much working
I wouldn't trust listserv.py though since I haven't fully tested it in production
Just sharing incase someone wants to write some integration with EDW, Active Directory or ListServs

### What is this repository for? ###

* Scripts to query UIC EDW and Active Directory
* Can be used to compare AD group to EDW queries based on Academic/Staff positions and Organizational codes
* Version (0.4)
* [Learn Markdown](https://bitbucket.org/tutorials/markdowndemo)

### How do I get set up? ###

* Clone this repo to your computer
* Install the oracle client http://www.oracle.com/technetwork/database/database-technologies/instant-client/overview/index.html
	* For linux download:
		* oracle-instantclient12.2-basic-12.2.0.1.0-1.x86_64.rpm
		* oracle-instantclient12.2-devel-12.2.0.1.0-1.x86_64.rpm 
* setup cx_Oracle with Python
	* sudo  pip install cx_Oracle 
* Run either commands to learn more about usage:
	* run ./edw.py -h
	* run ./ldap.py -h
	* run ./listerv.py -h
	* run ./employees.py -h
		* Example: ./employees.py --edw-config /home/nevoband/configs/db_config.ini --ad-config /home/nevoband/configs/ad_config.ini --notify-config /home/nevoband/configs/notify_config.ini --col-code FX --ad-guid 80120a64-6725-4896-9829-e57d65ba1a28 --notify
* See copy and modify configs from configs folder for each service
* EDW:
	* https://www.aits.uillinois.edu/access/get_access/get_data_warehouse_access
	* You will need to request access to the EDW tables:
		* V_JOB_DETL_HIST_1
		* V_EMPEE_HIST_1
		* V_EMPEE_CAMPUS_EMAIL_ADDR
		* V_EMPEE_PERS_HIST_1 (May deprecate this table since you usually don't need first and last name for anything)
	* Settings for EDW:
		* database = DSPROD01
		* username = (Your assigned EDW username, or service account password)
		* password = (Generated EDW password NOT UIC password)
		* host = chirptbd.admin.uillinois.edu
		* port = 2721
* Listservs
	* https://listserv.uic.edu
	* You will need to use your listserv password not your UIC password
	* Not password will be sent over postfix in plain text, that's how listserv works unfortunately 
	* I think there is an API but it's extremly in efficient and listserv themselves recommend updating via EMail commands
* Active Directory
	* Settings for UIC:
		* server = ad.uic.edu
		* domain = AD
		* account = (Read only service account with access only to groups you want to read)
		* password = (AD password for service account)
		* authentication = NTLM
		* path_root = ou=pharm,ou=depts,dc=ad,dc=uic,dc=edu
        * Store settings in AD Group
                * Add a json to the note field:
<code>
                {
    "listserv" :
 {
    
        "include" : ["nevoband@gmail.com","nevoband@illinois.edu"],
    
        "exclude" : ["nevoband@uic.edu"]
  
    }


}
</code>
### Contribution guidelines ###

* Writing tests
* Code review
* Other guidelines

### Who do I talk to? ###

* Nevo Band nevoband@uic.edu
