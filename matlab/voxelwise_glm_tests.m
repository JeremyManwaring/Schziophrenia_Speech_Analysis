%% Voxel-wise GLM Tests (t-tests and F-tests)
% Complete pipeline for voxel-wise GLM analysis with t-tests and F-tests
%
% This script performs:
% 1. First-level GLM specification and estimation
% 2. Contrast definition for t-tests
% 3. F-test definition for omnibus testing
% 4. Second-level group analysis
%
% Usage:
%   init_spm
%   voxelwise_glm_tests

function voxelwise_glm_tests(process_first_level, process_contrasts, process_ftests, process_second_level)

%% Configuration
if nargin < 1, process_first_level = true; end
if nargin < 2, process_contrasts = true; end
if nargin < 3, process_ftests = true; end
if nargin < 4, process_second_level = true; end

DATASET_ROOT = evalin('base', 'DATASET_ROOT');
[subjects, participants] = load_bids_data(DATASET_ROOT);

% Analysis parameters
TR = 2.0;
HPF = 128;
BASIS_DERIVS = [0 0];
IMPLICIT_MASK = 0.8;

fprintf('\n========================================\n');
fprintf('Voxel-wise GLM Analysis\n');
fprintf('========================================\n');
fprintf('Total subjects: %d\n', length(subjects));
fprintf('Processing:\n');
fprintf('  First-level: %s\n', mat2str(process_first_level));
fprintf('  T-test contrasts: %s\n', mat2str(process_contrasts));
fprintf('  F-tests: %s\n', mat2str(process_ftests));
fprintf('  Second-level: %s\n', mat2str(process_second_level));
fprintf('========================================\n\n');

%% Load events file
events_file = fullfile(DATASET_ROOT, 'task-speech_events.tsv');
events = readtable(events_file, 'FileType', 'text', 'Delimiter', '\t');

% Prepare condition onsets and durations
conditions = {'words', 'sentences', 'reversed', 'white-noise'};
onsets = cell(length(conditions), 1);
durations = cell(length(conditions), 1);

for c = 1:length(conditions)
    cond_idx = strcmp(events.condition, conditions{c});
    onsets{c} = events.onset(cond_idx);
    durations{c} = events.duration(cond_idx);
end

%% PART 1: FIRST-LEVEL GLM SPECIFICATION AND ESTIMATION
if process_first_level
    fprintf('\n========================================\n');
    fprintf('PART 1: First-Level GLM Specification\n');
    fprintf('========================================\n');
    
    for s = 1:length(subjects)
        sub_id = subjects{s};
        fprintf('\nProcessing subject: %s (%d/%d)\n', sub_id, s, length(subjects));
        
        sub_dir = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id));
        func_dir = fullfile(sub_dir, 'func');
        spm_dir = fullfile(sub_dir, 'spm', 'first_level');
        
        % Create SPM directory
        if ~exist(spm_dir, 'dir')
            mkdir(spm_dir);
        end
        
        % Find smoothed functional images
        func_images = cellstr(spm_select('ExtFPList', func_dir, sprintf('^swrsub-%s.*\\.nii$', sub_id), ':'));
        if isempty(func_images)
            warning('Subject %s: smoothed images not found. Skipping.', sub_id);
            continue;
        end
        
        % Find motion parameter file
        rp_file = fullfile(func_dir, sprintf('rp_sub-%s_task-speech_bold.txt', sub_id));
        if ~exist(rp_file, 'file')
            rp_file = fullfile(func_dir, sprintf('rp_rsub-%s_task-speech_bold.txt', sub_id));
        end
        
        clear matlabbatch;
        
        % Model specification
        matlabbatch{1}.spm.stats.fmri_spec.dir = {spm_dir};
        matlabbatch{1}.spm.stats.fmri_spec.timing.units = 'secs';
        matlabbatch{1}.spm.stats.fmri_spec.timing.RT = TR;
        matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t = 16;
        matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t0 = 8;
        matlabbatch{1}.spm.stats.fmri_spec.sess.scans = func_images;
        
        % Add task conditions (exclude white-noise as it's implicit baseline)
        task_conditions = {'words', 'sentences', 'reversed'};
        for c = 1:3
            cond_name = task_conditions{c};
            cond_idx = strcmp(conditions, cond_name);
            matlabbatch{1}.spm.stats.fmri_spec.sess.cond(c).name = cond_name;
            matlabbatch{1}.spm.stats.fmri_spec.sess.cond(c).onset = onsets{cond_idx};
            matlabbatch{1}.spm.stats.fmri_spec.sess.cond(c).duration = durations{cond_idx};
            matlabbatch{1}.spm.stats.fmri_spec.sess.cond(c).tmod = 0;
            matlabbatch{1}.spm.stats.fmri_spec.sess.cond(c).pmod = struct('name', {}, 'param', {}, 'poly', {});
            matlabbatch{1}.spm.stats.fmri_spec.sess.cond(c).orth = 1;
        end
        
        % Motion regressors
        matlabbatch{1}.spm.stats.fmri_spec.sess.multi = {''};
        matlabbatch{1}.spm.stats.fmri_spec.sess.regress = struct('name', {}, 'val', {});
        if exist(rp_file, 'file')
            matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = {rp_file};
        else
            matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = {''};
        end
        matlabbatch{1}.spm.stats.fmri_spec.sess.hpf = HPF;
        matlabbatch{1}.spm.stats.fmri_spec.fact = struct('name', {}, 'levels', {});
        matlabbatch{1}.spm.stats.fmri_spec.bases.hrf.derivs = BASIS_DERIVS;
        matlabbatch{1}.spm.stats.fmri_spec.volt = 1;
        matlabbatch{1}.spm.stats.fmri_spec.global = 'None';
        matlabbatch{1}.spm.stats.fmri_spec.mthresh = IMPLICIT_MASK;
        matlabbatch{1}.spm.stats.fmri_spec.mask = {''};
        matlabbatch{1}.spm.stats.fmri_spec.cvi = 'AR(1)';
        
        % Model estimation
        matlabbatch{2}.spm.stats.fmri_est.spmmat = {fullfile(spm_dir, 'SPM.mat')};
        matlabbatch{2}.spm.stats.fmri_est.write_residuals = 0;
        matlabbatch{2}.spm.stats.fmri_est.method.Classical = 1;
        
        spm_jobman('run', matlabbatch);
        fprintf('  ✓ GLM specification and estimation complete\n');
    end
end

%% PART 2: T-TEST CONTRASTS
if process_contrasts
    fprintf('\n========================================\n');
    fprintf('PART 2: T-Test Contrasts\n');
    fprintf('========================================\n');
    
    for s = 1:length(subjects)
        sub_id = subjects{s};
        fprintf('\nCreating contrasts for: %s (%d/%d)\n', sub_id, s, length(subjects));
        
        sub_dir = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id));
        spm_dir = fullfile(sub_dir, 'spm', 'first_level');
        spm_file = fullfile(spm_dir, 'SPM.mat');
        
        if ~exist(spm_file, 'file')
            warning('SPM.mat not found for subject %s. Skipping.', sub_id);
            continue;
        end
        
        clear matlabbatch;
        
        % Define contrasts
        % Contrast 1: Words > Baseline
        % Contrast 2: Sentences > Baseline
        % Contrast 3: Reversed > Baseline
        % Contrast 4: Words > Reversed
        % Contrast 5: Sentences > Reversed
        % Contrast 6: (Words + Sentences) > Reversed
        % Contrast 7: Words > Sentences
        
        matlabbatch{1}.spm.stats.con.spmmat = {spm_file};
        matlabbatch{1}.spm.stats.con.delete = 0;
        
        contrast_list = {
            {'Words > Baseline', [1 0 0]};
            {'Sentences > Baseline', [0 1 0]};
            {'Reversed > Baseline', [0 0 1]};
            {'Words > Reversed', [1 0 -1]};
            {'Sentences > Reversed', [0 1 -1]};
            {'(Words+Sentences) > Reversed', [1 1 -2]};
            {'Words > Sentences', [1 -1 0]};
        };
        
        for c = 1:length(contrast_list)
            matlabbatch{1}.spm.stats.con.consess{c}.tcon.name = contrast_list{c}{1};
            matlabbatch{1}.spm.stats.con.consess{c}.tcon.weights = contrast_list{c}{2};
            matlabbatch{1}.spm.stats.con.consess{c}.tcon.sessrep = 'none';
        end
        
        spm_jobman('run', matlabbatch);
        fprintf('  ✓ Created %d t-test contrasts\n', length(contrast_list));
    end
end

%% PART 3: F-TESTS
if process_ftests
    fprintf('\n========================================\n');
    fprintf('PART 3: F-Tests (Omnibus Tests)\n');
    fprintf('========================================\n');
    
    for s = 1:length(subjects)
        sub_id = subjects{s};
        fprintf('\nCreating F-tests for: %s (%d/%d)\n', sub_id, s, length(subjects));
        
        sub_dir = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id));
        spm_dir = fullfile(sub_dir, 'spm', 'first_level');
        spm_file = fullfile(spm_dir, 'SPM.mat');
        
        if ~exist(spm_file, 'file')
            warning('SPM.mat not found for subject %s. Skipping.', sub_id);
            continue;
        end
        
        clear matlabbatch;
        
        matlabbatch{1}.spm.stats.con.spmmat = {spm_file};
        matlabbatch{1}.spm.stats.con.delete = 0;
        
        % F-test 1: All task conditions (omnibus test for any activation)
        % This tests if any of the three conditions show significant activation
        matlabbatch{1}.spm.stats.con.consess{1}.fcon.name = 'All Conditions';
        matlabbatch{1}.spm.stats.con.consess{1}.fcon.weights = eye(3);  % Test all 3 conditions
        matlabbatch{1}.spm.stats.con.consess{1}.fcon.sessrep = 'none';
        
        % F-test 2: Differences between conditions
        % Tests if there are any differences between the three conditions
        matlabbatch{1}.spm.stats.con.consess{2}.fcon.name = 'Condition Differences';
        matlabbatch{1}.spm.stats.con.consess{2}.fcon.weights = [1 -1 0; 1 0 -1];  % Test differences
        matlabbatch{1}.spm.stats.con.consess{2}.fcon.sessrep = 'none';
        
        spm_jobman('run', matlabbatch);
        fprintf('  ✓ Created 2 F-tests\n');
    end
end

%% PART 4: SECOND-LEVEL GROUP ANALYSIS
if process_second_level
    fprintf('\n========================================\n');
    fprintf('PART 4: Second-Level Group Analysis\n');
    fprintf('========================================\n');
    
    second_level_dir = fullfile(DATASET_ROOT, 'spm', 'second_level');
    if ~exist(second_level_dir, 'dir')
        mkdir(second_level_dir);
    end
    
    % Define contrasts to analyze at group level
    contrast_numbers = 1:3;  % Words, Sentences, Reversed > Baseline
    contrast_names = {'Words_Baseline', 'Sentences_Baseline', 'Reversed_Baseline'};
    
    for c = 1:length(contrast_numbers)
        con_num = contrast_numbers(c);
        con_name = contrast_names{c};
        
        fprintf('\nSecond-level analysis: %s (contrast %d)\n', con_name, con_num);
        
        % Collect contrast images
        contrast_images = {};
        valid_subjects = {};
        
        for s = 1:length(subjects)
            sub_id = subjects{s};
            con_file = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id), ...
                'spm', 'first_level', sprintf('con_%04d.nii', con_num));
            
            if exist(con_file, 'file')
                contrast_images{end+1} = con_file;
                valid_subjects{end+1} = sub_id;
            end
        end
        
        if isempty(contrast_images)
            warning('No contrast images found for contrast %d. Skipping.', con_num);
            continue;
        end
        
        fprintf('  Found %d contrast images\n', length(contrast_images));
        
        % One-sample t-test
        clear matlabbatch;
        output_dir = fullfile(second_level_dir, con_name);
        if ~exist(output_dir, 'dir')
            mkdir(output_dir);
        end
        
        matlabbatch{1}.spm.stats.factorial_design.dir = {output_dir};
        matlabbatch{1}.spm.stats.factorial_design.des.t1.scans = contrast_images';
        matlabbatch{1}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});
        matlabbatch{1}.spm.stats.factorial_design.multi_cov = struct('files', {}, 'iCFI', {}, 'iCC', {});
        matlabbatch{1}.spm.stats.factorial_design.masking.tm.tm_none = 1;
        matlabbatch{1}.spm.stats.factorial_design.masking.im = 1;
        matlabbatch{1}.spm.stats.factorial_design.masking.em = {''};
        matlabbatch{1}.spm.stats.factorial_design.globalc.g_omit = 1;
        matlabbatch{1}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;
        matlabbatch{1}.spm.stats.factorial_design.globalm.glonorm = 1;
        
        matlabbatch{2}.spm.stats.fmri_est.spmmat = {fullfile(output_dir, 'SPM.mat')};
        matlabbatch{2}.spm.stats.fmri_est.write_residuals = 0;
        matlabbatch{2}.spm.stats.fmri_est.method.Classical = 1;
        
        matlabbatch{3}.spm.stats.con.spmmat = {fullfile(output_dir, 'SPM.mat')};
        matlabbatch{3}.spm.stats.con.consess{1}.tcon.name = 'Group Mean';
        matlabbatch{3}.spm.stats.con.consess{1}.tcon.weights = 1;
        matlabbatch{3}.spm.stats.con.consess{1}.tcon.sessrep = 'none';
        matlabbatch{3}.spm.stats.con.delete = 0;
        
        spm_jobman('run', matlabbatch);
        fprintf('  ✓ Second-level analysis complete\n');
        fprintf('  Results in: %s\n', output_dir);
    end
end

fprintf('\n========================================\n');
fprintf('Voxel-wise GLM Analysis Complete!\n');
fprintf('========================================\n');
fprintf('\nResults are stored in:\n');
fprintf('  First-level: sub-*/spm/first_level/\n');
fprintf('  Second-level: spm/second_level/\n');
fprintf('\nTo view results, use:\n');
fprintf('  - SPM Results GUI (spm > Results)\n');
fprintf('  - visualize_results.m script\n');
fprintf('========================================\n\n');

end

