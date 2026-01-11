%% SPM Second-Level (Group) Analysis for ds004302
% Performs group-level analysis comparing conditions across subjects
%
% Usage:
%   init_spm  % Run this first
%   batch_second_level

%% Configuration
DATASET_ROOT = evalin('base', 'DATASET_ROOT');

% Analysis directory
ANALYSIS_DIR = fullfile(DATASET_ROOT, 'spm', 'second_level');

% Load subject list and participant data
[subjects, participants] = load_bids_data(DATASET_ROOT);

% Define groups based on participant data
if ~isempty(participants)
    % Extract group information
    hc_subjects = {};
    avh_neg_subjects = {};
    avh_pos_subjects = {};
    
    for s = 1:length(subjects)
        sub_id = subjects{s};
        sub_label = sprintf('sub-%s', sub_id);
        
        % Find in participants table
        idx = strcmp(participants.participant_id, sub_label);
        if any(idx)
            group = participants.group{idx};
            switch group
                case 'HC'
                    hc_subjects{end+1} = sub_id;
                case 'AVH-'
                    avh_neg_subjects{end+1} = sub_id;
                case 'AVH+'
                    avh_pos_subjects{end+1} = sub_id;
            end
        end
    end
    
    fprintf('Group sizes:\n');
    fprintf('  HC: %d subjects\n', length(hc_subjects));
    fprintf('  AVH-: %d subjects\n', length(avh_neg_subjects));
    fprintf('  AVH+: %d subjects\n', length(avh_pos_subjects));
else
    % If no participant data, use all subjects
    hc_subjects = subjects;
    avh_neg_subjects = {};
    avh_pos_subjects = {};
end

%% Create contrasts of interest
% After first-level, create second-level analyses for:
% 1. Words > Baseline (white-noise)
% 2. Sentences > Baseline
% 3. Reversed > Baseline
% 4. Words > Reversed
% 5. Sentences > Reversed
% 6. Group comparisons (if groups defined)

contrasts = {'words', 'sentences', 'reversed', 'words_reversed', 'sentences_reversed'};

%% Example: One-sample t-test for "Words > Baseline" across all subjects
fprintf('\n========================================\n');
fprintf('Creating second-level analysis: Words > Baseline\n');
fprintf('========================================\n');

% Collect contrast images from first-level analyses
contrast_images = {};

for s = 1:length(subjects)
    sub_id = subjects{s};
    contrast_file = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id), 'spm', 'first_level', 'con_0001.nii');
    
    if exist(contrast_file, 'file')
        contrast_images{end+1} = contrast_file;
    else
        warning('Contrast file not found for subject %s', sub_id);
    end
end

if isempty(contrast_images)
    error('No contrast images found. Please run first-level analysis first.');
end

% Create directory for second-level
if ~exist(ANALYSIS_DIR, 'dir')
    mkdir(ANALYSIS_DIR);
end

% One-sample t-test
clear matlabbatch;
matlabbatch{1}.spm.stats.factorial_design.dir = {fullfile(ANALYSIS_DIR, 'words_baseline')};
matlabbatch{1}.spm.stats.factorial_design.des.t1.scans = contrast_images';
matlabbatch{1}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});
matlabbatch{1}.spm.stats.factorial_design.multi_cov = struct('files', {}, 'iCFI', {}, 'iCC', {});
matlabbatch{1}.spm.stats.factorial_design.masking.tm.tm_none = 1;
matlabbatch{1}.spm.stats.factorial_design.masking.im = 1;
matlabbatch{1}.spm.stats.factorial_design.masking.em = {''};
matlabbatch{1}.spm.stats.factorial_design.globalc.g_omit = 1;
matlabbatch{1}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;
matlabbatch{1}.spm.stats.factorial_design.globalm.glonorm = 1;

matlabbatch{2}.spm.stats.fmri_est.spmmat = {fullfile(ANALYSIS_DIR, 'words_baseline', 'SPM.mat')};
matlabbatch{2}.spm.stats.fmri_est.write_residuals = 0;
matlabbatch{2}.spm.stats.fmri_est.method.Classical = 1;

% Contrast: positive effect (Words > Baseline)
matlabbatch{3}.spm.stats.con.spmmat = {fullfile(ANALYSIS_DIR, 'words_baseline', 'SPM.mat')};
matlabbatch{3}.spm.stats.con.consess{1}.tcon.name = 'Words > Baseline';
matlabbatch{3}.spm.stats.con.consess{1}.tcon.weights = 1;
matlabbatch{3}.spm.stats.con.consess{1}.tcon.sessrep = 'none';
matlabbatch{3}.spm.stats.con.delete = 0;

% Run batch
spm_jobman('run', matlabbatch);

fprintf('Second-level analysis complete!\n');
fprintf('Results saved in: %s\n', fullfile(ANALYSIS_DIR, 'words_baseline'));

%% Note: Repeat similar structure for other contrasts and group comparisons
fprintf('\nNote: Modify this script to create additional second-level analyses:\n');
fprintf('  - Sentences > Baseline\n');
fprintf('  - Reversed > Baseline\n');
fprintf('  - Group comparisons (HC vs AVH- vs AVH+)\n');

