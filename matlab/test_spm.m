%% Test SPM Installation
% Quick test to verify SPM is properly installed and accessible
%
% Usage:
%   test_spm

fprintf('\n========================================\n');
fprintf('Testing SPM Installation\n');
fprintf('========================================\n\n');

%% Test 1: Check if SPM path exists
fprintf('Test 1: Checking SPM path...\n');
try
    init_spm;
    fprintf('  ✓ SPM path found and initialized\n');
catch ME
    fprintf('  ✗ Error: %s\n', ME.message);
    fprintf('\n  Please:\n');
    fprintf('    1. Install SPM12 from: https://www.fil.ion.ucl.ac.uk/spm/software/download/\n');
    fprintf('    2. Edit init_spm.m and set SPM_PATH to your SPM installation\n');
    return;
end

%% Test 2: Check SPM version
fprintf('\nTest 2: Checking SPM version...\n');
try
    spm_version = spm('Version');
    fprintf('  ✓ SPM version: %s\n', spm_version);
catch ME
    fprintf('  ✗ Error getting SPM version: %s\n', ME.message);
end

%% Test 3: Check SPM functions
fprintf('\nTest 3: Testing SPM functions...\n');
functions_to_test = {'spm_dir', 'spm_jobman', 'spm_defaults'};
for i = 1:length(functions_to_test)
    func_name = functions_to_test{i};
    if exist(func_name, 'builtin') || exist(func_name, 'file')
        fprintf('  ✓ %s is available\n', func_name);
    else
        fprintf('  ✗ %s not found\n', func_name);
    end
end

%% Test 4: Check dataset access
fprintf('\nTest 4: Testing dataset access...\n');
try
    [subjects, participants] = load_bids_data();
    fprintf('  ✓ Dataset loaded successfully\n');
    fprintf('    Subjects found: %d\n', length(subjects));
    if ~isempty(participants)
        fprintf('    Participants table: %d rows\n', height(participants));
    end
catch ME
    fprintf('  ✗ Error loading dataset: %s\n', ME.message);
end

%% Test 5: Check for neuroimaging files
fprintf('\nTest 5: Checking for neuroimaging files...\n');
try
    sub_dirs = dir(fullfile(DATASET_ROOT, 'sub-*'));
    if ~isempty(sub_dirs)
        % Check first subject
        first_sub = fullfile(DATASET_ROOT, sub_dirs(1).name);
        func_dir = fullfile(first_sub, 'func');
        anat_dir = fullfile(first_sub, 'anat');
        
        func_files = dir(fullfile(func_dir, '*.nii*'));
        anat_files = dir(fullfile(anat_dir, '*.nii*'));
        
        fprintf('  ✓ Found neuroimaging data\n');
        fprintf('    Example subject: %s\n', sub_dirs(1).name);
        if ~isempty(func_files)
            fprintf('    Functional files: %d found\n', length(func_files));
        end
        if ~isempty(anat_files)
            fprintf('    Anatomical files: %d found\n', length(anat_files));
        end
    else
        fprintf('  ✗ No subject directories found\n');
    end
catch ME
    fprintf('  ✗ Error checking files: %s\n', ME.message);
end

%% Summary
fprintf('\n========================================\n');
fprintf('Test Summary\n');
fprintf('========================================\n');
fprintf('If all tests passed, you are ready to run:\n');
fprintf('  - batch_preprocessing\n');
fprintf('  - batch_first_level\n');
fprintf('  - batch_second_level\n');
fprintf('\nFor help, see: matlab/README.md\n');
fprintf('========================================\n\n');

