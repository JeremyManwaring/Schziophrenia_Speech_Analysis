%% SPM Batch Preprocessing Script for ds004302
% Preprocesses fMRI data for all subjects
%
% This script performs:
% 1. Realignment (motion correction)
% 2. Coregistration (functional to structural)
% 3. Segmentation (structural image)
% 4. Normalization (to MNI space)
% 5. Smoothing
%
% Usage:
%   init_spm  % Run this first
%   batch_preprocessing

%% Configuration
DATASET_ROOT = evalin('base', 'DATASET_ROOT');

% Preprocessing parameters
% These should match your acquisition parameters (see task-speech_bold.json)
TR = 2.0;  % Repetition time in seconds
VoxelSize = [2 2 2];  % Voxel size for normalization (mm)
FWHM = [8 8 8];  % Smoothing kernel FWHM (mm)

% Options
realign_write_which = [2 1];  % [images to reslice: mean(1) + all(2)]
smooth_prefix = 's';  % Prefix for smoothed files

%% Load subject list
[subjects, participants] = load_bids_data(DATASET_ROOT);

%% Process each subject
for s = 1:length(subjects)
    sub_id = subjects{s};
    fprintf('\n========================================\n');
    fprintf('Processing subject: %s\n', sub_id);
    fprintf('========================================\n');
    
    % Subject directories
    sub_dir = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id));
    func_dir = fullfile(sub_dir, 'func');
    anat_dir = fullfile(sub_dir, 'anat');
    
    % Check if directories exist
    if ~exist(func_dir, 'dir') || ~exist(anat_dir, 'dir')
        warning('Subject %s: func or anat directory not found. Skipping.', sub_id);
        continue;
    end
    
    % Find functional image
    func_files = dir(fullfile(func_dir, sprintf('sub-%s_task-speech_bold.nii.gz', sub_id)));
    if isempty(func_files)
        warning('Subject %s: functional image not found. Skipping.', sub_id);
        continue;
    end
    
    % Find structural image
    anat_files = dir(fullfile(anat_dir, sprintf('sub-%s_T1w.nii.gz', sub_id)));
    if isempty(anat_files)
        warning('Subject %s: structural image not found. Skipping.', sub_id);
        continue;
    end
    
    % Unzip if needed (SPM can't directly read .gz files)
    func_path = fullfile(func_dir, func_files(1).name);
    anat_path = fullfile(anat_dir, anat_files(1).name);
    
    % Note: You may need to unzip .gz files first or use gunzip() function
    % For now, we assume files are unzipped or SPM12 handles them
    
    %% 1. REALIGNMENT
    fprintf('Step 1: Realignment...\n');
    matlabbatch{1}.spm.spatial.realign.estwrite.data = {cellstr(spm_select('ExtFPList', func_dir, sprintf('^sub-%s.*\\.nii$', sub_id), ':'))};
    matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.quality = 0.9;
    matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.sep = 4;
    matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.fwhm = 5;
    matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.rtm = 1;
    matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.interp = 4;
    matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.wrap = [0 0 0];
    matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.weight = '';
    matlabbatch{1}.spm.spatial.realign.estwrite.roptions.which = realign_write_which;
    matlabbatch{1}.spm.spatial.realign.estwrite.roptions.interp = 4;
    matlabbatch{1}.spm.spatial.realign.estwrite.roptions.wrap = [0 0 0];
    matlabbatch{1}.spm.spatial.realign.estwrite.roptions.mask = 1;
    matlabbatch{1}.spm.spatial.realign.estwrite.roptions.prefix = 'r';
    
    spm_jobman('run', matlabbatch);
    clear matlabbatch;
    
    %% 2. COREGISTRATION (Functional to Structural)
    fprintf('Step 2: Coregistration...\n');
    mean_func = fullfile(func_dir, sprintf('meanrsub-%s_task-speech_bold.nii', sub_id));
    matlabbatch{1}.spm.spatial.coreg.estimate.ref = {mean_func};
    matlabbatch{1}.spm.spatial.coreg.estimate.source = {anat_path};
    matlabbatch{1}.spm.spatial.coreg.estimate.other = {''};
    matlabbatch{1}.spm.spatial.coreg.estimate.eoptions.cost_fun = 'nmi';
    matlabbatch{1}.spm.spatial.coreg.estimate.eoptions.sep = [4 2];
    matlabbatch{1}.spm.spatial.coreg.estimate.eoptions.tol = [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001];
    matlabbatch{1}.spm.spatial.coreg.estimate.eoptions.fwhm = [7 7];
    
    spm_jobman('run', matlabbatch);
    clear matlabbatch;
    
    %% 3. SEGMENTATION
    fprintf('Step 3: Segmentation...\n');
    matlabbatch{1}.spm.spatial.preproc.channel.vols = {fullfile(anat_dir, sprintf('rsub-%s_T1w.nii', sub_id))};
    matlabbatch{1}.spm.spatial.preproc.channel.biasreg = 0.001;
    matlabbatch{1}.spm.spatial.preproc.channel.biasfwhm = 60;
    matlabbatch{1}.spm.spatial.preproc.channel.write = [0 1];
    matlabbatch{1}.spm.spatial.preproc.tissue(1).tpm = {fullfile(spm('dir'), 'tpm', 'TPM.nii,1')};
    matlabbatch{1}.spm.spatial.preproc.tissue(1).ngaus = 1;
    matlabbatch{1}.spm.spatial.preproc.tissue(1).native = [1 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(1).warped = [0 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(1).wrpdef = 0;
    matlabbatch{1}.spm.spatial.preproc.tissue(1).bias = [0 1];
    matlabbatch{1}.spm.spatial.preproc.tissue(1).biasreg = [0 0.001];
    matlabbatch{1}.spm.spatial.preproc.tissue(1).biasfwhm = [0 60];
    matlabbatch{1}.spm.spatial.preproc.tissue(2).tpm = {fullfile(spm('dir'), 'tpm', 'TPM.nii,2')};
    matlabbatch{1}.spm.spatial.preproc.tissue(2).ngaus = 1;
    matlabbatch{1}.spm.spatial.preproc.tissue(2).native = [1 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(2).warped = [0 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(2).wrpdef = 0;
    matlabbatch{1}.spm.spatial.preproc.tissue(3).tpm = {fullfile(spm('dir'), 'tpm', 'TPM.nii,3')};
    matlabbatch{1}.spm.spatial.preproc.tissue(3).ngaus = 2;
    matlabbatch{1}.spm.spatial.preproc.tissue(3).native = [1 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(3).warped = [0 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(3).wrpdef = 0;
    matlabbatch{1}.spm.spatial.preproc.warp.mrf = 1;
    matlabbatch{1}.spm.spatial.preproc.warp.cleanup = 1;
    matlabbatch{1}.spm.spatial.preproc.warp.reg = [0 0.001 0.5 0.05 0.2];
    matlabbatch{1}.spm.spatial.preproc.warp.affreg = 'mni';
    matlabbatch{1}.spm.spatial.preproc.warp.fwhm = 0;
    matlabbatch{1}.spm.spatial.preproc.warp.samp = 3;
    matlabbatch{1}.spm.spatial.preproc.warp.write = [0 1];
    
    spm_jobman('run', matlabbatch);
    clear matlabbatch;
    
    %% 4. NORMALIZE WRITE
    fprintf('Step 4: Normalization...\n');
    deformation_field = fullfile(anat_dir, sprintf('y_rsub-%s_T1w.nii', sub_id));
    func_images = cellstr(spm_select('ExtFPList', func_dir, sprintf('^rsub-%s.*\\.nii$', sub_id), ':'));
    
    matlabbatch{1}.spm.spatial.normalise.write.subj.def = {deformation_field};
    matlabbatch{1}.spm.spatial.normalise.write.subj.resample = func_images;
    matlabbatch{1}.spm.spatial.normalise.write.woptions.bb = [-78 -112 -70; 78 76 85];
    matlabbatch{1}.spm.spatial.normalise.write.woptions.vox = VoxelSize;
    matlabbatch{1}.spm.spatial.normalise.write.woptions.interp = 4;
    matlabbatch{1}.spm.spatial.normalise.write.woptions.prefix = 'w';
    
    spm_jobman('run', matlabbatch);
    clear matlabbatch;
    
    %% 5. SMOOTHING
    fprintf('Step 5: Smoothing...\n');
    normalized_func = cellstr(spm_select('ExtFPList', func_dir, sprintf('^wrsub-%s.*\\.nii$', sub_id), ':'));
    
    matlabbatch{1}.spm.spatial.smooth.data = normalized_func;
    matlabbatch{1}.spm.spatial.smooth.fwhm = FWHM;
    matlabbatch{1}.spm.spatial.smooth.dtype = 0;
    matlabbatch{1}.spm.spatial.smooth.im = 0;
    matlabbatch{1}.spm.spatial.smooth.prefix = smooth_prefix;
    
    spm_jobman('run', matlabbatch);
    clear matlabbatch;
    
    fprintf('Subject %s preprocessing complete!\n', sub_id);
end

fprintf('\n========================================\n');
fprintf('All subjects processed!\n');
fprintf('========================================\n');

