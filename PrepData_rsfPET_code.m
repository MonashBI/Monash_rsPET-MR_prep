function PrepData_rsfPET_code(pet, output_file, t_sigma, s_sigma)

%addpath(genpath('.'))
% if ~exist('pet_file','var')
%     pet_file = 'Test_Data/sub-303_pet-16_space-native.nii.gz';
%     epi_file = 'Test_Data/sub-303_rest_epi_unwarped_space-native_f.nii.gz';
%     pet_parc_file = 'Test_Data/aparc+aseg_in_PET-native.nii';
%     epi_parc_file = 'Test_Data/aparc+aseg_in_epi-native.nii';
%     output_file = 'rsfPET_data.mat';
% end

%% Load files
%t=tic;
%if ~exist('epi_parc','var')
    %pet_parc = load_nii(pet_parc_file);
    %epi = load_nii(epi_file);
    %epi_parc = load_nii(epi_parc_file);
    %pet = load_nii(pet_file);
%end
%toc(t)

%% Calc gradient of pet
inst_pet = convn(pet.img,GradOperator_rsfPET(t_sigma, s_sigma),'same');
t_width = 7;
inst_pet(:,:,:,1:floor(t_width/2)) = inst_pet(:,:,:,ceil(t_width/2)*ones(1,floor(t_width/2))); % edge cases
inst_pet(:,:,:,(size(inst_pet,4)-floor(t_width/2)+1):end) = inst_pet(:,:,:,(size(inst_pet,4)-floor(t_width/2))*ones(1,floor(t_width/2))); % edge cases

%% Output struct
%out = struct();
out =inst_pet;

%% Save output
save(output_file,'out')

end

%%
function se = GradOperator_rsfPET(t_sigma,s_sigma)

    t_width=7;
	s_width=7;
    
    if nargin<1
        t_sigma=2;
        s_sigma=1;
    end
        
    % Temporal smoother operator based on gaussian [-1 0 1]
    temporal_se = fspecial('gaussian',[1 t_width],t_sigma);
    temporal_se(1,1,1,1:t_width) = temporal_se;
    temporal_se = temporal_se(1,1,1,1:t_width);
    
    % Spatial smoothing operator based on gaussian
    spatial_se = fspecial3('gaussian',s_width,s_sigma);
    
    % Convolved spatial-temporal gaussian-weighted gradient operator
    se = convn(spatial_se,temporal_se);
    %se = temporal_se;
    
    % Remove bias (origin value)
    se(:,:,:,ceil(t_width/2)) = 0;
    
    % Renormalise to unity
    se = 2.*se/sum(se,'all');
    
    % Add gradient [-1 0 1]
    se(:,:,:,ceil(t_width/2)+1:end) = -se(:,:,:,ceil(t_width/2)+1:end);    
    
    %se = zeros(1,1,1,7);
    %se(:) = [1 1 1 0 -1 -1 -1];
end
