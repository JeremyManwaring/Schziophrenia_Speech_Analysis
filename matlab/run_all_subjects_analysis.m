%% Run Complete Analysis for All Subjects
% Preprocessing → GLM → Visualization for all subjects in dataset
%
% Usage:
%   run_all_subjects_analysis  % Process all subjects
%   run_all_subjects_analysis([], false)  % Don't retrieve files (already done)

function run_all_subjects_analysis(subject_list, retrieve_files, batch_size)

%% Configuration
if nargin < 1, subject_list = []; end
if nargin < 2, retrieve_files = true; end
if nargin < 3, batch_size = 5; end  % Process 5 subjects at a time

fprintf('\n╔══════════════════════════════════════════════════════════╗\n');
fprintf('║    Complete Analysis: All Subjects                     ║\n');
fprintf('╚══════════════════════════════════════════════════════════╝\n\n');

%% Initialize
init_spm;
DATASET_ROOT = evalin('base', 'DATASET_ROOT');
[all_subjects, participants] = load_bids_data(DATASET_ROOT);

if isempty(subject_list)
    subjects = all_subjects;
else
    subjects = intersect(all_subjects, subject_list);
end

fprintf('Total subjects to process: %d\n', length(subjects));
fprintf('Batch size: %d subjects\n', batch_size);
fprintf('Expected time: ~20-40 minutes per subject\n');
fprintf('Total estimated time: %.1f - %.1f hours\n\n', ...
    length(subjects) * 20/60, length(subjects) * 40/60);

%% Step 1: Retrieve files if needed
if retrieve_files
    fprintf('═══════════════════════════════════════════════════════════\n');
    fprintf('Step 1: Retrieving Data Files\n');
    fprintf('═══════════════════════════════════════════════════════════\n');
    fprintf('This may take time depending on network speed...\n\n');
    
    retrieve_subjects_files(subjects);
end

%% Step 2: Process subjects in batches
fprintf('\n═══════════════════════════════════════════════════════════\n');
fprintf('Step 2: Processing Subjects\n');
fprintf('═══════════════════════════════════════════════════════════\n');

total_start = tic;
processed = 0;
failed = 0;
failed_subjects = {};

num_batches = ceil(length(subjects) / batch_size);

for batch = 1:num_batches
    start_idx = (batch - 1) * batch_size + 1;
    end_idx = min(batch * batch_size, length(subjects));
    batch_subjects = subjects(start_idx:end_idx);
    
    fprintf('\n═══════════════════════════════════════════════════════════\n');
    fprintf('Batch %d/%d: Processing subjects %d-%d\n', batch, num_batches, start_idx, end_idx);
    fprintf('Subjects: %s\n', strjoin(batch_subjects, ', '));
    fprintf('═══════════════════════════════════════════════════════════\n');
    
    batch_start = tic;
    
    for s = 1:length(batch_subjects)
        sub_id = batch_subjects{s};
        fprintf('\n[%d/%d] Processing subject %s...\n', ...
            (batch-1)*batch_size + s, length(subjects), sub_id);
        
        try
            % Run complete analysis for this subject
            run_complete_analysis({sub_id}, false);
            processed = processed + 1;
            fprintf('  ✓ Subject %s completed successfully\n', sub_id);
        catch ME
            failed = failed + 1;
            failed_subjects{end+1} = sub_id;
            fprintf('  ✗ Subject %s failed: %s\n', sub_id, ME.message);
            
            % Save error to log
            log_error(sub_id, ME);
        end
    end
    
    batch_time = toc(batch_start);
    fprintf('\nBatch %d completed in %.1f minutes\n', batch, batch_time/60);
    fprintf('Progress: %d/%d subjects processed (%.1f%%)\n', ...
        processed, length(subjects), 100*processed/length(subjects));
end

total_time = toc(total_start);

%% Summary
fprintf('\n╔══════════════════════════════════════════════════════════╗\n');
fprintf('║              Analysis Complete                           ║\n');
fprintf('╚══════════════════════════════════════════════════════════╝\n\n');

fprintf('Summary:\n');
fprintf('────────────────────────────────────────────────────────────\n');
fprintf('Total subjects: %d\n', length(subjects));
fprintf('Successfully processed: %d\n', processed);
fprintf('Failed: %d\n', failed);
fprintf('Total time: %.1f hours (%.1f minutes)\n', total_time/3600, total_time/60);
fprintf('Average time per subject: %.1f minutes\n', total_time/length(subjects)/60);

if failed > 0
    fprintf('\nFailed subjects:\n');
    for i = 1:length(failed_subjects)
        fprintf('  - %s\n', failed_subjects{i});
    end
    fprintf('\nTo retry failed subjects:\n');
    fprintf('  run_all_subjects_analysis({%s}, false)\n', ...
        strjoin(cellfun(@(x) ['''', x, ''''], failed_subjects, 'UniformOutput', false), ', '));
end

fprintf('\n────────────────────────────────────────────────────────────\n');
fprintf('Results are in: sub-*/spm/first_level/\n');
fprintf('To view results:\n');
if processed > 0
    fprintf('  show_glm_results(''%s'', 1)\n', subjects{1});
end
fprintf('  check_analysis_status\n');
fprintf('────────────────────────────────────────────────────────────\n\n');

end

%% Helper function to retrieve files
function retrieve_subjects_files(subjects)
    DATASET_ROOT = evalin('base', 'DATASET_ROOT');
    
    % Use system call to git-annex
    fprintf('Retrieving files using git-annex...\n');
    
    for s = 1:length(subjects)
        sub_id = subjects{s};
        fprintf('  Subject %s (%d/%d)...', sub_id, s, length(subjects));
        
        func_file = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id), ...
            'func', sprintf('sub-%s_task-speech_bold.nii.gz', sub_id));
        anat_file = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id), ...
            'anat', sprintf('sub-%s_T1w.nii.gz', sub_id));
        
        % Check if already accessible
        if isfile(func_file) && isfile(anat_file)
            try
                % Try to read first byte to verify accessible
                fid = fopen(func_file, 'r');
                if fid > 0
                    fread(fid, 1);
                    fclose(fid);
                    fprintf(' already available\n');
                    continue;
                end
            catch
                % File not accessible, retrieve it
            end
        end
        
        % Retrieve using git-annex
        func_dir = fileparts(func_file);
        [status, ~] = system(sprintf('cd "%s" && git-annex get "%s" 2>&1', ...
            DATASET_ROOT, func_file), '-echo');
        
        if status == 0
            fprintf(' retrieved\n');
        else
            fprintf(' warning (may still work)\n');
        end
    end
end

%% Log errors
function log_error(sub_id, ME)
    DATASET_ROOT = evalin('base', 'DATASET_ROOT');
    log_dir = fullfile(DATASET_ROOT, 'spm', 'logs');
    if ~exist(log_dir, 'dir')
        mkdir(log_dir);
    end
    
    log_file = fullfile(log_dir, sprintf('error_sub-%s_%s.log', sub_id, datestr(now, 'yyyymmdd_HHMMSS')));
    fid = fopen(log_file, 'w');
    if fid > 0
        fprintf(fid, 'Error log for subject %s\n', sub_id);
        fprintf(fid, 'Date: %s\n\n', datestr(now));
        fprintf(fid, 'Error message: %s\n', ME.message);
        fprintf(fid, '\nStack trace:\n');
        for i = 1:length(ME.stack)
            fprintf(fid, '  File: %s\n', ME.stack(i).file);
            fprintf(fid, '  Line: %d\n', ME.stack(i).line);
        end
        fclose(fid);
    end
end

