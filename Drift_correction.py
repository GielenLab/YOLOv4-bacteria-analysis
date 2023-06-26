# -*- coding: utf-8 -*-
"""
Created on Tue Apr  5 09:33:03 2022

@author: FGLab also see 
https://github.com/TheImagingSource/IC-Imaging-Control-Samples/tree/master/Python/tisgrabber/samples

"""

import ctypes
import tisgrabber as IC
import serial
import time
import cv2 as cv2
import numpy as np
import os
from cv2 import resize, imwrite, imshow
import csv
from shutil import copyfile

results_file=r'D:\Fabrice\IC-Imaging-Control-Samples-master (2)\IC-Imaging-Control-Samples-master\Python\Z focus drift correction\results.csv'

##########PARAMETERS TO ADJUST
step_size=5 # step size in 0.1 microns
nb_slices=28 #number of slices
total_nb=5000 # total number of time points
time_interval=10 # time interval between time points

exposure_time=4e-3
gain=0.0

tolerance=2
############################
with open(results_file, "w+") as f:
    f.write('focus history \n')

###
main_dir=os.getcwd()
image_dir = main_dir+'\Images'

ser=serial.Serial(
     port='COM3',
     baudrate=9600,
     timeout=1,
     bytesize=8,
     parity=serial.PARITY_NONE,
     stopbits=serial.STOPBITS_ONE,
     rtscts=False,
     dsrdtr=False,
     xonxoff=False
     )

print(ser.get_settings())
print(ser.name) 
print("OPENING port.")

if ser.isOpen()==False:
    ser.open()

ser.write(b"\r"); #return carriage to initialise comm
ser.flush() #make sure all is sent

ser.write(b"\r"); #second return carriage
ser.flush()

serialString=ser.readlines(16) #read output
print(serialString)

ser.write(b"\r")
ser.flush()

serialString=ser.read(16)
position=bytes.decode(serialString) #convert bytes to string
position_ini=int(position[4:10]) #crop useful number as it comes in form 0,0,number
position_ini2=bytes(str(position_ini),'utf-8') #convert bytes to string
print(position_ini)
         
step=bytes(str(step_size),'utf-8') #convert to string
ser.write(b"C "+step+b"\r") #sets step size for focus motor
ser.flush()
               

ic = ctypes.cdll.LoadLibrary("./tisgrabber_x64.dll")

print('ok')

IC.declareFunctions(ic)

ic.IC_InitLibrary(0)

hGrabber = IC.openDevice(ic)

ic.IC_SetPropertyAbsoluteValue(hGrabber, IC.T("Exposure"), IC.T("Value"),
                                ctypes.c_float(exposure_time))
ic.IC_SetPropertyAbsoluteValue(hGrabber, IC.T("Gain"), IC.T("Value"),
                                ctypes.c_float(gain))

    
print('camera properties initialized')

#starting live video feed..
if(ic.IC_IsDevValid(hGrabber)):
          ic.IC_StartLive(hGrabber, 1)  


def Acquire_Average(ic, hGrabber, image_dir):
    
    #initialize average image array
    im_avg = np.zeros((540,720),float)
    
    # First acquire 10 images to average the initial slice used for drift correction
    for k in range(10):
        
        im_str="\\foo_ini"+str(k)+".jpeg"
        # Convert image to OpenCV for saving to JPEG file
                
        if ic.IC_SnapImage(hGrabber, 2000) == IC.IC_SUCCESS:
                ic.IC_SaveImage(hGrabber, IC.T(image_dir+im_str),
                                        IC.ImageFileTypes['JPEG'], 100)
                
                print("Initial Image "+str(k)+" saved.")
                time.sleep(4) # 
                
                im_local = cv2.imread(image_dir+im_str,0)
                im_avg = im_avg+im_local/10 # compute average
                
    #Save the average of the 10 images 
    cv2.imwrite(image_dir+"\\Average.jpeg",im_avg)
    

def CalculateDiff(ic,hGrabber,image_dir):
 
    if ic.IC_SnapImage(hGrabber, 2000) == IC.IC_SUCCESS:
            ic.IC_SaveImage(hGrabber, IC.T(image_dir+"\\drift_test.jpeg"),
                                    IC.ImageFileTypes['JPEG'], 100)
    
            im_local=cv2.imread(image_dir+"\\drift_test.jpeg", 0)
            im_avg=cv2.imread(image_dir+"\\Average.jpeg",0)
            im_local=im_local+0.0
            im_avg= im_avg+0.0 # convert to float
            diff=abs(im_local-im_avg)# take absolute value of diff with average
            diff2=sum(sum(diff)) #sum all the diffs to get one number
            
            return diff2
        
im_local = np.zeros((540,720),float)

for j in range(total_nb):

    for x in range(nb_slices):
         
            im_str="\\foo"+str(j+456)+"_"+str(x)+".jpeg"
            # Convert image to OpenCV for saving to JPEG file
            
            if ic.IC_SnapImage(hGrabber, 2000) == IC.IC_SUCCESS:
                    ic.IC_SaveImage(hGrabber, IC.T(image_dir+im_str),
                                            IC.ImageFileTypes['JPEG'], 100)
                    print("Image saved.")
            
            print("slice "+str(x))
                    
             
            #check that diff increases every slice
            if (j==0) and (x==0):
                Acquire_Average(ic, hGrabber, image_dir)
                time.sleep(0.5) # 
                im_avg=cv2.imread(image_dir+"\\Average.jpeg",0)
                im_avg= im_avg+0.0 # convert to float
                im_local=cv2.imread(image_dir+im_str, 0)
                im_local=im_local+0.0
                diff=abs(im_local-im_avg)# take absolute value of diff with average
                diff_ini=sum(sum(diff)) #sum all the diffs to get one number
                print("diff_ini="+str(diff_ini/1e6))
                
            ser.write(b"U\r") #moves down by z steps D=DOWN U=UP
            ser.flush()
            time.sleep(0.15) # interval between every slice
             
              
         
    ser.write(b"V "+position_ini2+b"\r") #COME BACK TO INITIAL POSITION
    ser.flush()
    serialString=ser.read(16)
    print(serialString)
    time.sleep(3) # let the system time to come back to initial position
    
        
     # Now check that returned position against the average of the 10 initial images    
    
    diff2=CalculateDiff(ic,hGrabber,image_dir) 
    print("rel. diff2="+str(diff2/diff_ini))
    
   
    #### Find correct focus when diff with aberage too large
    ################# TRY GOING DOWN ##########################

    count=0
    ######CHANGE STEP SIZE TOI 0.2 MICRONS FOR FINE DRIFT CORRECTION
    if (diff2>tolerance*diff_ini):
        print("setting step size to 0.2um")
        step_drift=bytes(str(2),'utf-8') #convert to string
        ser.write(b"C "+step_drift+b"\r") #sets step size for focus motor
        ser.flush()
    
    
    while (diff2>tolerance*diff_ini) and (count <4):  # here we tolerate 100% difference with initial diff 
        print("Focus correction...")
       
        ser.write(b"D\r") #moves YP by z steps D=DOWN U=UP
        ser.flush()
        time.sleep(1) # 
       
        #check New diff
        diff2=CalculateDiff(ic,hGrabber,image_dir) 
        print("new rel. diff= "+str(diff2/diff_ini))
              
        count=count+1
    
    #GO BACK TO ORIGINAL POSITION BEFORE TRYING GOING UP
    #Drift_Corr_Function(diff2,diff_ini,count,position_ini2)
    if (diff2>tolerance*diff_ini) and (count !=0):
        print("drift correction going down UP, coming back to original position")
        ser.write(b"V "+position_ini2+b"\r") #COME BACK TO INITIAL POSITION
        ser.flush()
        serialString=ser.read(16)
        print(serialString)
        time.sleep(2) # 
        
    elif (diff2<tolerance*diff_ini) and (count!=0):
        #new position_ini2 after drift correction !
        serialString=ser.readlines(16) #read output
        print(serialString)
        ser.write(b"\r")
        ser.flush()
        serialString=ser.read(16)
        print(serialString)
        position=bytes.decode(serialString) #convert bytes to string
        position_ini=int(position[4:10]) #crop useful number as it comes in form 0,0,number
        position_ini2=bytes(str(position_ini),'utf-8') #convert bytes to string
        print("drift correction successfully applied")
    
    ################# TRY GOING UP ##########################
    count=0 
    
    while (diff2>tolerance*diff_ini) and (count <4):  # here we tolerate 50% difference with initial diff 
        print("Focus correction...")
       
        ser.write(b"U\r") #moves YP by z steps D=DOWN U=UP
        ser.flush()
        time.sleep(1) # 
       
        #check New diff
        diff2=CalculateDiff(ic,hGrabber,image_dir) 
        print("new rel. diff= "+str(diff2/diff_ini))
              
        count=count+1
    
    #End of the drift correction trials
    
    #Drift_Corr_Function(diff2,diff_ini,count,position_ini2)
    if (diff2>tolerance*diff_ini) and (count !=0):
        print("drift correction going DOWN failed, coming back to original position")
        ser.write(b"V "+position_ini2+b"\r") #COME BACK TO INITIAL POSITION
        ser.flush()
        serialString=ser.read(16)
        print(serialString)
        time.sleep(2) # 
        print("XY has moved, acquiring new average picture")
        Acquire_Average(ic,hGrabber,image_dir) # take average of 10 images and save
        diff_ini=CalculateDiff(ic,hGrabber,image_dir) #new diff_ini
        
        
    elif (diff2<tolerance*diff_ini) and (count!=0):
        #new position_ini2 after drift correction !
        serialString=ser.readlines(16) #read output
        print(serialString)
        ser.write(b"\r")
        ser.flush()
        serialString=ser.read(16)
        print(serialString)
        position=bytes.decode(serialString) #convert bytes to string
        position_ini=int(position[4:10]) #crop useful number as it comes in form 0,0,number
        position_ini2=bytes(str(position_ini),'utf-8') #convert bytes from string
        print("drift correction successfully applied")
    
    
    print("Setting step size to Step_Size")
    ser.write(b"C "+step+b"\r") #sets step size for focus motor
    ser.flush()       
    
    with open(results_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([position_ini, diff2/diff_ini])
    
    time.sleep(time_interval) #wait until next time point 
 
       
ser.reset_input_buffer()
ser.reset_output_buffer()        

copyfile(results_file,'results_saved.csv')
f.close()

ser.close()

ic.IC_ReleaseGrabber(hGrabber)


