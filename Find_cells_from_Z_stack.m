%% Written by Fabrice Gielen - 15/06/2023
%This code extracts the bounding boxes for all cells in all stacks and find a detection count
%Raw images must be in .png format, numpies .npz must be saved in the same base
%folder

close all
clear all

base_folder='\\mcrlsinas01\lab-gielen\Tiwari_et_al_2023\Yolov4_bacteriophage\Matlab\Example data\Detections'; % folder with npz detections

time_folder='\\mcrlsinas01\lab-gielen\Tiwari_et_al_2023\Yolov4_bacteriophage\Matlab\Example data\Images'; %folder with raw data images

nb_slices=24; % number of Z slices acquired

nb_time_points=3; % number of time points to analyse

motion_range=10; %exclusion radius in number of pixels (typically 10)

size_pic=540; % size of image in pixel (assuming square image)

lst_files = dir(fullfile(base_folder,'*.npz')); % Gets a list of all npz files in folder

lst_files_im = dir(fullfile(base_folder,'*.png')); % Gets a list of all tif files in folder

lst_files_time = dir(fullfile(time_folder,'*.jpeg')); % Gets a list of all jpeg files in folder

%natural sort order of list_files
[~, Index] = natsort({lst_files.name});
lst_files2   = lst_files(Index);

[~, Index] = natsort({lst_files_im.name});
lst_files_im2   = lst_files_im(Index);

[~, Index] = natsort({lst_files_time.name});
lst_files_time2   = lst_files_time(Index);


%%% initializations %%%
number=zeros(length(lst_files2),1); % total number of cells
doublets=zeros(length(lst_files2)/nb_slices,1);
nb_cells=zeros(length(lst_files2)/nb_slices,1);

%%% MAIN LOOP %%%

for t=1: nb_time_points %change to number of data points

    t %display time point

    clf; %clear figure for each time point

    coord_center=[]; % store all cordinates for centers of bounding boxes for all slices

    for k = 1:nb_slices   % loop over each slice
      
        area=[];
        
        full_file_name = fullfile(strcat(base_folder,'\foo',num2str(t-1),'_',num2str(k-1),'_detection.npz')); % file name for detections
        full_file_name_im = fullfile(base_folder, lst_files_im2((t-1)*nb_slices+k).name); % corresponding file name for image
       
    
        [nb, bboxes, class,scores]=read_npy(full_file_name); % read numpy with detections
        number(k)=nb; %extract number of detections
               
        %calculate area of all bounding boxes     
            for i=1:nb
                area=[area; [ (bboxes(i,4)-bboxes(i,2)) * (bboxes(i,3)-bboxes(i,1))]];
            end
        %%%
            
        %%Figure displaying the first slice of a stack and overlays detections for cells as red dots 
        figure(1);
        if k==1
           a=imread(full_file_name_im);
           imagesc(flip(a,1)); 
           set(gca,'Ydir','normal'); hold on;
           set(gca,'XTickLabel', []);
           set(gca,'YTickLabel', []);
        end
    
        
        for i=1:nb % nb is total number of cells detected
            
                %coord_center stores information on detections: [X - Y -
                %CLASS - NB_SLICE - AREA -SCORE]
                coord_center=[coord_center;[bboxes(i,2)+(bboxes(i,4)-bboxes(i,2))/2 bboxes(i,1)+(bboxes(i,3)-bboxes(i,1))/2  class(i) k area(i) scores(i)]];
                
        end
      
    end

    %%% 
    %Next, find the slice with the most number of in-plane cells

    [a,b]=max(number);
     
    %now find bacteria that are close by (within motion_range distance)
    dist=[];
    count=0;

    for l=1:size(coord_center,1) % find the slice with the maximum number of cells and put at the end of coord_center to process it first
        if coord_center(l,4)==b
            coord_center=[coord_center; coord_center(l,:)];
        end
    end
    
    coord_center=flipud(coord_center); %flip array
    coord_center=unique(coord_center,'rows','stable'); %remove duplicates while keeping order

    %%%

    for i=1:size(coord_center,1)
                       
        for j=1:size(coord_center,1)
        
            dist(i,j)=sqrt((coord_center(i,1)-coord_center(j,1))^2+ (coord_center(i,2)-coord_center(j,2))^2); %calculate all distances between cells
               
            if dist(i,j)<motion_range &&  i~=j && coord_center(i,4)~=coord_center(j,4) % if two points are close and not on same plane they are counted as separate cells 
         
              coord_center(j,:)=NaN; %remove cell assumed to be the same as a previous one

            end
       
        end

    end

    if ~isempty(coord_center)
    
        coord_1=coord_center(:,1); %variable used to count number of cells
        coord_1(isnan(coord_1))=[]; 
    
        nb_cells(t)=length(coord_1); %total number of cells across stack
        
        %plot all detected cells as red dots
        for i=1:size(coord_center,1)
             plot(coord_center(i,1),size_pic-coord_center(i,2),'o','MarkerSize',8,'MarkerFaceColor',[1  0 0]); hold on; 
        end
        xlim([0 size_pic]);
        ylim([0 size_pic]);

    end

    text(0.8*size_pic,0.8*size_pic,num2str(nb_cells(t)),'FontSize',18); % overlay number of cells on figure
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

end


%%% Find time tag according to when images were saved %%%
FileInfoini = [time_folder '\foo0_0.jpeg']; %funtion to extract time point of the first image
time_t0 = GetFileTime(FileInfoini);
time_tag0=time_t0.Write(4)*3600+time_t0.Write(5)*60+time_t0.Write(6); %time-point of the first image in mins 

 for i = 1 : (nb_time_points-1) % extract time-points of all subsequent fooi_0 images 
    FileInfo = [time_folder strcat('\foo',int2str(i),'_0.jpeg')];
    time_t= GetFileTime(FileInfo);
    time_tag(i)= (time_t.Write(4)*3600+time_t.Write(5)*60+time_t.Write(6))-time_tag0; 
 end

figure(2);
plot([0,time_tag./60],nb_cells)

%%%%%%%%%%%%%%%%% READING NUMPIES %%%%%%%%%%%%%%%%%%%%%
function [nz,bboxes,class,scores] =read_npy(file_name)
   
    a=unzip(file_name); 

    b=readNPY(a{1}); %read numpies 
    scores=readNPY(a{2});
    b=squeeze(b); %emove first dimension which is not used
    nz=nnz(b)/4 ;%number of non zero elements,divide by 4 coordinates = number of bacteria in total
    class=readNPY(a{3});
    bboxes=b;

end
%%%%%%%%%%%%%%%%%%%%%%%%%%


