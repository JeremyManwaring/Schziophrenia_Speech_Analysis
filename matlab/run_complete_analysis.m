%% Run Complete Analysis: Preprocessing + GLM + Visualization
% Processes data, runs GLM analysis, and creates visualizations
% 
% Usage:
%   run_complete_analysis  % Process first 3 subjects
%   run_complete_analysis([], true)  % Process all subjects

function run_complete_analysis(subject_list, process_all)

if nargin < 1, subject_list = {'01', '02', '03'}; end  % Default: first 3 subjects
if nargin < 2, process_all = false; end

fprintf('\n╔══════════════════════════════════════════════════════════╗\n');
fprintf('║      Complete Analysis: Preprocessing + GLM + Viz       ║\n');
fprintf('╚══════════════════════════════════════════════════════════╝\n\n');

%% Initialize
init_spm;
DATASET_ROOT = evalin('base', 'DATASET_ROOT');

[all_subjects, participants] = load_bids_data(DATASET_ROOT);

if process_all
    subjects = all_subjects;
    fprintf('Processing ALL %d subjects (this will take several hours)\n', length(subjects));
else
    subjects = subject_list;
    fprintf('Processing %d subjects for demonstration: %s\n', length(subjects), strjoin(subjects, ', '));
end

%% Step 1: Unzip files if needed
fprintf('\n═══════════════════════════════════════════════════════════\n');
fprintf('Step 1: Preparing Data (unzipping if needed)\n');
fprintf('═══════════════════════════════════════════════════════════\n');

for s = 1:length(subjects)
    sub_id = subjects{s};
    func_dir = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id), 'func');
    anat_dir = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id), 'anat');
    
    % Check and unzip functional
    func_gz = fullfile(func_dir, sprintf('sub-%s_task-speech_bold.nii.gz', sub_id));
    func_nii = fullfile(func_dir, sprintf('sub-%s_task-speech_bold.nii', sub_id));
    
    if exist(func_gz, 'file') && ~exist(func_nii, 'file')
        fprintf('  Unzipping functional image for subject %s...\n', sub_id);
        try
            gunzip(func_gz, func_dir);
            fprintf('    ✓ Functional image unzipped\n');
        catch ME
            warning('Could not unzip functional: %s', ME.message);
        end
    end
    
    % Check and unzip anatomical
    anat_gz = fullfile(anat_dir, sprintf('sub-%s_T1w.nii.gz', sub_id));
    anat_nii = fullfile(anat_dir, sprintf('sub-%s_T1w.nii', sub_id));
    
    if exist(anat_gz, 'file') && ~exist(anat_nii, 'file')
        fprintf('  Unzipping anatomical image for subject %s...\n', sub_id);
        try
            gunzip(anat_gz, anat_dir);
            fprintf('    ✓ Anatomical image unzipped\n');
        catch ME
            warning('Could not unzip anatomical: %s', ME.message);
        end
    end
end

fprintf('  ✓ Data preparation complete\n');

%% Step 2: Preprocessing
fprintf('\n═══════════════════════════════════════════════════════════\n');
fprintf('Step 2: Preprocessing\n');
fprintf('═══════════════════════════════════════════════════════════\n');
fprintf('This step includes:\n');
fprintf('  - Realignment (motion correction)\n');
fprintf('  - Coregistration (functional to structural)\n');
fprintf('  - Segmentation and Normalization\n');
fprintf('  - Smoothing (8mm FWHM)\n');
fprintf('\nProcessing subjects...\n');

preprocessing_start = tic;
preprocessed_subjects = {};

for s = 1:length(subjects)
    sub_id = subjects{s};
    fprintf('\n[%d/%d] Processing subject %s...\n', s, length(subjects), sub_id);
    
    try
        preprocess_subject(sub_id);
        preprocessed_subjects{end+1} = sub_id;
        fprintf('  ✓ Subject %s preprocessing complete\n', sub_id);
    catch ME
        warning('Failed to preprocess subject %s: %s', sub_id, ME.message);
    end
end

preprocessing_time = toc(preprocessing_start);
fprintf('\n✓ Preprocessing complete (%d subjects, %.1f minutes)\n', ...
    length(preprocessed_subjects), preprocessing_time/60);

%% Step 3: GLM Analysis
fprintf('\n═══════════════════════════════════════════════════════════\n');
fprintf('Step 3: GLM Analysis (T-tests and F-tests)\n');
fprintf('═══════════════════════════════════════════════════════════\n');

glm_start = tic;

for s = 1:length(preprocessed_subjects)
    sub_id = preprocessed_subjects{s};
    fprintf('\n[%d/%d] Running GLM for subject %s...\n', s, length(preprocessed_subjects), sub_id);
    
    try
        run_glm_for_subject(sub_id);
        fprintf('  ✓ Subject %s GLM complete\n', sub_id);
    catch ME
        warning('Failed GLM for subject %s: %s', sub_id, ME.message);
    end
end

glm_time = toc(glm_start);
fprintf('\n✓ GLM analysis complete (%d subjects, %.1f minutes)\n', ...
    length(preprocessed_subjects), glm_time/60);

%% Step 4: Visualization
fprintf('\n═══════════════════════════════════════════════════════════\n');
fprintf('Step 4: Generating Visualizations\n');
fprintf('═══════════════════════════════════════════════════════════\n');

if ~isempty(preprocessed_subjects)
    create_visualization_summary(preprocessed_subjects);
    fprintf('\n✓ Visualizations ready\n');
    fprintf('\nTo view results, run:\n');
    fprintf('  show_glm_results(''%s'', 1)  %% T-test: Words > Baseline\n', preprocessed_subjects{1});
    fprintf('  show_glm_results(''%s'', 4)  %% T-test: Words > Reversed\n', preprocessed_subjects{1});
    fprintf('  show_glm_results(''%s'', 1, true)  %% F-test: All Conditions\n', preprocessed_subjects{1});
end

%% Summary
fprintf('\n╔══════════════════════════════════════════════════════════╗\n');
fprintf('║                    Analysis Complete                     ║\n');
fprintf('╚══════════════════════════════════════════════════════════╝\n');
fprintf('\nProcessed: %d/%d subjects\n', length(preprocessed_subjects), length(subjects));
fprintf('Total time: %.1f minutes\n', (preprocessing_time + glm_time)/60);
fprintf('\nResults locations:\n');
for s = 1:min(3, length(preprocessed_subjects))
    fprintf('  Subject %s: sub-%s/spm/first_level/\n', preprocessed_subjects{s}, preprocessed_subjects{s});
end
fprintf('\n');

end

%% Preprocess a single subject
function preprocess_subject(sub_id)
    DATASET_ROOT = evalin('base', 'DATASET_ROOT');
    TR = 2.0;
    VoxelSize = [2 2 2];
    FWHM = [8 8 8];
    
    sub_dir = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id));
    func_dir = fullfile(sub_dir, 'func');
    anat_dir = fullfile(sub_dir, 'anat');
    
    % Check for smoothed images (already processed)
    smoothed = dir(fullfile(func_dir, 'swr*.nii'));
    if ~isempty(smoothed)
        fprintf('  Subject %s already preprocessed, skipping...\n', sub_id);
        return;
    end
    
    % Find images (try .nii first, then .nii.gz)
    func_nii_file = fullfile(func_dir, sprintf('sub-%s_task-speech_bold.nii', sub_id));
    func_gz_file = fullfile(func_dir, sprintf('sub-%s_task-speech_bold.nii.gz', sub_id));
    
    if exist(func_nii_file, 'file')
        func_path = func_nii_file;
    elseif exist(func_gz_file, 'file')
        fprintf('  Unzipping functional image (symlink detected)...\n');
        try
            % Read from symlink and write unzipped version
            gunzip(func_gz_file, func_dir);
            func_path = func_nii_file;
            fprintf('    ✓ Functional image ready\n');
        catch ME
            error('Failed to unzip functional image: %s', ME.message);
        end
    else
        error('Functional image not found for subject %s', sub_id);
    end
    
    anat_nii_file = fullfile(anat_dir, sprintf('sub-%s_T1w.nii', sub_id));
    anat_gz_file = fullfile(anat_dir, sprintf('sub-%s_T1w.nii.gz', sub_id));
    
    if exist(anat_nii_file, 'file')
        anat_path = anat_nii_file;
    elseif exist(anat_gz_file, 'file')
        fprintf('  Unzipping anatomical image (symlink detected)...\n');
        try
            gunzip(anat_gz_file, anat_dir);
            anat_path = anat_nii_file;
            fprintf('    ✓ Anatomical image ready\n');
        catch ME
            error('Failed to unzip anatomical image: %s', ME.message);
        end
    else
        error('Anatomical image not found for subject %s', sub_id);
    end
    
    clear matlabbatch;
    
    % Check if file needs unzipping (SPM may not read .gz directly)
    % First, try to use the file as-is
    try
        V = spm_vol(func_path);
        func_scans = cell(length(V), 1);
        for i = 1:length(V)
            func_scans{i} = sprintf('%s,%d', func_path, i);
        end
    catch
        % If that fails, unzip it
        fprintf('    Unzipping functional image (SPM may not read .gz)...\n');
        func_unzipped = fullfile(func_dir, sprintf('sub-%s_task-speech_bold.nii', sub_id));
        if ~exist(func_unzipped, 'file')
            gunzip(func_path, func_dir);
        end
        func_path = func_unzipped;
        V = spm_vol(func_path);
        func_scans = cell(length(V), 1);
        for i = 1:length(V)
            func_scans{i} = sprintf('%s,%d', func_path, i);
        end
    end
    
    % Realignment
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
    
    % Coregistration (will be set up after realignment creates mean image)
    mean_func = fullfile(func_dir, sprintf('meansub-%s_task-speech_bold.nii', sub_id));
    matlabbatch{2}.spm.spatial.coreg.estimate.ref = {{''}}; % Will be updated after realignment
    matlabbatch{2}.spm.spatial.coreg.estimate.source = {{anat_path}};
    matlabbatch{2}.spm.spatial.coreg.estimate.other = {''};
    matlabbatch{2}.spm.spatial.coreg.estimate.eoptions.cost_fun = 'nmi';
    matlabbatch{2}.spm.spatial.coreg.estimate.eoptions.sep = [4 2];
    matlabbatch{2}.spm.spatial.coreg.estimate.eoptions.tol = [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001];
    matlabbatch{2}.spm.spatial.coreg.estimate.eoptions.fwhm = [7 7];
    
    % Segmentation
    anat_coreg = fullfile(anat_dir, sprintf('rsub-%s_T1w.nii', sub_id));
    matlabbatch{3}.spm.spatial.preproc.channel.vols = {{anat_coreg}};
    matlabbatch{3}.spm.spatial.preproc.channel.biasreg = 0.001;
    matlabbatch{3}.spm.spatial.preproc.channel.biasfwhm = 60;
    matlabbatch{3}.spm.spatial.preproc.channel.write = [0 1];
    matlabbatch{3}.spm.spatial.preproc.tissue(1).tpm = {fullfile(spm('dir'), 'tpm', 'TPM.nii,1')};
    matlabbatch{3}.spm.spatial.preproc.tissue(1).ngaus = 1;
    matlabbatch{3}.spm.spatial.preproc.tissue(1).native = [1 0];
    matlabbatch{3}.spm.spatial.preproc.tissue(1).warped = [0 0];
    matlabbatch{3}.spm.spatial.preproc.tissue(2).tpm = {fullfile(spm('dir'), 'tpm', 'TPM.nii,2')};
    matlabbatch{3}.spm.spatial.preproc.tissue(2).ngaus = 1;
    matlabbatch{3}.spm.spatial.preproc.tissue(2).native = [1 0];
    matlabbatch{3}.spm.spatial.preproc.tissue(2).warped = [0 0];
    matlabbatch{3}.spm.spatial.preproc.tissue(3).tpm = {fullfile(spm('dir'), 'tpm', 'TPM.nii,3')};
    matlabbatch{3}.spm.spatial.preproc.tissue(3).ngaus = 2;
    matlabbatch{3}.spm.spatial.preproc.tissue(3).native = [1 0];
    matlabbatch{3}.spm.spatial.preproc.tissue(3).warped = [0 0];
    matlabbatch{3}.spm.spatial.preproc.warp.mrf = 1;
    matlabbatch{3}.spm.spatial.preproc.warp.cleanup = 1;
    matlabbatch{3}.spm.spatial.preproc.warp.reg = [0 0.001 0.5 0.05 0.2];
    matlabbatch{3}.spm.spatial.preproc.warp.affreg = 'mni';
    matlabbatch{3}.spm.spatial.preproc.warp.fwhm = 0;
    matlabbatch{3}.spm.spatial.preproc.warp.samp = 3;
    matlabbatch{3}.spm.spatial.preproc.warp.write = [0 1];
    
    % Normalization (will be set up after realignment completes)
    deformation_field = fullfile(anat_dir, sprintf('y_rsub-%s_T1w.nii', sub_id));
    realigned_func = fullfile(func_dir, sprintf('rsub-%s_task-speech_bold.nii', sub_id));
    
    % Initialize normalization batch (will update file paths after realignment)
    matlabbatch{4}.spm.spatial.normalise.write.subj.def = {{deformation_field}};
    matlabbatch{4}.spm.spatial.normalise.write.subj.resample = {''}; % Will be updated
    matlabbatch{4}.spm.spatial.normalise.write.woptions.bb = [-78 -112 -70; 78 76 85];
    matlabbatch{4}.spm.spatial.normalise.write.woptions.vox = VoxelSize;
    matlabbatch{4}.spm.spatial.normalise.write.woptions.interp = 4;
    matlabbatch{4}.spm.spatial.normalise.write.woptions.prefix = 'w';
    
    % Smoothing (will be set up after normalization completes)
    normalized_func = fullfile(func_dir, sprintf('wrsub-%s_task-speech_bold.nii', sub_id));
    
    % Initialize smoothing batch (will update file paths after normalization)
    matlabbatch{5}.spm.spatial.smooth.data = {''}; % Will be updated
    matlabbatch{5}.spm.spatial.smooth.fwhm = FWHM;
    matlabbatch{5}.spm.spatial.smooth.dtype = 0;
    matlabbatch{5}.spm.spatial.smooth.im = 0;
    matlabbatch{5}.spm.spatial.smooth.prefix = 's';
    
    % Run preprocessing steps sequentially
    fprintf('    Running realignment...\n');
    spm_jobman('run', matlabbatch(1));
    
    % Wait for realignment to complete
    % Note: SPM creates mean BEFORE applying 'r' prefix
    mean_func = fullfile(func_dir, sprintf('meansub-%s_task-speech_bold.nii', sub_id));
    max_wait = 300; % 5 minutes max wait
    wait_time = 0;
    while ~exist(mean_func, 'file') && wait_time < max_wait
        pause(2);
        wait_time = wait_time + 2;
    end
    
    if ~exist(mean_func, 'file')
        error('Realignment failed - mean image not created');
    end
    
    % Update coregistration with mean image (now exists)
    % Clear and rebuild the batch properly
    clear matlabbatch_coreg;
    matlabbatch_coreg{1}.spm.spatial.coreg.estimate.ref = {{mean_func}};
    matlabbatch_coreg{1}.spm.spatial.coreg.estimate.source = {{anat_path}};
    matlabbatch_coreg{1}.spm.spatial.coreg.estimate.other = {''};
    matlabbatch_coreg{1}.spm.spatial.coreg.estimate.eoptions.cost_fun = 'nmi';
    matlabbatch_coreg{1}.spm.spatial.coreg.estimate.eoptions.sep = [4 2];
    matlabbatch_coreg{1}.spm.spatial.coreg.estimate.eoptions.tol = [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001];
    matlabbatch_coreg{1}.spm.spatial.coreg.estimate.eoptions.fwhm = [7 7];
    
    fprintf('    Running coregistration...\n');
    spm_jobman('run', matlabbatch_coreg);
    
    % Wait for coregistration
    anat_coreg = fullfile(anat_dir, sprintf('rsub-%s_T1w.nii', sub_id));
    wait_time = 0;
    while ~exist(anat_coreg, 'file') && wait_time < max_wait
        pause(2);
        wait_time = wait_time + 2;
    end
    
    if ~exist(anat_coreg, 'file')
        error('Coregistration failed - coregistered anatomical file not created: %s', anat_coreg);
    end
    
    fprintf('    ✓ Coregistration complete\n');
    fprintf('    Running segmentation...\n');
    spm_jobman('run', matlabbatch(3));
    
    % Wait for segmentation and deformation field
    deformation_field = fullfile(anat_dir, sprintf('y_rsub-%s_T1w.nii', sub_id));
    wait_time = 0;
    while ~exist(deformation_field, 'file') && wait_time < max_wait
        pause(2);
        wait_time = wait_time + 2;
    end
    
    if ~exist(deformation_field, 'file')
        error('Segmentation failed - deformation field not created');
    end
    
    % Update normalization with correct file paths (realigned func exists now)
    realigned_func = fullfile(func_dir, sprintf('rsub-%s_task-speech_bold.nii', sub_id));
    if ~exist(realigned_func, 'file')
        error('Realigned functional file not found after realignment');
    end
    
    V = spm_vol(realigned_func);
    func_images = cell(length(V), 1);
    for i = 1:length(V)
        func_images{i} = sprintf('%s,%d', realigned_func, i);
    end
    
    matlabbatch{4}.spm.spatial.normalise.write.subj.resample = func_images;
    
    fprintf('    Running normalization...\n');
    spm_jobman('run', matlabbatch(4));
    
    % Wait for normalization
    normalized_func = fullfile(func_dir, sprintf('wrsub-%s_task-speech_bold.nii', sub_id));
    wait_time = 0;
    while ~exist(normalized_func, 'file') && wait_time < max_wait
        pause(2);
        wait_time = wait_time + 2;
    end
    
    if ~exist(normalized_func, 'file')
        error('Normalization failed - normalized file not created');
    end
    
    % Update smoothing with correct file paths
    Vw = spm_vol(normalized_func);
    smooth_images = cell(length(Vw), 1);
    for i = 1:length(Vw)
        smooth_images{i} = sprintf('%s,%d', normalized_func, i);
    end
    
    matlabbatch{5}.spm.spatial.smooth.data = smooth_images;
    
    fprintf('    Running smoothing...\n');
    spm_jobman('run', matlabbatch(5));
    
    fprintf('    ✓ Preprocessing complete\n');
end

%% Run GLM for a subject
function run_glm_for_subject(sub_id)
    DATASET_ROOT = evalin('base', 'DATASET_ROOT');
    TR = 2.0;
    HPF = 128;
    
    sub_dir = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id));
    func_dir = fullfile(sub_dir, 'func');
    spm_dir = fullfile(sub_dir, 'spm', 'first_level');
    
    if ~exist(spm_dir, 'dir')
        mkdir(spm_dir);
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

%% Create visualization summary
function create_visualization_summary(subject_list)
    DATASET_ROOT = evalin('base', 'DATASET_ROOT');
    
    summary_file = fullfile(DATASET_ROOT, 'spm', 'analysis_results_summary.txt');
    fid = fopen(summary_file, 'w');
    
    fprintf(fid, 'GLM Analysis Results Summary\n');
    fprintf(fid, '═══════════════════════════════════════════════════════\n\n');
    fprintf(fid, 'Analysis Date: %s\n', datestr(now));
    fprintf(fid, 'Subjects Analyzed: %d\n', length(subject_list));
    fprintf(fid, 'Subject IDs: %s\n\n', strjoin(subject_list, ', '));
    
    fprintf(fid, 'T-tests Created: 7\n');
    fprintf(fid, 'F-tests Created: 2\n\n');
    
    fprintf(fid, 'To visualize results:\n');
    fprintf(fid, '  show_glm_results(''%s'', 1)\n', subject_list{1});
    fprintf(fid, '  report_glm_statistics(''first_level'', ''%s'', 1)\n', subject_list{1});
    
    fclose(fid);
    fprintf('Summary saved to: %s\n', summary_file);
end

