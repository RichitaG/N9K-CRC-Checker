# Nexus9K CRC Checker


**Overview:**  
The purpose of this script is to automate identification of ports generating CRC /FCS errors in Nexus 9200 & 9300 Cloud Scale switches and identify if port is having L1 issue or it's just forwarding stompped packets.

Cisco 9000 series switch run in cut-through switching mode, by default. Whenever switch receives corrupt frame, it doesn't drop the frame. Rather it stomps the packet and keeps forwarding it. 
Thus, multiple interfaces may see CRC errors, however faulty L1 issue may lie with any one interface in the path.
Various counters needs to be looked upto to isolate problematic Port /SFP /Cable.
This CRC tracing and identification is now automated for Nexus 9200 & 9300 Cloud Scale switches to ease troubleshooting. 

There are two scripts. 
Poller script collects interface error counters at timely intervals. 
Parser script analyses the output collected in first script and generates tabular output with remediation (whether interface is source of the error or is it forwarding already stompped packets).


---
**Prerequisites on client machine from where script will be executed:**  

1. Python3  
2. Network access to Nexus Switches   
3. Nexus_CRC_requirements.txt attached to be installed in client machine. 
(This is a one time setup in clinet jumphost. Thist step installs required python libraries to jump-host)
  
        Follow below steps to install requirements.txt:  
        1. Download requirements.txt  
        2. Open terminal window  
        3. Navigate to folder where requirements.txt is located and run below command:  
            #pip install -r Nexus_CRC_requirements.txt  

<img width="1200" alt="image" src="https://user-images.githubusercontent.com/93187517/190986614-69172f23-d9af-42ae-98b2-b9416c6280e6.png">


	Upon successful installation, it shows message as below:
		Successfully installed DateTime-4.3 numpy-1.21.2 pandas-1.3.2 paramiko-2.7.2 python-dateutil-2.8.2 stdiomask-0.0.5 tabulate-0.8.9 termcolor-1.1.0  


---

**Script tested on:**  

*  Windows-10 64Bit  
*  MAC Monterey  

  
--- 

**Applicable Platforms: Nexus 9200/9300 Fixed Switches**

*  N9K-C92160YC-X
*  N9K-C92300YC
*  N9K-C92304QC
*  N9K-C92348GC-X
*  N9K-C9236C
*  N9K-C9272Q
*  N9K-C9332C
*  N9K-C9364C
*  N9K-C93108TC-EX
*  N9K-C93108TC-EX-24
*  N9K-C93180LC-EX
*  N9K-C93180YC-EX
*  N9K-C93180YC-EX-24
*  N9K-C93108TC-FX
*  N9K-C93108TC-FX-24
*  N9K-C93180YC-FX
*  N9K-C93180YC-FX-24
*  N9K-C9348GC-FXP
*  N9K-C93240YC-FX2
*  N9K-C93216TC-FX2
*  N9K-C9336C-FX2
*  N9K-C9336C-FX2-E
*  N9K-C93360YC-FX2
*  N9K-C93180YC-FX3
*  N9K-C93108TC-FX3P
*  N9K-C93180YC-FX3S
*  N9K-C9316D-GX
*  N9K-C93600CD-GX
*  N9K-C9364C-GX
*  N9K-C9364D-GX2A
*  N9K-C9332D-GX2B
---

**Execution:**

Interface CRC and FCS counter detail needs to be collected at periodic interval to see if errors are historic or live.  

Script execution is divided in two parts where,  
1.	script-1(Poller) will collect Interface error data in files every 10-30 for maximum upto seven days of duration.  
2.	script-2(Parser) will analyse these outputs and give tabular output listing interfaces which are source of Error, as well interfaces which are just forwarding the stomped packets. 

_Make sure you have all the pre-requisites installed in system_


**Execution sequence:**  

**Script-1:**  

    Execute " NEXUS_CRC_POLLER.py" to collect Interface errors in domain.  
        
    Inputs:
        1. Nexus Switch IP /FQDN, Username and password
        
<img width="452" alt="image" src="https://user-images.githubusercontent.com/93187517/190986559-fbe17894-9202-44cc-a773-b1f0df071043.png">


        2. Path to the folder where you want to save files  
                VALID folder format:  
                EXAMPLE:  
                    Windows-> C:\Users\Admin\Desktop\Nexus\   
                    MAC -> /Users/admin/Desktop/Nexus/  
    **PLEASE NOTE that data collection and script execution might get impacted if folder format is not as above. Also make sure that folder where you want to save files already exists**  

<img width="1200" alt="image" src="https://user-images.githubusercontent.com/93187517/190986526-08c212b8-1d9a-419d-8b80-5126f09dd41a.png">


            
        3. Duration for which you want to run the script:  
        	Maximum allowed duration is upto seven days
		Minimum one should run for atleast 30minutes to collect CRC differencial counters and error increments
    **Script collects Interface errors every 10 to 30 minutes and saves data to files at the path specified in earlier input. It will collect data for the duration given in this input**  
    
<img width="1170" alt="image" src="https://user-images.githubusercontent.com/93187517/191009817-76ea0179-30d5-4707-b378-bfdc24310f76.png">



	4. If there are no errors in the domain, it will ask if user still wants to continue and collect data once more

<img width="1200" alt="image" src="https://user-images.githubusercontent.com/93187517/190986443-68772681-29b7-443e-a1aa-b37f308fdd54.png">


		   	
**Script-2:**  
_Keep your terminal sesssion font resolution to 100% for proper tabular output view_

    "NEXUS_CRC_PARSER.py" will analyse the data and give you tabular output with interfaces having error and will also provide remediation actions.
    Script-2 execution should be started once we at-least have two files to compare data.
    i.e. script-2 execution should be started after approx 30 minutes of script-1 execution.  
     Script-2 is going to use those files created by script-1 and work further.
     
    Inputs:  
    1.	Enter the same file location, where you have collected data from Script-1.

	Enter the absolute path of the folder where the files are stored:/Users/rgajjar/Desktop/CRC_NEXUS/ <<<<<<<
	
Sample Execution and Output table for switch running on version >=10.2:
        
<img width="1200" alt="image" src="https://user-images.githubusercontent.com/93187517/190986125-73094471-2be4-4cc5-87fa-1cc5b10450d1.png">

	

Sample Execution and Output table for switch running on version < 10.2::

	
<img width="1200" alt="image" src="https://user-images.githubusercontent.com/93187517/190980372-c88e4c8b-f186-4a9b-8d61-f11e4df33550.png">


**Reference Documents:**
For further logical understanding of N9K CRC troubleshooting, refer: https://www.cisco.com/c/en/us/support/docs/switches/nexus-9000-series-switches/216239-nexus-9000-cloud-scale-asic-crc-identifi.html#anc12

---
   
            

**Contributors:** 
- Partha Dasgupta <padasgup@cisco.com>
- Richita Gajjar <rgajjar@cisco.com>
- Narendra Yerra <nyerra@cisco.com>
- R Likitha <llikitha@cisco.com>


**Company:**  
- Cisco Systems, Inc.  

**Version:**  
- v1.0  

**Date:**  
- 19th Sep, 2022  

**Disclaimer:**  
- Code provided as-is.  No warranty implied or included.  Use the code for production at your own risk.
