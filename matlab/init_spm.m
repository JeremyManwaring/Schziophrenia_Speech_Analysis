%% Initialize SPM for ds004302 dataset analysis
% This script sets up the MATLAB path and initializes SPM
%
% Usage:
%   Run this script first before any SPM analysis
%   You may need to modify the SPM_PATH variable below

%% Configuration
% Auto-detect SPM installation, or set manually below
SPM_PATH = '';

% Try to auto-detect SPM
if isempty(SPM_PATH)
    % Common SPM installation locations
    possible_paths = {
        '~/Documents/MATLAB/spm12'
        '~/Documents/MATLAB/spm_25.01.02'  % SPM12 version identifier
        '~/spm12'
        '/usr/local/spm12'
        '/Applications/spm12'
        fullfile(fileparts(mfilename('fullpath')), '..', '..', 'spm12')
    };
    
    for i = 1:length(possible_paths)
        test_path = possible_paths{i};
        % Expand ~ to home directory
        if test_path(1) == '~'
            test_path = fullfile(getenv('HOME'), test_path(3:end));
        end
        if exist(test_path, 'dir')
            % Check if it contains SPM files
            if exist(fullfile(test_path, 'spm.m'), 'file')
                SPM_PATH = test_path;
                fprintf('Auto-detected SPM at: %s\n', SPM_PATH);
                break;
            end
        end
    end
end

% If still not found, try to find in MATLAB path
if isempty(SPM_PATH)
    matlab_dirs = dir(fullfile(getenv('HOME'), 'Documents', 'MATLAB', 'spm*'));
    for i = 1:length(matlab_dirs)
        test_path = fullfile(matlab_dirs(i).folder, matlab_dirs(i).name);
        if exist(fullfile(test_path, 'spm.m'), 'file')
            SPM_PATH = test_path;
            fprintf('Auto-detected SPM at: %s\n', SPM_PATH);
            break;
        end
    end
end

% If still not found, prompt user or use default
if isempty(SPM_PATH)
    % Set default path (user should modify if needed)
    SPM_PATH = '~/Documents/MATLAB/spm12';
    fprintf('Using default SPM path: %s\n', SPM_PATH);
    fprintf('If SPM is not found, please modify SPM_PATH in init_spm.m\n');
end

% Expand ~ to home directory
if SPM_PATH(1) == '~'
    SPM_PATH = fullfile(getenv('HOME'), SPM_PATH(3:end));
end

%% Add SPM to MATLAB path
if ~exist(SPM_PATH, 'dir')
    error('SPM path not found: %s\nPlease modify SPM_PATH in init_spm.m', SPM_PATH);
end

if ~exist(fullfile(SPM_PATH, 'spm.m'), 'file')
    error('SPM not found at: %s\nPlease check your SPM installation', SPM_PATH);
end

% Add SPM to path
addpath(SPM_PATH);

% Initialize SPM
try
    spm('defaults', 'FMRI');
    spm_jobman('initcfg');
    fprintf('SPM initialized successfully!\n');
    fprintf('SPM version: %s\n', spm('Version'));
catch ME
    warning('Error initializing SPM: %s', ME.message);
    fprintf('Please ensure SPM is properly installed.\n');
end

%% Set dataset root
% Get the directory where this script is located
script_dir = fileparts(mfilename('fullpath'));
DATASET_ROOT = fileparts(script_dir);  % Go up one level from matlab/

fprintf('Dataset root: %s\n', DATASET_ROOT);

%% Save paths to workspace
assignin('base', 'SPM_PATH', SPM_PATH);
assignin('base', 'DATASET_ROOT', DATASET_ROOT);

fprintf('\nSPM setup complete. Variables SPM_PATH and DATASET_ROOT are now in workspace.\n');

