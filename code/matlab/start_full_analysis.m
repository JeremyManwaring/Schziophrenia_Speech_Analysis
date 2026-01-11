%% Start Full Analysis for All Subjects
% This script ensures files are accessible and starts the complete pipeline

function start_full_analysis()

fprintf('\n╔══════════════════════════════════════════════════════════╗\n');
fprintf('║    Starting Full Analysis Pipeline                      ║\n');
fprintf('╚══════════════════════════════════════════════════════════╝\n\n');

init_spm;
DATASET_ROOT = evalin('base', 'DATASET_ROOT');
[subjects, ~] = load_bids_data(DATASET_ROOT);

fprintf('Total subjects: %d\n', length(subjects));
fprintf('\nVerifying file accessibility...\n');

% Check first few subjects for file accessibility
accessible_count = 0;
for s = 1:min(5, length(subjects))
    sub_id = subjects{s};
    func_file = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id), 'func', ...
        sprintf('sub-%s_task-speech_bold.nii.gz', sub_id));
    anat_file = fullfile(DATASET_ROOT, sprintf('sub-%s', sub_id), 'anat', ...
        sprintf('sub-%s_T1w.nii.gz', sub_id));
    
    if exist(func_file, 'file') && exist(anat_file, 'file')
        accessible_count = accessible_count + 1;
        fprintf('  ✓ Subject %s: Files accessible\n', sub_id);
    else
        fprintf('  ✗ Subject %s: Files not found\n', sub_id);
    end
end

fprintf('\nAccessible: %d/%d checked\n', accessible_count, min(5, length(subjects)));

if accessible_count == 0
    fprintf('\n⚠️  No files accessible. Please retrieve files first:\n');
    fprintf('   export PATH="/opt/homebrew/bin:$PATH"\n');
    fprintf('   git-annex get sub-*/func/*.nii.gz sub-*/anat/*.nii.gz\n');
    return;
end

fprintf('\nStarting complete analysis pipeline...\n');
fprintf('This will process all %d subjects sequentially.\n', length(subjects));
fprintf('Expected time: ~24-48 hours\n\n');

% Start processing
process_all_subjects(3, 1);

end

