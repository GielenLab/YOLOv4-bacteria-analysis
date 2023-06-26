# YOLOv4-bacteria-analysis
The code in this repository is used to analyze growth of individual bacterial cells in a z-stack based on YOLOv4 oriented detection.
The Find_cells_from_Z_stack code takes the location of folders that contain detection files, original images and npz files as input to extract number of cells in each z-stack.
The code also outputs a movie as seen in form of Movie-S1 and Movie-S2. 
To do the final processed count plot, one must save the nb_cells and time_tag as ".m" files from the output of Find_cells_from_Z_stack code. 
GetFIleTime.m is used to extract information on when the first image of each z-stack was taken and therfore to calucalte the total duration of experiments based on the number of z-stacks.
Further instructions to use each code have been specified in specific code files.

Z-focus_drift_correction code is used to correct for any changes in focus from the initial conditions based on acquiring an average image. This is implemented on Spyder with the correct plugins for z-axis control for the microscope and the camera to trigger and acquire images.  
