%% Monitor Analysis Progress
% Shows real-time progress of preprocessing and GLM analysis

function monitor_analysis_progress()

init_spm;
DATASET_ROOT = evalin('base', 'DATASET_ROOT');
[subjects, ~] = load_bids_data(DATASET_ROOT);

fprintf('\n╔══════════════════════════════════════════════════════════╗\n');
fprintf('║         Analysis Progress Monitor                       ║\n');
fprintf('╚══════════════════════════════════════════════════════════╝\n\n');

%% Check preprocessing status
fprintf('Preprocessing Status:\n');
fprintf('────────────────────────────────────────────────────────────\n');

preprocessed = 0;
preprocessing_subjects = {};

for s = 1:length(subjects)
    sub_id = subjects{s};
    func_dir = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id), 'func');
    
    % Check for smoothed images (final preprocessing output)
    smoothed = dir(fullfile(func_dir, 'swr*.nii'));
    if ~isempty(smoothed)
        preprocessed = preprocessed + 1;
        preprocessing_subjects{end+1} = sub_id;
    end
end

fprintf('Preprocessed: %d/%d subjects (%.1f%%)\n', preprocessed, length(subjects), ...
    100*preprocessed/length(subjects));

if preprocessed > 0
    fprintf('Completed subjects: ');
    if length(preprocessing_subjects) <= 10
        fprintf('%s\n', strjoin(preprocessing_subjects, ', '));
    else
        fprintf('%s ... (%d total)\n', strjoin(preprocessing_subjects(1:10), ', '), length(preprocessing_subjects));
    end
end

%% Check GLM status
fprintf('\nGLM Analysis Status:\n');
fprintf('────────────────────────────────────────────────────────────\n');

glm_complete = 0;
glm_subjects = {};

for s = 1:length(subjects)
    sub_id = subjects{s};
    spm_file = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id), 'spm', 'first_level', 'SPM.mat');
    con_file = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id), 'spm', 'first_level', 'con_0001.nii');
    
    if exist(spm_file, 'file') && exist(con_file, 'file')
        glm_complete = glm_complete + 1;
        glm_subjects{end+1} = sub_id;
    end
end

fprintf('GLM Complete: %d/%d subjects (%.1f%%)\n', glm_complete, length(subjects), ...
    100*glm_complete/length(subjects));

if glm_complete > 0
    fprintf('Completed subjects: ');
    if length(glm_subjects) <= 10
        fprintf('%s\n', strjoin(glm_subjects, ', '));
    else
        fprintf('%s ... (%d total)\n', strjoin(glm_subjects(1:10), ', '), length(glm_subjects));
    end
end

%% Check T-test and F-test contrasts
fprintf('\nContrasts Status:\n');
fprintf('────────────────────────────────────────────────────────────\n');

if glm_complete > 0
    % Check first completed subject
    sample_sub = glm_subjects{1};
    spm_dir = fullfile(DATASET_ROOT, sprintf('sub-%s', sample_sub), 'spm', 'first_level');
    
    t_tests = dir(fullfile(spm_dir, 'spmT_*.nii'));
    f_tests = dir(fullfile(spm_dir, 'spmF_*.nii'));
    
    fprintf('T-test contrast images: %d (expected: 7)\n', length(t_tests));
    fprintf('F-test contrast images: %d (expected: 2)\n', length(f_tests));
    
    if length(t_tests) == 7 && length(f_tests) == 2
        fprintf('✓ All contrasts created successfully!\n');
    end
end

%% Summary
fprintf('\n────────────────────────────────────────────────────────────\n');
fprintf('Summary\n');
fprintf('────────────────────────────────────────────────────────────\n');
fprintf('Total subjects: %d\n', length(subjects));
fprintf('Preprocessing complete: %d (%.1f%%)\n', preprocessed, 100*preprocessed/length(subjects));
fprintf('GLM complete: %d (%.1f%%)\n', glm_complete, 100*glm_complete/length(subjects));
fprintf('Remaining: %d subjects\n', length(subjects) - max(preprocessed, glm_complete));

if glm_complete > 0
    fprintf('\nReady for visualization:\n');
    fprintf('  show_glm_results(''%s'', 1)\n', glm_subjects{1});
end

fprintf('\n');

end

