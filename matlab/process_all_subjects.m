%% Process All Subjects: Complete Pipeline
% Handles preprocessing, GLM, and visualization for all subjects
%
% This script processes subjects in batches to avoid memory issues

function process_all_subjects(batch_size, start_from)

if nargin < 1, batch_size = 3; end  % Process 3 at a time
if nargin < 2, start_from = 1; end

init_spm;
DATASET_ROOT = evalin('base', 'DATASET_ROOT');
[subjects, ~] = load_bids_data(DATASET_ROOT);

fprintf('\n╔══════════════════════════════════════════════════════════╗\n');
fprintf('║    Processing All %d Subjects                           ║\n', length(subjects));
fprintf('╚══════════════════════════════════════════════════════════╝\n\n');

% Process in batches
num_batches = ceil((length(subjects) - start_from + 1) / batch_size);
total_processed = 0;
total_failed = 0;
failed_list = {};

overall_start = tic;

for batch = 1:num_batches
    start_idx = start_from + (batch - 1) * batch_size;
    end_idx = min(start_from + batch * batch_size - 1, length(subjects));
    batch_subjects = subjects(start_idx:end_idx);
    
    fprintf('\n═══════════════════════════════════════════════════════════\n');
    fprintf('BATCH %d/%d: Subjects %d-%d\n', batch, num_batches, start_idx, end_idx);
    fprintf('Processing: %s\n', strjoin(batch_subjects, ', '));
    fprintf('═══════════════════════════════════════════════════════════\n\n');
    
    batch_start = tic;
    
    for i = 1:length(batch_subjects)
        sub_id = batch_subjects{i};
        global_idx = start_idx + i - 1;
        
        fprintf('\n[%d/%d] Subject %s\n', global_idx, length(subjects), sub_id);
        fprintf('────────────────────────────────────────────────────────────\n');
        
        try
            % Run complete analysis
            run_complete_analysis({sub_id}, false);
            total_processed = total_processed + 1;
            fprintf('✓ Subject %s completed\n', sub_id);
        catch ME
            total_failed = total_failed + 1;
            failed_list{end+1} = sub_id;
            fprintf('✗ Subject %s failed: %s\n', sub_id, ME.message);
        end
    end
    
    batch_time = toc(batch_start);
    fprintf('\nBatch %d completed in %.1f minutes\n', batch, batch_time/60);
    fprintf('Progress: %d/%d (%.1f%%), Failed: %d\n\n', ...
        total_processed, global_idx, 100*total_processed/global_idx, total_failed);
end

total_time = toc(overall_start);

% Final summary
fprintf('\n╔══════════════════════════════════════════════════════════╗\n');
fprintf('║              PROCESSING COMPLETE                         ║\n');
fprintf('╚══════════════════════════════════════════════════════════╝\n\n');

fprintf('Summary:\n');
fprintf('  Total subjects: %d\n', length(subjects));
fprintf('  Processed: %d\n', total_processed);
fprintf('  Failed: %d\n', total_failed);
fprintf('  Total time: %.1f hours\n', total_time/3600);
fprintf('  Avg time/subject: %.1f minutes\n', total_time/length(subjects)/60);

if total_failed > 0
    fprintf('\nFailed subjects: %s\n', strjoin(failed_list, ', '));
end

fprintf('\nResults location: sub-*/spm/first_level/\n');
fprintf('\n');

end

