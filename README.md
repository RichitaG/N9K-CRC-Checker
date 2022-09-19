# N9K-CRC-Checker

# Nexus9K-FCS-CRC Checker


**Overview:**  
The purpose of this script is to capture ports generating CRC or FCS errors in Nexus 9000 series switches.  
Nexus switches run in cut-through switching mode. Whenever switch receives corrupt frame, it stomps the packet and keeps forwarding it.  
If the error gets generated in Nexus switch itself, then it stomps the packet; as well adds FCS Error counter.  
If interface only has CRC counters, then it could be because of stomped packets and is usually not the source of error.  



---
**Prerequisites on client machine from where script will be executed:**  

1. Python3  
2. Network access to Nexus Switches   
3. Nexus_CRC_requirements.txt attached to be installed in client machine. 
(This is a one time setup to install required libraries to jump-host)
  
        Follow below steps to install requirements.txt:  
        1. Download requirements.txt  
        2. Open terminal window  
        3. Navigate to folder where requirements.txt is located and run below command:  
            #pip install -r Nexus_CRC_requirements.txt  
          
rgajjar@RGAJJAR-M-925B NEXUS_CRC_Latest % pip3 install -r NEXUS_CRC_Requirements.txt                                        
Defaulting to user installation because normal site-packages is not writeable
Collecting DateTime==4.3
  Using cached DateTime-4.3-py2.py3-none-any.whl (60 kB)
Collecting numpy==1.21.2
  Using cached numpy-1.21.2-cp38-cp38-macosx_10_9_x86_64.whl (16.9 MB)
Collecting pandas==1.3.2
  Using cached pandas-1.3.2-cp38-cp38-macosx_10_9_x86_64.whl (11.4 MB)
Collecting paramiko==2.7.2
  Using cached paramiko-2.7.2-py2.py3-none-any.whl (206 kB)
Collecting python-dateutil==2.8.2

**SNIP**

Successfully installed DateTime-4.3 numpy-1.21.2 pandas-1.3.2 paramiko-2.7.2 python-dateutil-2.8.2 stdiomask-0.0.5 tabulate-0.8.9 termcolor-1.1.0  
            


---

**Script tested on:**  

*  Windows-10 64Bit  
*  MAC Bigsur  

  
--- 

** Applicable Platforms: Nexus 9200/9300 Fixed Switches **

N9K-C92160YC-X
N9K-C92300YC
N9K-C92304QC
N9K-C92348GC-X
N9K-C9236C
N9K-C9272Q
N9K-C9332C
N9K-C9364C
N9K-C93108TC-EX
N9K-C93108TC-EX-24
N9K-C93180LC-EX
N9K-C93180YC-EX
N9K-C93180YC-EX-24
N9K-C93108TC-FX
N9K-C93108TC-FX-24
N9K-C93180YC-FX
N9K-C93180YC-FX-24
N9K-C9348GC-FXP
N9K-C93240YC-FX2
N9K-C93216TC-FX2
N9K-C9336C-FX2
N9K-C9336C-FX2-E
N9K-C93360YC-FX2
N9K-C93180YC-FX3
N9K-C93108TC-FX3P
N9K-C93180YC-FX3S
N9K-C9316D-GX
N9K-C93600CD-GX
N9K-C9364C-GX
N9K-C9364D-GX2A
N9K-C9332D-GX2B
---

**Execution:**

FCS and CRC counter detail needs to be collected at periodic interval to see if errors are historic or live.  

Script execution is divided in two parts where,  
1.	script-1(Poller) will collect CRC+FCS error data in files every five minutes for maximum upto seven days of duration.  
2.	script-2(Parser) will analyse these outputs and give tabular output listing interfaces which are source of Error, as well interfaces which are just forwarding the stomped packets.
    Additionally, one can also review more granular data on specific interface by giving relevant inputs.  

_Make sure you have all the pre-requisites installed in system_


**Execution sequence:**  

**Script-1:**  

    Execute " Nexus_CRC_Poller.py" to collect CRC+FCS errors in domain.  
        
    Inputs:
        1. Nexus Switch IP /FQDN, Username and password
        
rgajjar@RGAJJAR-M-925B NEXUS_CRC_Latest % python3 NEXUS_CRC_POLLER.py 
Enter the IP address of Switch: 10.78.51.89
__________________________________________________________
Enter the username: admin
___________________________________________________________
Enter the password: *********
Trying to connect to Nexus...
Connection established to the Nexus


        2. Path to the folder where you want to save files  
                VALID folder format:  
                EXAMPLE:  
                    Windows-> C:\Users\Admin\Desktop\Nexus\   
                    MAC -> /Users/admin/Desktop/Nexus/  
    **PLEASE NOTE that data collection and script execution might get impacted if folder format is not as above. Also make sure that folder where you want to save files already exists**  

___________________________________________________________
Please enter the folder where files have to be stored
_____________________________________________________________
VALID folder format:
EXAMPLE:
Windows-> C:\Users\Admin\Desktop\CRC_NEXUS\
MAC -> /User/admin/Desktop/CRC_NEXUS/
---------------------------------------------------------------------------------------------------
PLEASE NOTE that data collection and script execution might get impacted if folder format is not as below
--------------------------------------------------------------------------------------------------------
Enter the absolute path of the folder where the files have to be stored:/Users/rgajjar/Desktop/CRC_NEXUS/


            
        3. Duration for which you want to run the script:  
                Maximum allowed duration is upto seven days 
                Minimum valid duration is 5minutes. Even if user enters duration lesser than 5-minutes, script will run for 5-minutes and collect data in two files at the interval of 5-minutes.  
    **Script collects FCS+CRC error every five minutes and saves data to files at the path specified in earlier input. It will collect data for the duration given in this input**  
    
----------------------------------------------------------------
Enter the End Time until which the script runs(in the format of yyyy-mm-dd hh:mm, current time:2022-09-15 17:26....  maximum upto 2022-09-22 17:26): 2022-09-15 18:00
___________________________________________________________
Model : N9K-C9236C
Version : 7.0(3)I7(6)
HostName : RP 

Collecting data....

		4. If there are no errors in the domain, it will ask if user still wants to continue and collect data once more

No errors in the Switch, do you still want to run the script(y/n):y
Script will only generate files if errors are generated in given time range of script execution
Collecting data....

		   	
**Script-2:**  
_Keep your terminal sesssion font resolution to 100% for proper tabular output view_

    "Nexus_CRC_Parser.py" will analyse the data and give you tabular output with interfaces having error and will also provide remediation actions.
    Script-2 execution should be started once we at-least have two files to compare data.
    i.e. script-2 execution should be started after approx 30 minutes of script-1 execution.  
     Script-2 is going to use those files created by script-1 and work further.
     
    Inputs:  
    1.	Enter the same file location, where you have collected data from Script-1.

        
rgajjar@RGAJJAR-M-925B NEXUS_CRC_Latest % python3 NEXUS_CRC_PARSER.py
Please enter the folder where files are stored
Please make sure we have at least two files exists in the directory where you have saved data 
_____________________________________________________________
VALID folder format:
EXAMPLE:
Windows-> C:\Users\Admin\Desktop\CRC\
MAC -> /Users/admin/Desktop/CRC/
--------------------------------------------------------------------------------------------
PLEASE NOTE that data collection and script execution might get impacted if folder format is not as above
--------------------------------------------------------------------------------------------------------
Enter the absolute path of the folder where the files are stored:/Users/rgajjar/Desktop/CRC_NEXUS/
___________________________________________________________
You have CRC files for the below date range
1.2022-08-18
Fetching first and last file of the same date 20220818
CRC_20220818_1615.txt
CRC_20220818_1630.txt
__________________________________________________________
The script is executing.....
Version: 10.2(3)
Hostname: F.cisco.cm 

+---------+-------------+-----------+--------------+-----------+-------------------+------------------------------------------------------------+
|         |   Align-Err |   FCS-Err |   StompedCRC |   eth_crc |   eth_stomped_crc | Remediation                                                |
+=========+=============+===========+==============+===========+===================+============================================================+
| Eth1/14 |           0 |         0 |            0 |       345 |               673 | Please ignore.                                             |
|         |             |           |              |           |                   | These are Stomped errors received from Remote end.         |
+---------+-------------+-----------+--------------+-----------+-------------------+------------------------------------------------------------+
| Eth1/18 |           0 |         0 |            0 |       653 |               236 | It is physical layer problem.                              |
|         |             |           |              |           |                   | Please Check for SFP and cabling.                          |
+---------+-------------+-----------+--------------+-----------+-------------------+------------------------------------------------------------+
| Eth1/24 |         384 |         0 |           25 |         0 |                 0 | This could be Physical Link Issue, SFP Issue or MTU Issue. |
|         |             |           |              |           |                   | Contact Cisco TAC to troubleshoot further.                 |
+---------+-------------+-----------+--------------+-----------+-------------------+------------------------------------------------------------+
rgajjar@RGAJJAR-M-925B NEXUS_CRC_Latest % 


Talbe <10.2

rgajjar@RGAJJAR-M-925B NEXUS_CRC_Latest % python3 NEXUS_CRC_PARSER.py
Please enter the folder where files are stored
Please make sure we have at least two files exists in the directory where you have saved data 
_____________________________________________________________
VALID folder format:
EXAMPLE:
Windows-> C:\Users\Admin\Desktop\CRC\
MAC -> /Users/admin/Desktop/CRC/
--------------------------------------------------------------------------------------------
PLEASE NOTE that data collection and script execution might get impacted if folder format is not as above
--------------------------------------------------------------------------------------------------------
Enter the absolute path of the folder where the files are stored:/Users/rgajjar/Desktop/CRC_NEXUS/
___________________________________________________________
You have CRC files for the below date range
1.2022-09-11
Fetching first and last file of the same date 20220911
CRC_20220911_1115.txt
CRC_20220911_1132.txt
__________________________________________________________
The script is executing.....
Version: 9.2(3)
Hostname: switch

+--------+----------------+-------+-------------+-----------+--------------------------+----------------------------+------------------------------------------------------------+
|        |   input_errors |   crc |   Align-Err |   FCS-Err |   02-RX Frm with FCS Err |   16-RX Frm CRC Err(Stomp) | Remediation                                                |
+========+================+=======+=============+===========+==========================+============================+============================================================+
| Eth1/5 |            252 |     0 |           0 |      3534 |                     8635 |                       6455 | It is a physical layer problem.                            |
|        |                |       |             |           |                          |                            | Please Check for SFP and cabling                           |
+--------+----------------+-------+-------------+-----------+--------------------------+----------------------------+------------------------------------------------------------+
| Eth1/7 |            234 |   275 |         273 |         0 |                        0 |                       5344 | Please ignore.                                             |
|        |                |       |             |           |                          |                            | These are Stomped errors received from Remote end.         |
+--------+----------------+-------+-------------+-----------+--------------------------+----------------------------+------------------------------------------------------------+
| Eth1/9 |            535 |     0 |         935 |         0 |                        0 |                          0 | This could be Physical Link Issue, SFP Issue or MTU Issue. |
|        |                |       |             |           |                          |                            | Contact Cisco TAC to troubleshoot further.                 |
+--------+----------------+-------+-------------+-----------+--------------------------+----------------------------+------------------------------------------------------------+
   

** Reference Documents:**
For further logical understanding of N9K CRC troubleshooting, refer: https://www.cisco.com/c/en/us/support/docs/switches/nexus-9000-series-switches/216239-nexus-9000-cloud-scale-asic-crc-identifi.html#anc12

---
   
            

**Contributors:** 
- Partha Dasgupta <padasgup@cisco.com>
- Narendra Yerra <nyerra@cisco.com>
- R Likitha <llikitha@cisco.com>
- Richita Gajjar <rgajjar@cisco.com>


**Company:**  
- Cisco Systems, Inc.  

**Version:**  
- v1.0  

**Date:**  
- 22nd Aug, 2022  

**Disclaimer:**  
- Code provided as-is.  No warranty implied or included.  Use the code for production at your own risk.
