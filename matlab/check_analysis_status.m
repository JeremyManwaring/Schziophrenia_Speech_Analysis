%% Check Analysis Status
% Shows progress of preprocessing and GLM analysis

function check_analysis_status()

init_spm;
DATASET_ROOT = evalin('base', 'DATASET_ROOT');

[subjects, ~] = load_bids_data(DATASET_ROOT);

fprintf('\n╔══════════════════════════════════════════════════════════╗\n');
fprintf('║              Analysis Status Check                      ║\n');
fprintf('╚══════════════════════════════════════════════════════════╝\n\n');

fprintf('Total subjects: %d\n\n', length(subjects));

%% Check preprocessing status
fprintf('Preprocessing Status:\n');
fprintf('────────────────────────────────────────────────────────────\n');

preprocessed = 0;
for s = 1:length(subjects)
    sub_id = subjects{s};
    func_dir = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id), 'func');
    smoothed = dir(fullfile(func_dir, 'swr*.nii'));
    
    if ~isempty(smoothed)
        fprintf('  ✓ Subject %s: Preprocessed\n', sub_id);
        preprocessed = preprocessed + 1;
    else
        if s <= 10  % Only show first 10 unprocessed
            fprintf('  ✗ Subject %s: Not preprocessed\n', sub_id);
        end
    end
end

if preprocessed < length(subjects) && length(subjects) > 10
    fprintf('  ... (and %d more not shown)\n', length(subjects) - 10);
end

fprintf('\nPreprocessed: %d/%d (%.1f%%)\n\n', preprocessed, length(subjects), ...
    100*preprocessed/length(subjects));

%% Check GLM status
fprintf('GLM Analysis Status:\n');
fprintf('────────────────────────────────────────────────────────────\n');

glm_complete = 0;
for s = 1:length(subjects)
    sub_id = subjects{s};
    spm_file = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id), 'spm', 'first_level', 'SPM.mat');
    con_file = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id), 'spm', 'first_level', 'con_0001.nii');
    
    if exist(spm_file, 'file') && exist(con_file, 'file')
        fprintf('  ✓ Subject %s: GLM complete\n', sub_id);
        glm_complete = glm_complete + 1;
    else
        if s <= 10  % Only show first 10
            if preprocessed > 0  % Only show if preprocessing is done
                fprintf('  ✗ Subject %s: GLM not done\n', sub_id);
            end
        end
    end
end

fprintf('\nGLM Complete: %d/%d (%.1f%%)\n\n', glm_complete, length(subjects), ...
    100*glm_complete/length(subjects));

%% Show ready subjects for visualization
if glm_complete > 0
    fprintf('Ready for Visualization:\n');
    fprintf('────────────────────────────────────────────────────────────\n');
    
    count = 0;
    for s = 1:length(subjects)
        sub_id = subjects{s};
        spm_file = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id), 'spm', 'first_level', 'SPM.mat');
        if exist(spm_file, 'file')
            fprintf('  Subject %s\n', sub_id);
            count = count + 1;
            if count >= 5
                break;
            end
        end
    end
    
    if count > 0
        fprintf('\nTo visualize, run:\n');
        fprintf('  show_glm_results(''%s'', 1)\n', subjects{1});
        fprintf('  report_glm_statistics(''first_level'', ''%s'', 1)\n', subjects{1});
    end
end

fprintf('\n');

end

