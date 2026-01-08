%% SPM First-Level Analysis for ds004302
% Performs subject-level GLM analysis
%
% This script creates first-level models for each subject with:
% - Task conditions: words, sentences, reversed
% - Baseline: white-noise
% - Motion regressors from realignment
%
% Usage:
%   init_spm  % Run this first
%   batch_first_level

%% Configuration
DATASET_ROOT = evalin('base', 'DATASET_ROOT');

% Analysis parameters (from task-speech_bold.json)
TR = 2.0;  % Repetition time (seconds)
% Note: First 5 volumes (10 seconds) were discarded in original analysis
% Events file starts at first volume after discard

% High-pass filter
HPF = 128;  % High-pass filter cutoff (seconds)

% Basis function
BASIS_FUNCTION = 'hrf';  % Hemodynamic response function
BASIS_DERIVS = [0 0];  % [time derivative, dispersion derivative]

% Masking
IMPLICIT_MASK = 1;  % Use implicit mask (threshold = 0.8)
GLOBAL_NORM = 'None';  % Global normalization

%% Load subject list
[subjects, participants] = load_bids_data(DATASET_ROOT);

%% Process each subject
for s = 1:length(subjects)
    sub_id = subjects{s};
    fprintf('\n========================================\n');
    fprintf('First-level analysis: %s\n', sub_id);
    fprintf('========================================\n');
    
    % Subject directories
    sub_dir = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id));
    func_dir = fullfile(sub_dir, 'func');
    
    % Find smoothed functional images
    func_images = cellstr(spm_select('ExtFPList', func_dir, sprintf('^swrsub-%s.*\\.nii$', sub_id), ':'));
    if isempty(func_images)
        warning('Subject %s: smoothed functional images not found. Skipping.', sub_id);
        continue;
    end
    
    % Load events file
    events_file = fullfile(DATASET_ROOT, 'task-speech_events.tsv');
    events = readtable(events_file, 'FileType', 'text', 'Delimiter', '\t');
    
    % Create conditions structure
    conditions = {'words', 'sentences', 'reversed', 'white-noise'};
    onsets = cell(length(conditions), 1);
    durations = cell(length(conditions), 1);
    
    for c = 1:length(conditions)
        cond_idx = strcmp(events.condition, conditions{c});
        onsets{c} = events.onset(cond_idx);
        durations{c} = events.duration(cond_idx);
    end
    
    % Find motion parameter file
    rp_file = fullfile(func_dir, sprintf('rp_sub-%s_task-speech_bold.txt', sub_id));
    if ~exist(rp_file, 'file')
        % Alternative naming
        rp_file = fullfile(func_dir, sprintf('rp_rsub-%s_task-speech_bold.txt', sub_id));
    end
    
    %% Create SPM batch for first-level
    clear matlabbatch;
    
    % Model specification
    matlabbatch{1}.spm.stats.fmri_spec.dir = {fullfile(sub_dir, 'spm', 'first_level')};
    matlabbatch{1}.spm.stats.fmri_spec.timing.units = 'secs';
    matlabbatch{1}.spm.stats.fmri_spec.timing.RT = TR;
    matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t = 16;
    matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t0 = 8;
    
    matlabbatch{1}.spm.stats.fmri_spec.sess.scans = func_images;
    
    % Add conditions (excluding white-noise as baseline)
    for c = 1:3  % words, sentences, reversed only
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(c).name = conditions{c};
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(c).onset = onsets{c};
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(c).duration = durations{c};
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(c).tmod = 0;
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(c).pmod = struct('name', {}, 'param', {}, 'poly', {});
        matlabbatch{1}.spm.stats.fmri_spec.sess.cond(c).orth = 1;
    end
    
    % Motion regressors
    if exist(rp_file, 'file')
        matlabbatch{1}.spm.stats.fmri_spec.sess.multi = {''};
        matlabbatch{1}.spm.stats.fmri_spec.sess.regress = struct('name', {}, 'val', {});
        matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = {rp_file};
    else
        warning('Motion parameter file not found for subject %s', sub_id);
        matlabbatch{1}.spm.stats.fmri_spec.sess.multi = {''};
        matlabbatch{1}.spm.stats.fmri_spec.sess.regress = struct('name', {}, 'val', {});
        matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = {''};
    end
    
    matlabbatch{1}.spm.stats.fmri_spec.sess.hpf = HPF;
    
    matlabbatch{1}.spm.stats.fmri_spec.fact = struct('name', {}, 'levels', {});
    matlabbatch{1}.spm.stats.fmri_spec.bases.hrf.derivs = BASIS_DERIVS;
    matlabbatch{1}.spm.stats.fmri_spec.volt = 1;
    matlabbatch{1}.spm.stats.fmri_spec.global = GLOBAL_NORM;
    matlabbatch{1}.spm.stats.fmri_spec.mthresh = 0.8;
    matlabbatch{1}.spm.stats.fmri_spec.mask = {''};
    matlabbatch{1}.spm.stats.fmri_spec.cvi = 'AR(1)';
    
    % Model estimation
    matlabbatch{2}.spm.stats.fmri_est.spmmat = {fullfile(sub_dir, 'spm', 'first_level', 'SPM.mat')};
    matlabbatch{2}.spm.stats.fmri_est.write_residuals = 0;
    matlabbatch{2}.spm.stats.fmri_est.method.Classical = 1;
    
    % Run batch
    spm_jobman('run', matlabbatch);
    
    fprintf('Subject %s first-level analysis complete!\n', sub_id);
end

fprintf('\n========================================\n');
fprintf('First-level analysis complete for all subjects!\n');
fprintf('========================================\n');

