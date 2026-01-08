%% Quick Start Script for MATLAB/SPM
% This script initializes MATLAB, loads SPM, and sets up the dataset
% Run this from MATLAB or as: matlab -r "cd matlab; start_matlab_spm"

fprintf('\n========================================\n');
fprintf('MATLAB/SPM Initialization for ds004302\n');
fprintf('========================================\n\n');

% Change to matlab directory
if ~contains(pwd, 'matlab')
    matlab_dir = fullfile(fileparts(mfilename('fullpath')));
    if exist(matlab_dir, 'dir')
        cd(matlab_dir);
        fprintf('Changed to directory: %s\n\n', pwd);
    end
end

% Initialize SPM
try
    init_spm;
catch ME
    fprintf('Error during SPM initialization:\n');
    fprintf('  %s\n\n', ME.message);
    fprintf('Troubleshooting:\n');
    fprintf('  1. Check if SPM is installed\n');
    fprintf('  2. Edit init_spm.m and set SPM_PATH manually\n');
    fprintf('  3. Download SPM from: https://www.fil.ion.ucl.ac.uk/spm/software/download/\n');
    rethrow(ME);
end

% Verify SPM is working
try
    spm_version = spm('Version');
    fprintf('\n✓ SPM initialized successfully!\n');
    fprintf('  Version: %s\n', spm_version);
catch
    warning('SPM may not be fully initialized');
end

% Display dataset information
fprintf('\nDataset Information:\n');
fprintf('  Root: %s\n', DATASET_ROOT);
try
    [subjects, participants] = load_bids_data();
    fprintf('  Subjects: %d\n', length(subjects));
    if ~isempty(participants)
        fprintf('  Groups:\n');
        if ismember('group', participants.Properties.VariableNames)
            group_counts = groupsummary(participants, 'group');
            for i = 1:height(group_counts)
                fprintf('    %s: %d\n', string(group_counts.group(i)), group_counts.GroupCount(i));
            end
        end
    end
catch
    fprintf('  (Could not load participant information)\n');
end

fprintf('\n========================================\n');
fprintf('Setup Complete! You can now run:\n');
fprintf('  - batch_preprocessing\n');
fprintf('  - batch_first_level\n');
fprintf('  - batch_second_level\n');
fprintf('========================================\n\n');

