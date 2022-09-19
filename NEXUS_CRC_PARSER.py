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
	Narendra Yerra nyerra@cisco.com
	R Likitha llikitha@cisco.com
	Richita Gajjar rgajjar@cisco.com
'''

import os
from tabulate import tabulate
from datetime import datetime
from termcolor import colored,cprint
import pandas as pd
import paramiko
import sys


class InvalidRangeError(Exception):
    pass


class InvalidInterface(Exception):
    pass


class InvalidFileFormatError(Exception):
    pass


#parses files which have nxos version < 10.2(1)
def compare1(file1,file2):
    dfs=[]
    for k in [file1,file2]:
        df= pd.DataFrame(columns=["input_errors" , "crc" ,"Align-Err","FCS-Err" , "02-RX Frm with FCS Err","16-RX Frm CRC Err(Stomp)"])
        for line in range(5, len(k)):
            if "Po" in k[line]:
                continue
            lst = k[line].split('|')
            if len(lst) == 9:
                df.loc[lst[1].strip()] = lst[2:8] 
        dfs.append(df)
    #calculating difference b/w first and second flie values
    df_diff =  pd.DataFrame(columns=[ "input_errors" , "crc" ,"Align-Err","FCS-Err" , "02-RX Frm with FCS Err","16-RX Frm CRC Err(Stomp)"])
    for i in dfs[0].index:
        df_diff.loc[i,"input_errors"]=int(dfs[1].loc[i,"input_errors"])-int(dfs[0].loc[i,"input_errors"])
        df_diff.loc[i,"crc"]=int(dfs[1].loc[i,"crc"])-int(dfs[0].loc[i,"crc"])
        df_diff.loc[i,"Align-Err"]=int(dfs[1].loc[i,"Align-Err"])-int(dfs[0].loc[i,"Align-Err"])
        df_diff.loc[i,"FCS-Err"]=int(dfs[1].loc[i,"FCS-Err"])-int(dfs[0].loc[i,"FCS-Err"])
        df_diff.loc[i,"02-RX Frm with FCS Err"]=int(dfs[1].loc[i,"02-RX Frm with FCS Err"])-int(dfs[0].loc[i,"02-RX Frm with FCS Err"])
        df_diff.loc[i,"16-RX Frm CRC Err(Stomp)"]=int(dfs[1].loc[i,"16-RX Frm CRC Err(Stomp)"])-int(dfs[0].loc[i,"16-RX Frm CRC Err(Stomp)"])
        #dropping the interfaces from the table if no values present
        if df_diff.loc[i,"input_errors"]==0 and df_diff.loc[i,"crc"]==0 and df_diff.loc[i,"Align-Err"]==0 and df_diff.loc[i,"FCS-Err"]==0 and df_diff.loc[i,"16-RX Frm CRC Err(Stomp)"] ==0 and df_diff.loc[i,"02-RX Frm with FCS Err"] ==0:
            df_diff=df_diff.drop(i)
            continue
        #checking for physical link issue 
        if df_diff.loc[i,"input_errors"]>0 or df_diff.loc[i,"crc"]>0 or df_diff.loc[i,"Align-Err"]>0 or df_diff.loc[i,"FCS-Err"]==0:
            df_diff.loc[i,"Remediation"]="This could be Physical Link Issue, SFP Issue or MTU Issue.\nContact Cisco TAC to troubleshoot further."
        #checking for physical layer problem
        if  df_diff.loc[i,"02-RX Frm with FCS Err"]>0:
            df_diff.loc[i,"Remediation"]="It is a physical layer problem.\nPlease Check for SFP and cabling"
        #checking for remote end issue
        elif df_diff.loc[i,"16-RX Frm CRC Err(Stomp)"]>0:
            df_diff.loc[i,"Remediation"]="Please ignore.\nThese are Stomped errors received from Remote end."
    #printing the results
    if len(df_diff)==0:
        c=colored("There are no incrementing CRC values, only historical values",'red','on_cyan')
        cprint(c)
    else:
        df_diff = tabulate(df_diff, headers=df_diff.columns.tolist(),tablefmt='grid')
        print(df_diff)

#parses files which have nxos version >= 10.2(1)
def compare2(file1,file2):
    dfs=[]
    for k in [file1,file2]:
        df= pd.DataFrame(columns=[ "Align-Err","FCS-Err" ,"StompedCRC","eth_crc","eth_stomped_crc"])
        for line in range(5, len(k)):
            if "Po" in k[line]:
                continue
            lst = k[line].split('|')
            if len(lst) == 8:
                df.loc[lst[1].strip()] = lst[2:7] 
        dfs.append(df)
    #calculating difference b/w first and second flie values
    df_diff =  pd.DataFrame(columns=[ "Align-Err","FCS-Err" ,"StompedCRC","eth_crc","eth_stomped_crc","Remediation"])
    for i in dfs[0].index:
        df_diff.loc[i,"Align-Err"]=int(dfs[1].loc[i,"Align-Err"])-int(dfs[0].loc[i,"Align-Err"])
        df_diff.loc[i,"FCS-Err"]=int(dfs[1].loc[i,"FCS-Err"])-int(dfs[0].loc[i,"FCS-Err"])
        df_diff.loc[i,"StompedCRC"]=int(dfs[1].loc[i,"StompedCRC"])-int(dfs[0].loc[i,"StompedCRC"])
        df_diff.loc[i,"eth_crc"]=int(dfs[1].loc[i,"eth_crc"])-int(dfs[0].loc[i,"eth_crc"])
        df_diff.loc[i,"eth_stomped_crc"]=int(dfs[1].loc[i,"eth_stomped_crc"])-int(dfs[0].loc[i,"eth_stomped_crc"])
        #dropping the interfaces from the table if no values present
        if df_diff.loc[i,"Align-Err"]==0 and df_diff.loc[i,"FCS-Err"]==0 and df_diff.loc[i,"StompedCRC"]==0 and df_diff.loc[i,"eth_crc"]==0 and df_diff.loc[i,"eth_stomped_crc"]==0:
            df_diff=df_diff.drop(i)
            continue
        #checking for physical link issue 
        if df_diff.loc[i,"Align-Err"]>0 or df_diff.loc[i,"FCS-Err"]>0 or df_diff.loc[i,"StompedCRC"]>0:
            df_diff.loc[i,"Remediation"]="This could be Physical Link Issue, SFP Issue or MTU Issue.\nContact Cisco TAC to troubleshoot further."
        #checking for physical layer problem
        if df_diff.loc[i,"eth_crc"]>0 and df_diff.loc[i,"eth_crc"]>=df_diff.loc[i,"eth_stomped_crc"]:
            df_diff.loc[i,"Remediation"]="It is physical layer problem.\nPlease Check for SFP and cabling."
        #checking for remote end issue
        elif df_diff.loc[i,"eth_stomped_crc"]>0 and df_diff.loc[i,"eth_crc"]<df_diff.loc[i,"eth_stomped_crc"]:
            df_diff.loc[i,"Remediation"]="Please ignore.\nThese are Stomped errors received from Remote end."
    #printing the results
    if len(df_diff)==0:
        print(colored("There are no incrementing CRC values, only historical values","green"))
    else:
        df_diff=tabulate(df_diff, headers=df_diff.columns.tolist(),tablefmt='grid')
        print(df_diff)

print("Please enter the folder where files are stored")
print("Please make sure we have at least two files exists in the directory where you have saved data ")

#####Checking whether the entered file format is valid ###########################
while(True):
    print("_____________________________________________________________")
    print("VALID folder format:")
    print("EXAMPLE:")
    print("Windows-> C:\\Users\Admin\Desktop\CRC\\")
    print("MAC -> /Users/admin/Desktop/CRC/")
    print("--------------------------------------------------------------------------------------------")
    print("PLEASE NOTE that data collection and script execution might get impacted if folder format is not as above")
    print("--------------------------------------------------------------------------------------------------------")
    try:
        LOCAL_PATH = input("Enter the absolute path of the folder where the files are stored:")
        if sys.platform.startswith('win') and not(LOCAL_PATH.endswith('\\')):
            raise InvalidFileFormatError
        if sys.platform.startswith('darwin') and not(LOCAL_PATH.endswith('/')):
            raise InvalidFileFormatError
        files = [file for file in os.listdir(LOCAL_PATH) if file.startswith('CRC_')]
    except InvalidFileFormatError:
        print(colored("!!!Invalid folder format, please enter valid path",'yellow'))
    except KeyboardInterrupt:
        print()
        inp=int(input("Do you want to terminate the program, 1-yes, 0-no (0/1):"))
        if inp==1:
            sys.exit()
        else:
            continue
    except:
        print(colored("!!!The system cannot find the path specified, please check the folder format or the folder exists",'yellow'))
    else:
        break
#checking files are available or not 
if len(files) == 0:
    print(colored("!!!Please validate the folder path or run script-1 to gather CRC_FCS data!!!",'yellow'))
    sys.exit()
else:
    print("___________________________________________________________")
    print("You have CRC files for the below date range")
    index = 1
    date_list = []
    #Sorting the files based on date&time
    sorted_files = sorted(
        [int(file.split('_')[1]+(file.split('_')[2].split('.')[0])) for file in files])
    sorted_files = [str(x) for x in sorted_files]
    for file in sorted_files:
        date = file[0:8]
        if date not in date_list:
            print(str(index)+"."+str(datetime.strptime(date, '%Y%m%d').date()))
            date_list.append(date)
            index = index+1
    
    ###########If multiple dates are avilable asking the user to select start and end date, else fetch from the same date########
    if(len(date_list) > 1):
        print("------------------------------------------------------------------")
        print("If you want data for same start and end date, enter the same value in below two inputs")
        while(True):
            print("------------------------------------------------------------")
            try:
                start = int(
                    input("Enter the start date(any number from the above listed (1-"+str(len(date_list))+")): "))
                end = int(
                    input("Enter the end date(any number from the above listed (1-"+str(len(date_list))+")): "))
                if((start >= 1 and start <= len(date_list)) and (end >= 1 and end <= len(date_list))):
                    break
                else:
                    raise InvalidRangeError
            except InvalidRangeError:
                print(colored("Invalid format/value,Please enter any number from the above listed (1-" +
                      str(len(date_list))+")): ",'yellow'))
            except KeyboardInterrupt:
                print()
                inp=int(input("Do you want to terminate the program, 1-yes, 0-no (0/1):"))
                if inp==1:
                    sys.exit()
                else:
                    continue
            except:
                print(colored("Invalid format,Please enter any number from the above listed (1-" +
                      str(len(date_list))+")): ",'yellow'))
            else:
                break
        if start > end:
            start, end = end, start

        print("__________________________________________________________")
        print("Fetching first file of " +
              date_list[start-1]+" and end file of "+date_list[end-1])
    else:
        print("Fetching first and last file of the same date "+date_list[0])

    if(len(sorted_files) == 1):
        start_file = "CRC_" +sorted_files[0][0:8]+"_"+sorted_files[0][8:]+".txt"
        end_file = start_file = "CRC_" +sorted_files[0][0:8]+"_"+sorted_files[0][8:]+".txt"
    else:
        if len(date_list)==1: 
            start_files=[x for x in sorted_files if x[0:8]==date_list[0]]
            end_files=[x for x in sorted_files if x[0:8]==date_list[0]]
            start_file="CRC_" + start_files[0][0:8]+"_"+start_files[0][8:]+".txt"
            end_file="CRC_" + end_files[-1][0:8]+"_"+end_files[-1][8:]+".txt"
        else:
        ##Getting the first file of start date and last file of end date
            start_files=[x for x in sorted_files if x[0:8]==date_list[start-1]]
            end_files=[x for x in sorted_files if x[0:8]==date_list[end-1]]
            start_file="CRC_" + start_files[0][0:8]+"_"+start_files[0][8:]+".txt"
            end_file="CRC_" + end_files[-1][0:8]+"_"+end_files[-1][8:]+".txt"

    print(start_file)
    print(end_file)
    fp1 = open(LOCAL_PATH+start_file, "r")
    file1=fp1.readlines()
    fp2 = open(LOCAL_PATH+end_file, "r")
    file2=fp2.readlines()
    version1 = file1[0][10:]
    version2 = file2[0][10:]
    hostname1 = file1[1][11:]
    hostname2 = file2[1][11:]
    if hostname1 != hostname2:
        print('\033[91m' + "Looks like you are comparing data of two different switches - " + '\033[1m' + hostname1[:-1] + '\033[0m' + '\033[91m' + " and "+ '\033[1m' +  hostname2[:-1]+ '\033[0m' + '\033[91m' + " !!!" + "\nPlease ensure that you provide files from same switch for data evaluation!" + '\033[0m')
        sys.exit()
    elif version1 != version2:
        print('\033[91m' + "It looks like switch " + '\033[1m' + "version" + '\033[0m' + '\033[91m' " has changed in-between data collection.\nMake sure that you are comparing recent files of switch for proper evaluation of CRC.\nRun Poller script again to collect latest data!" +  '\033[0m')
        sys.exit()
    #checking the version
    v=""
    for i in version1:
        if i=="(":
            break
        else:
            v+=i
    v=float(v)
    f=2
    if v<10.2:
        f=1
    print("__________________________________________________________")
    print("The script is executing.....")
    print("Version:",version1,end="")
    print("Hostname:",hostname1)
    if f==1:
        compare1(file1,file2)
    else:
        compare2(file1,file2)
    fp1.close()
    fp2.close()
