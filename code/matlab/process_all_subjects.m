%% Process All Subjects: Complete Pipeline with Parallel Processing
% Handles preprocessing, GLM, and visualization for all subjects
%
% Uses MATLAB Parallel Computing Toolbox for faster processing
%
% Usage:
%   process_all_subjects()           % Default: 4 parallel workers
%   process_all_subjects(8)          % Use 8 parallel workers
%   process_all_subjects(4, 1)       % 4 workers, start from subject 1
%   process_all_subjects(4, 1, false) % Sequential mode (no parallel)

function process_all_subjects(num_workers, start_from, use_parallel)

if nargin < 1, num_workers = 4; end        % Default: 4 parallel workers
if nargin < 2, start_from = 1; end         % Start from first subject
if nargin < 3, use_parallel = true; end    % Use parallel by default

% Initialize SPM and get dataset info
init_spm;
DATASET_ROOT = evalin('base', 'DATASET_ROOT');
SPM_PATH = evalin('base', 'SPM_PATH');
[subjects, ~] = load_bids_data(DATASET_ROOT);

% Select subjects to process
subjects_to_process = subjects(start_from:end);
num_subjects = length(subjects_to_process);

fprintf('\n======================================================\n');
if use_parallel
    fprintf('  Processing %d Subjects (Parallel: %d workers)\n', num_subjects, num_workers);
else
    fprintf('  Processing %d Subjects (Sequential Mode)\n', num_subjects);
end
fprintf('======================================================\n\n');

% Setup parallel pool if using parallel processing
if use_parallel
    % Check if Parallel Computing Toolbox is available
    % First check license, then verify toolbox is actually installed
    has_license = license('test', 'Distrib_Computing_Toolbox');
    has_toolbox = exist('parpool', 'file') > 0;
    
    if ~has_license
        warning('Parallel Computing Toolbox license not available. Falling back to sequential.');
        use_parallel = false;
    elseif ~has_toolbox
        warning('Parallel Computing Toolbox not installed. Falling back to sequential.');
        use_parallel = false;
    else
        % Start or resize parallel pool
        pool = gcp('nocreate');
        if isempty(pool)
            fprintf('Starting parallel pool with %d workers...\n', num_workers);
            pool = parpool('local', num_workers);
        elseif pool.NumWorkers ~= num_workers
            fprintf('Resizing parallel pool to %d workers...\n', num_workers);
            delete(pool);
            pool = parpool('local', num_workers);
        else
            fprintf('Using existing parallel pool with %d workers\n', pool.NumWorkers);
        end
        fprintf('Parallel pool ready.\n\n');
    end
end

% Pre-allocate result tracking arrays
results = zeros(num_subjects, 1);  % 1 = success, 0 = failed
error_msgs = cell(num_subjects, 1);

overall_start = tic;

if use_parallel
    %% PARALLEL PROCESSING
    fprintf('Processing %d subjects in parallel...\n\n', num_subjects);
    
    parfor i = 1:num_subjects
        sub_id = subjects_to_process{i};
        
        try
            % Each worker needs to initialize SPM independently
            addpath(SPM_PATH);
            spm('defaults', 'FMRI');
            spm_jobman('initcfg');
            
            % Run the complete analysis for this subject
            run_single_subject(sub_id, DATASET_ROOT);
            
            results(i) = 1;
            fprintf('[OK] Subject %s completed\n', sub_id);
        catch ME
            results(i) = 0;
            error_msgs{i} = ME.message;
            fprintf('[FAIL] Subject %s: %s\n', sub_id, ME.message);
        end
    end
else
    %% SEQUENTIAL PROCESSING
    fprintf('Processing %d subjects sequentially...\n\n', num_subjects);
    
    for i = 1:num_subjects
        sub_id = subjects_to_process{i};
        
        fprintf('\n[%d/%d] Subject %s\n', i, num_subjects, sub_id);
        fprintf('----------------------------------------------------\n');
        
        try
            run_complete_analysis({sub_id}, false);
            results(i) = 1;
            fprintf('[OK] Subject %s completed\n', sub_id);
        catch ME
            results(i) = 0;
            error_msgs{i} = ME.message;
            fprintf('[FAIL] Subject %s: %s\n', sub_id, ME.message);
        end
    end
end

total_time = toc(overall_start);

% Calculate statistics
total_processed = sum(results);
total_failed = sum(results == 0);
failed_indices = find(results == 0);

% Final summary
fprintf('\n======================================================\n');
fprintf('              PROCESSING COMPLETE\n');
fprintf('======================================================\n\n');

fprintf('Summary:\n');
if use_parallel
    fprintf('  Mode: Parallel (%d workers)\n', num_workers);
else
    fprintf('  Mode: Sequential\n');
end
fprintf('  Total subjects: %d\n', num_subjects);
fprintf('  Successful: %d\n', total_processed);
fprintf('  Failed: %d\n', total_failed);
fprintf('  Total time: %.1f hours\n', total_time/3600);
fprintf('  Avg time/subject: %.1f minutes\n', total_time/num_subjects/60);
if use_parallel && total_processed > 0
    fprintf('  Effective speedup: ~%.1fx\n', min(num_workers, total_processed));
end

if total_failed > 0
    fprintf('\nFailed subjects:\n');
    for i = 1:length(failed_indices)
        idx = failed_indices(i);
        fprintf('  %s: %s\n', subjects_to_process{idx}, error_msgs{idx});
    end
end

fprintf('\nResults location: sub-*/spm/first_level/\n');
fprintf('\n');

end

%% Run single subject analysis (for parallel workers)
function run_single_subject(sub_id, DATASET_ROOT)
    VoxelSize = [2 2 2];
    FWHM = [8 8 8];
    
    sub_dir = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id));
    func_dir = fullfile(sub_dir, 'func');
    anat_dir = fullfile(sub_dir, 'anat');
    
    % Check for smoothed images (already processed)
    smoothed = dir(fullfile(func_dir, 'swr*.nii'));
    if ~isempty(smoothed)
        fprintf('  Subject %s already preprocessed, running GLM only...\n', sub_id);
        run_glm_standalone(sub_id, DATASET_ROOT);
        return;
    end
    
    % Find and prepare images
    func_nii_file = fullfile(func_dir, sprintf('sub-%s_task-speech_bold.nii', sub_id));
    func_gz_file = fullfile(func_dir, sprintf('sub-%s_task-speech_bold.nii.gz', sub_id));
    
    if exist(func_nii_file, 'file')
        func_path = func_nii_file;
    elseif exist(func_gz_file, 'file')
        gunzip(func_gz_file, func_dir);
        func_path = func_nii_file;
    else
        error('Functional image not found for subject %s', sub_id);
    end
    
    anat_nii_file = fullfile(anat_dir, sprintf('sub-%s_T1w.nii', sub_id));
    anat_gz_file = fullfile(anat_dir, sprintf('sub-%s_T1w.nii.gz', sub_id));
    
    if exist(anat_nii_file, 'file')
        anat_path = anat_nii_file;
    elseif exist(anat_gz_file, 'file')
        gunzip(anat_gz_file, anat_dir);
        anat_path = anat_nii_file;
    else
        error('Anatomical image not found for subject %s', sub_id);
    end
    
    % Load functional scans
    V = spm_vol(func_path);
    func_scans = cell(length(V), 1);
    for i = 1:length(V)
        func_scans{i} = sprintf('%s,%d', func_path, i);
    end
    
    clear matlabbatch;
    
    % === REALIGNMENT ===
    matlabbatch{1}.spm.spatial.realign.estwrite.data = {func_scans};
    matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.quality = 0.9;
    matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.sep = 4;
    matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.fwhm = 5;
    matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.rtm = 1;
    matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.interp = 4;
    matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.wrap = [0 0 0];
    matlabbatch{1}.spm.spatial.realign.estwrite.roptions.which = [2 1];
    matlabbatch{1}.spm.spatial.realign.estwrite.roptions.interp = 4;
    matlabbatch{1}.spm.spatial.realign.estwrite.roptions.wrap = [0 0 0];
    matlabbatch{1}.spm.spatial.realign.estwrite.roptions.mask = 1;
    matlabbatch{1}.spm.spatial.realign.estwrite.roptions.prefix = 'r';
    
    % === SEGMENTATION ===
    matlabbatch{2}.spm.spatial.preproc.channel.vols = {anat_path};
    matlabbatch{2}.spm.spatial.preproc.channel.biasreg = 0.001;
    matlabbatch{2}.spm.spatial.preproc.channel.biasfwhm = 60;
    matlabbatch{2}.spm.spatial.preproc.channel.write = [0 1];
    matlabbatch{2}.spm.spatial.preproc.tissue(1).tpm = {fullfile(spm('dir'), 'tpm', 'TPM.nii,1')};
    matlabbatch{2}.spm.spatial.preproc.tissue(1).ngaus = 1;
    matlabbatch{2}.spm.spatial.preproc.tissue(1).native = [1 0];
    matlabbatch{2}.spm.spatial.preproc.tissue(1).warped = [0 0];
    matlabbatch{2}.spm.spatial.preproc.tissue(2).tpm = {fullfile(spm('dir'), 'tpm', 'TPM.nii,2')};
    matlabbatch{2}.spm.spatial.preproc.tissue(2).ngaus = 1;
    matlabbatch{2}.spm.spatial.preproc.tissue(2).native = [1 0];
    matlabbatch{2}.spm.spatial.preproc.tissue(2).warped = [0 0];
    matlabbatch{2}.spm.spatial.preproc.tissue(3).tpm = {fullfile(spm('dir'), 'tpm', 'TPM.nii,3')};
    matlabbatch{2}.spm.spatial.preproc.tissue(3).ngaus = 2;
    matlabbatch{2}.spm.spatial.preproc.tissue(3).native = [1 0];
    matlabbatch{2}.spm.spatial.preproc.tissue(3).warped = [0 0];
    matlabbatch{2}.spm.spatial.preproc.warp.mrf = 1;
    matlabbatch{2}.spm.spatial.preproc.warp.cleanup = 1;
    matlabbatch{2}.spm.spatial.preproc.warp.reg = [0 0.001 0.5 0.05 0.2];
    matlabbatch{2}.spm.spatial.preproc.warp.affreg = 'mni';
    matlabbatch{2}.spm.spatial.preproc.warp.fwhm = 0;
    matlabbatch{2}.spm.spatial.preproc.warp.samp = 3;
    matlabbatch{2}.spm.spatial.preproc.warp.write = [0 1];
    
    % === NORMALIZATION ===
    deformation_field = fullfile(anat_dir, sprintf('y_sub-%s_T1w.nii', sub_id));
    matlabbatch{3}.spm.spatial.normalise.write.subj.def = {deformation_field};
    matlabbatch{3}.spm.spatial.normalise.write.subj.resample = {''};
    matlabbatch{3}.spm.spatial.normalise.write.woptions.bb = [-78 -112 -70; 78 76 85];
    matlabbatch{3}.spm.spatial.normalise.write.woptions.vox = VoxelSize;
    matlabbatch{3}.spm.spatial.normalise.write.woptions.interp = 4;
    matlabbatch{3}.spm.spatial.normalise.write.woptions.prefix = 'w';
    
    % === SMOOTHING ===
    matlabbatch{4}.spm.spatial.smooth.data = {''};
    matlabbatch{4}.spm.spatial.smooth.fwhm = FWHM;
    matlabbatch{4}.spm.spatial.smooth.dtype = 0;
    matlabbatch{4}.spm.spatial.smooth.im = 0;
    matlabbatch{4}.spm.spatial.smooth.prefix = 's';
    
    % Run realignment
    spm_jobman('run', matlabbatch(1));
    
    % Wait for mean image
    mean_func = fullfile(func_dir, sprintf('meansub-%s_task-speech_bold.nii', sub_id));
    wait_for_file(mean_func, 300);
    
    % Run coregistration
    clear matlabbatch_coreg;
    matlabbatch_coreg{1}.spm.spatial.coreg.estimate.ref = {mean_func};
    matlabbatch_coreg{1}.spm.spatial.coreg.estimate.source = {anat_path};
    matlabbatch_coreg{1}.spm.spatial.coreg.estimate.other = {''};
    matlabbatch_coreg{1}.spm.spatial.coreg.estimate.eoptions.cost_fun = 'nmi';
    matlabbatch_coreg{1}.spm.spatial.coreg.estimate.eoptions.sep = [4 2];
    matlabbatch_coreg{1}.spm.spatial.coreg.estimate.eoptions.tol = [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001];
    matlabbatch_coreg{1}.spm.spatial.coreg.estimate.eoptions.fwhm = [7 7];
    spm_jobman('run', matlabbatch_coreg);
    
    % Run segmentation
    spm_jobman('run', matlabbatch(2));
    
    % Wait for deformation field
    wait_for_file(deformation_field, 300);
    
    % Update and run normalization
    realigned_func = fullfile(func_dir, sprintf('rsub-%s_task-speech_bold.nii', sub_id));
    V = spm_vol(realigned_func);
    func_images = cell(length(V), 1);
    for i = 1:length(V)
        func_images{i} = sprintf('%s,%d', realigned_func, i);
    end
    matlabbatch{3}.spm.spatial.normalise.write.subj.resample = func_images;
    spm_jobman('run', matlabbatch(3));
    
    % Wait for normalized file
    normalized_func = fullfile(func_dir, sprintf('wrsub-%s_task-speech_bold.nii', sub_id));
    wait_for_file(normalized_func, 300);
    
    % Update and run smoothing
    Vw = spm_vol(normalized_func);
    smooth_images = cell(length(Vw), 1);
    for i = 1:length(Vw)
        smooth_images{i} = sprintf('%s,%d', normalized_func, i);
    end
    matlabbatch{4}.spm.spatial.smooth.data = smooth_images;
    spm_jobman('run', matlabbatch(4));
    
    % Run GLM
    run_glm_standalone(sub_id, DATASET_ROOT);
end

%% GLM analysis for parallel workers
function run_glm_standalone(sub_id, DATASET_ROOT)
    TR = 2.0;
    HPF = 128;
    
    sub_dir = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id));
    func_dir = fullfile(sub_dir, 'func');
    spm_dir = fullfile(sub_dir, 'spm', 'first_level');
    
    if ~exist(spm_dir, 'dir')
        mkdir(spm_dir);
    end
    
    % Check if GLM already done
    if exist(fullfile(spm_dir, 'SPM.mat'), 'file')
        return;
    end
    
    % Load events
    events_file = fullfile(DATASET_ROOT, 'task-speech_events.tsv');
    events = readtable(events_file, 'FileType', 'text', 'Delimiter', '\t');
    
    conditions = {'words', 'sentences', 'reversed', 'white-noise'};
    onsets = cell(length(conditions), 1);
    durations = cell(length(conditions), 1);
    
    for c = 1:length(conditions)
        cond_idx = strcmp(events.condition, conditions{c});
        onsets{c} = events.onset(cond_idx);
        durations{c} = events.duration(cond_idx);
    end
    
    % Find smoothed images
    smoothed_func = fullfile(func_dir, sprintf('swrsub-%s_task-speech_bold.nii', sub_id));
    V = spm_vol(smoothed_func);
    func_images = cell(length(V), 1);
    for i = 1:length(V)
        func_images{i} = [V(i).fname ',' num2str(i)];
    end
    
    clear matlabbatch;
    
    % GLM Specification
    matlabbatch{1}.spm.stats.fmri_spec.dir = {spm_dir};
    matlabbatch{1}.spm.stats.fmri_spec.timing.units = 'secs';
    matlabbatch{1}.spm.stats.fmri_spec.timing.RT = TR;
    matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t = 16;
    matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t0 = 8;
    matlabbatch{1}.spm.stats.fmri_spec.sess.scans = func_images;
    
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
    rp_file = fullfile(func_dir, sprintf('rp_sub-%s_task-speech_bold.txt', sub_id));
    if ~exist(rp_file, 'file')
        rp_file = fullfile(func_dir, sprintf('rp_rsub-%s_task-speech_bold.txt', sub_id));
    end
    
    matlabbatch{1}.spm.stats.fmri_spec.sess.multi = {''};
    matlabbatch{1}.spm.stats.fmri_spec.sess.regress = struct('name', {}, 'val', {});
    if exist(rp_file, 'file')
        matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = {rp_file};
    else
        matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = {''};
    end
    matlabbatch{1}.spm.stats.fmri_spec.sess.hpf = HPF;
    matlabbatch{1}.spm.stats.fmri_spec.fact = struct('name', {}, 'levels', {});
    matlabbatch{1}.spm.stats.fmri_spec.bases.hrf.derivs = [0 0];
    matlabbatch{1}.spm.stats.fmri_spec.volt = 1;
    matlabbatch{1}.spm.stats.fmri_spec.global = 'None';
    matlabbatch{1}.spm.stats.fmri_spec.mthresh = 0.8;
    matlabbatch{1}.spm.stats.fmri_spec.mask = {''};
    matlabbatch{1}.spm.stats.fmri_spec.cvi = 'AR(1)';
    
    % Estimation
    matlabbatch{2}.spm.stats.fmri_est.spmmat = {fullfile(spm_dir, 'SPM.mat')};
    matlabbatch{2}.spm.stats.fmri_est.write_residuals = 0;
    matlabbatch{2}.spm.stats.fmri_est.method.Classical = 1;
    
    % Contrasts (T-tests)
    matlabbatch{3}.spm.stats.con.spmmat = {fullfile(spm_dir, 'SPM.mat')};
    matlabbatch{3}.spm.stats.con.delete = 0;
    
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
        matlabbatch{3}.spm.stats.con.consess{c}.tcon.name = contrast_list{c}{1};
        matlabbatch{3}.spm.stats.con.consess{c}.tcon.weights = contrast_list{c}{2};
        matlabbatch{3}.spm.stats.con.consess{c}.tcon.sessrep = 'none';
    end
    
    % F-tests
    matlabbatch{3}.spm.stats.con.consess{8}.fcon.name = 'All Conditions';
    matlabbatch{3}.spm.stats.con.consess{8}.fcon.weights = eye(3);
    matlabbatch{3}.spm.stats.con.consess{8}.fcon.sessrep = 'none';
    
    matlabbatch{3}.spm.stats.con.consess{9}.fcon.name = 'Condition Differences';
    matlabbatch{3}.spm.stats.con.consess{9}.fcon.weights = [1 -1 0; 1 0 -1];
    matlabbatch{3}.spm.stats.con.consess{9}.fcon.sessrep = 'none';
    
    spm_jobman('run', matlabbatch);
end

%% Wait for file to exist
function wait_for_file(filepath, max_wait)
    wait_time = 0;
    while ~exist(filepath, 'file') && wait_time < max_wait
        pause(2);
        wait_time = wait_time + 2;
    end
    if ~exist(filepath, 'file')
        error('Timeout waiting for file: %s', filepath);
    end
end
