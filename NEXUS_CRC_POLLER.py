'''
###########################################################################
Copyright (c) 2022 Cisco and/or its affiliates
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
###########################################################################
Version: v1.0
Created on: 19th Sep, 2022
Supported Jump-host OS Platforms: Windows, MAC
Script Tested on: 
    Windows-10 64Bit
    MAC Monterey
Authors:
    Partha Dasgupta padasgup@cisco.com
    Richita Gajjar rgajjar@cisco.com
    Narendra Yerra nyerra@cisco.com
    R Likitha llikitha@cisco.com
	
'''

from distutils.version import Version
import stdiomask
import paramiko
from datetime import datetime, timedelta
import pandas as pd
import sys
import os
from tabulate import tabulate
import re
from termcolor import colored
from time import time, sleep
from paramiko.ssh_exception import AuthenticationException, SSHException

#ssh client connection
ssh = paramiko.SSHClient()

#creating ssh connection to switch
def connect_nexus(ip_address, admin_username, admin_password):
    print("Trying to connect to Nexus...")
    try:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=ip_address, username=admin_username, password=admin_password)
        print("Connection established to the Nexus")
    except AuthenticationException:
        print("Authentication failed, please verify your credentials:")
        print("Connection to the Nexus failed !!!")
        exit()
    except:
        print("Connection to the Nexus failed !!!")
        print("Verify the domain is up and re-run the script")
        exit()

class MaxexceedError(Exception):
    pass

class PastTimeError(Exception):
    pass

class InvalidFileFormatError(Exception):
    pass

#collecting files which have nxos version < 10.2(1)
def crc1(outFileName,version,host_name):
    #collecting interfaces information
    crc_command = 'show interface | grep -A 40 "Ethernet" | egrep "Ethernet|CRC|input error" | grep -v Hardware'
    stdin, stdout, stderr = ssh.exec_command(crc_command)
    all_interfaces=stdout.read().decode("utf-8",'ignore')
    all_interfaces=re.findall("(Ethernet.*?ignored)",all_interfaces,re.DOTALL)
    interfaces={}
    for k in all_interfaces:
        a={}
        a['input_errors']=re.search("(\d+).input error",k).group(1)    
        a['crc']=re.search("(\d+).CRC",k).group(1)
        interfaces["Eth"+re.search("Ethernet(\d+/\d+)",k).group(1)]=a
    #collecting conter errors
    crc_command = "show interface counters errors non-zero"
    stdin, stdout, stderr = ssh.exec_command(crc_command)
    interface_counters = stdout.readlines()
    counter_errors = {}
    if len(interface_counters[4].split())==0:
        user_query = input("No errors in the Switch, do you still want to run the script(y/n):")
        if user_query.lower() == "y":
            print("Script will only generate files if errors are generated in given time range of script execution")
            print("..............")
            return
        else:
            sys.exit()
    else:
        crc_command = "show interface counters errors"
        stdin, stdout, stderr = ssh.exec_command(crc_command)
        interface_counters = stdout.readlines()
        for i in range(5,len(interface_counters)):
            interface_counters[i]=interface_counters[i].split()
            if len(interface_counters[i])==0 or "-" in interface_counters[i][0] or  "Po" in interface_counters[i][0]:
                break
            if "mgmt0" in interface_counters[i]:
                continue
            interfaces[interface_counters[i][0]]["Align-Err"]=int(interface_counters[i][1])
            interfaces[interface_counters[i][0]]["FCS-Err"]=int(interface_counters[i][2])
    #collecting hardware mappings
    crc_command = "show interface hardware-mappings"
    stdin, stdout, stderr = ssh.exec_command(crc_command)
    mappings = stdout.readlines()
    hardware_mappings = {}
    for i in mappings:
        i=i.split()
        if len(i)==16 and i[0]!="Name":
            a={}
            a["Unit"] = i[3]
            a["MacId"] = i[11]
            a["MacSP"] = i[12]
            hardware_mappings[i[0]]=a
    for x in hardware_mappings:
        crc_command = "slot "+x[3]+" show hardware internal tah counters asic "+hardware_mappings[x]["Unit"] 
        stdin, stdout, stderr = ssh.exec_command(crc_command)
        a= stdout.read().decode("utf-8",'ignore')
        a=a.split("\n")
        crc_counter = "M"+hardware_mappings[x]["MacId"]+","+hardware_mappings[x]["MacSP"]
        k=-1
        d={}
        for i in a:
            if 'REG' in i and crc_counter in i:
                i=i.split()
                for j in range(len(i)):
                    if i[j][0:len(crc_counter)]==crc_counter:
                        k=len(i)-j
            if 'REG' in i or k<0:
                continue
            if k>=0 and  '02-RX Frm with FCS Err' in i:
                i=i.split()
                if i[len(i)-k]=="....":
                    interfaces[x]["02-RX Frm with FCS Err"]=0
                else:
                    interfaces[x]["02-RX Frm with FCS Err"]=int(i[len(i)-k])
            if k>=0 and '16-RX Frm CRC Err(Stomp)' in i:
                i=i.split()
                if i[len(i)-k]=="....":
                    interfaces[x]["16-RX Frm CRC Err(Stomp)"]=0
                else:
                    interfaces[x]["16-RX Frm CRC Err(Stomp)"]=int(i[len(i)-k])
                k=-1
                break
    #creating a table with the values collected
    a = pd.DataFrame.from_dict(interfaces)
    a=a.T
    a=tabulate(a, headers=a.columns.tolist(),tablefmt='pretty')
    #writing into the file on Jumphost
    outFile = open(outFileName, "w")
    outFile.writelines("Version : "+version+"\n")
    outFile.writelines("HostName : "+host_name+"\n")
    outFile.writelines(a)
    outFile.close()
    print(outFileName,"is created")

#collecting files which have nxos version > 10.2(1)
def crc2(outFileName,version,host_name):
    #collecting interfaces information
    crc_command = 'show interface | grep -A 40 "Ethernet" | grep -v Hardware | egrep "Ethernet|CRC|input error|Stomped" '
    stdin, stdout, stderr = ssh.exec_command(crc_command)
    all_interfaces=stdout.read().decode("utf-8",'ignore')
    all_interfaces=re.findall("(Ethernet.*?Stomped CRC)",all_interfaces,re.DOTALL)
    crc_interfaces=[]
    for k in all_interfaces:
        interface=dict()
        interface['Interface']=re.search("Ethernet(\d+/\d+)",k).group(1)
        interface['input_errors']=re.search("(\d+).input error",k).group(1)    
        interface['crc']=re.search("(\d+).CRC",k).group(1)
        interface['Stomped_crc']=re.search("(\d+).Stomped",k).group(1)
        crc_interfaces.append(interface)
    #collecting interfaces counters
    crc_command = "show interface counters errors non-zero"
    stdin, stdout, stderr = ssh.exec_command(crc_command)
    interface_counters = stdout.readlines()
    counter_errors = {}
    flag=1
    if len(interface_counters[4].split())==0:
        user_query = input("No errors in the Switch, do you still want to run the script(y/n):")
        if user_query.lower() == "y":
            print("Script will only generate files if errors are generated in given time range of script execution")
            print("Collecting data....")
            return
        else:
            sys.exit()
    else:
        crc_command = "show interface counters errors"
        stdin, stdout, stderr = ssh.exec_command(crc_command)
        interface_counters = stdout.readlines()
        for i in range(4,len(interface_counters)):
            interface_counters[i]=interface_counters[i].split()
            if len(interface_counters[i])==0  or  "Port" in interface_counters[i]:
                flag=0
            if "mgmt0" in interface_counters[i]:
                continue
            if "Stomped-CRC" in interface_counters[i]:
                flag = 2
                i=i+1
                continue
            if flag==1:
                a={}
                a["Align-Err"]=int(interface_counters[i][1])
                a["FCS-Err"]=int(interface_counters[i][2])
                counter_errors[interface_counters[i][0]]=a
            if flag == 2 and len(interface_counters[i]) !=1:        
                counter_errors[interface_counters[i][0]]["StompedCRC"]=int(interface_counters[i][1])
    for i in counter_errors:
        crc_command = "show interface "+i+" | json-pretty | include ignore-case crc"
        stdin, stdout, stderr = ssh.exec_command(crc_command)
        out=stdout.readlines()
        out[0]=out[0].split(":")
        out[1]=out[1].split(":")
        counter_errors[i][out[0][0].strip()[1:-1]]=out[0][1][2:-4]
        counter_errors[i][out[1][0].strip()[1:-1]]=out[1][1][2:-4]
    #creating a table with the values collected
    a = pd.DataFrame.from_dict(counter_errors)
    a=a.T
    a=tabulate(a, headers=a.columns.tolist(),tablefmt='pretty')
    # writing into the file
    outFile = open(outFileName, "w")
    outFile.writelines("Version : "+version+"\n")
    outFile.writelines("HostName : "+host_name+"\n")
    outFile.writelines(a)
    outFile.close()
    print(outFileName,"is created")

#creating file in jumphost and storing the values
def store(end_time):
    global flag3
    #collecting module info
    crc_command = "show module"
    stdin, stdout, stderr = ssh.exec_command(crc_command)
    out=stdout.read().decode("utf-8",'ignore')
    r=re.findall("(N9K.*?Mod) ",out,re.DOTALL)[0].split()[0]
    model=['N9K-C92160YC-X','N9K-C92300YC','N9K-C92304QC', 'N9K-C92348GC-X', 'N9K-C9236C', 'N9K-C9272Q', 'N9K-C9332C', 'N9K-C9364C', 'N9K-C93108TC-EX', 'N9K-C93108TC-EX-24', 'N9K-C93180LC-EX', 'N9K-C93180YC-EX', 'N9K-C93180YC-EX-24', 'N9K-C93108TC-FX', 'N9K-C93108TC-FX-24', 'N9K-C93180YC-FX', 'N9K-C93180YC-FX-24', 'N9K-C9348GC-FXP', 'N9K-C93240YC-FX2', 'N9K-C93216TC-FX2', 'N9K-C9336C-FX2', 'N9K-C9336C-FX2-E', 'N9K-C93360YC-FX2', 'N9K-C93180YC-FX3', 'N9K-C93108TC-FX3P', 'N9K-C93180YC-FX3S', 'N9K-C9316D-GX', 'N9K-C93600CD-GX', 'N9K-C9364C-GX', 'N9K-C9364D-GX2A', 'N9K-C9332D-GX2B']
    if r not in model:
        print("Logic is not implemented for this Switch Model")
        return
    print("Model : "+r)
    #collecting version info
    crc_command = "show version"
    stdin, stdout, stderr = ssh.exec_command(crc_command)
    out=stdout.read().decode("utf-8",'ignore')
    version = re.findall(r'NXOS: version ([0-9.()A-Z]*)',out)[0]
    print("Version : "+version)
    v=""
    for i in version:
        if i=="(":
            break
        else:
            v+=i
    v=float(v)
    f=2
    if v<10.2:
        f=1
    #collecting host info
    crc_command = "show switchname"
    stdin, stdout, stderr = ssh.exec_command(crc_command)
    host_name=stdout.read().decode("utf-8",'ignore')
    print("HostName : "+host_name)
    while(True):
        print("Collecting data........................")
        now = datetime.today()
        outFileName = LOCAL_PATH+"CRC_"+str(now.year) +             str('{:02d}'.format(now.month))+str('{:02d}'.format(now.day))+"_" +             str('{:02d}'.format(now.hour)) +             str('{:02d}'.format(now.minute))+".txt"
        # Execute the query
        if f==1:
            crc1(outFileName,version,host_name)
        else:
            crc2(outFileName,version,host_name)
        if(end_time < datetime.today()):
            break
        print(colored("Script will collect next set of interface counter values after 5-minutes !!!", 'yellow'))    
        sleep(60*5)
        

# Getting the required inputs
LOCAL_PATH=""
ip_address = input("Enter the IP address of Switch: ")
print("__________________________________________________________")
admin_username = input("Enter the username: ")
print("___________________________________________________________")
admin_password = stdiomask.getpass("Enter the password: ")
connect_nexus(ip_address, admin_username, admin_password)
print("___________________________________________________________")
print("Please enter the folder where files have to be stored")

#####Checking whether the entered file format is valid ###########################
while(True):
    print("_____________________________________________________________")
    print("VALID folder format:")
    print("EXAMPLE:")
    print("Windows-> C:\\Users\Admin\Desktop\CRC_NEXUS\\")
    print("MAC -> /User/admin/Desktop/CRC_NEXUS/")
    print("---------------------------------------------------------------------------------------------------")
    print("PLEASE NOTE that data collection and script execution might get impacted if folder format is not as below")
    print("--------------------------------------------------------------------------------------------------------")
    try:
        LOCAL_PATH = input(
        "Enter the absolute path of the folder where the files have to be stored:")

        if sys.platform.startswith('win') and not(LOCAL_PATH.endswith('\\')):
            raise InvalidFileFormatError
        if sys.platform.startswith('darwin') and not(LOCAL_PATH.endswith('/')):
            raise InvalidFileFormatError
        files = [file for file in os.listdir(LOCAL_PATH)] ###Just to check whether the script able to resolve folder name
    except InvalidFileFormatError:
        print(colored("!!!Invalid file format, please enter valid path",'yellow'))
    except:
        print(colored("!!!The system cannot find the path specified, please check the folder format or the folder exists",'yellow'))
    else:
        break
print("----------------------------------------------------------------")
print(colored("Enter end time of at-least 30 minutes to 1 hour after current time in order to collect interface counters at periodic interval !!!", 'yellow'))
now = datetime.today()
max_range = datetime.today()+timedelta(7)
while(True):
    end_time = input(
        "Enter the End Time until which the script runs(in the format of yyyy-mm-dd hh:mm, current time:"+str(now.year)+"-"+str('{:02d}'.format(now.month))+"-"+str('{:02d}'.format(now.day))+" "+str('{:02d}'.format(now.hour))+":"+str('{:02d}'.format(now.minute))+"....  maximum upto "+str(max_range.year)+"-"+str('{:02d}'.format(max_range.month))+"-"+str('{:02d}'.format(max_range.day))+" "+str('{:02d}'.format(max_range.hour))+":"+str('{:02d}'.format(max_range.minute))+"): ")
    print("___________________________________________________________")
    try:
        # Extracting date, hour and minute from the input
        date_tuple = tuple([int(x) for x in end_time[:10].split('-')]) + tuple([int(x) for x in end_time[11:].split(':')])
        endtimeobj = datetime(*date_tuple)
        if(endtimeobj < datetime.today()):
            raise PastTimeError
        if(endtimeobj > max_range):
            raise MaxexceedError
    except PastTimeError:
        print("The entered time is already passed")
    except MaxexceedError:
        print("The entered time range exceeds than max range")
        user_query = input(
            "Do you want to continue with the maximum showed range(y/n):")
        if user_query.lower() == "y":
            endtimeobj = max_range
            break
        else:
            continue
    except KeyboardInterrupt:
                print()
                inp=int(input("Do you want to terminate the program, 1-yes, 0-no (0/1):"))
                if inp==1:
                    sys.exit()
                else:
                    continue

    except:
        print(colored("!!!!Invalid time format",'yellow'))
        print(colored("!!!!Please enter in the format of yyyy-mm-dd hh:mm",'yellow'))
        print("-------------------------------------")

    else:
        break
store(endtimeobj)

ssh.close()
print(colored("Script execution completed for given time range. Run Parser script for evaluation of collected Data!!!",'green'))
sys.exit()


