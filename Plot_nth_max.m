% this program plots the estimated cell count step increase based on the
% Nth maximum method

nb_cells=importdata('\\mcrlsinas01\lab-gielen\Tiwari_et_al_2023\Yolov4_bacteriophage\Matlab\Example data\nb_cells.mat'); %import array with number of cells

time_tag=importdata('\\mcrlsinas01\lab-gielen\Tiwari_et_al_2023\Yolov4_bacteriophage\Matlab\Example data\time_tag.mat'); % import array with times
time_tag_transpose=time_tag'./60; % change time to minutes

mov_nb=3; %length of moving average
count_max=0;
nb_max=3; %number of max chosen

mov_avg_round=round(movmean(nb_cells,mov_nb)); %moving average of number of cells
nb_cells(nb_cells==0)=NaN; %0 cell not expected in growth experiments
%%% initialization
nb_cells_max=mov_avg_round(1).*ones(1,length(nb_cells));
%%%

for i=2:length(nb_cells)

        if  mov_avg_round(i)>nb_cells_max(i-1) 
            count_max=count_max+1; %counter for nb of mins
        end
        
        if count_max==nb_max 
            nb_cells_max(i)=mov_avg_round(i);
            count_max=0; %reset counter

        else
            nb_cells_max(i)= nb_cells_max(i-1); 
        end
end


figure;
plot(time_tag_transpose,nb_cells); % plot number of cells from detections
hold on;
plot(time_tag_transpose,nb_cells_max);% plot processed count with the Nth maximum method 


