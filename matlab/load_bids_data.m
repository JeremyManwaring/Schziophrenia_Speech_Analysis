function [subjects, participants] = load_bids_data(dataset_root)
%% Load BIDS dataset information
%
% Input:
%   dataset_root - Path to BIDS dataset root directory
%
% Output:
%   subjects - Cell array of subject IDs (e.g., {'01', '02', ...})
%   participants - Table with participant information

    if nargin < 1
        dataset_root = get_dataset_root();
    end

    % Find all subject directories
    sub_dirs = dir(fullfile(dataset_root, 'sub-*'));
    subjects = {};
    
    for i = 1:length(sub_dirs)
        if sub_dirs(i).isdir
            sub_id = sub_dirs(i).name(5:end);  % Remove 'sub-' prefix
            subjects{end+1} = sub_id;
        end
    end
    
    subjects = sort(subjects);
    fprintf('Found %d subjects\n', length(subjects));
    
    % Load participants.tsv
    participants_file = fullfile(dataset_root, 'participants.tsv');
    if exist(participants_file, 'file')
        participants = readtable(participants_file, 'FileType', 'text', 'Delimiter', '\t');
        fprintf('Loaded participant information for %d participants\n', height(participants));
    else
        warning('participants.tsv not found');
        participants = [];
    end
end

function root = get_dataset_root()
    % Try to get from workspace, otherwise use relative path
    try
        root = evalin('base', 'DATASET_ROOT');
    catch
        script_dir = fileparts(mfilename('fullpath'));
        root = fileparts(script_dir);  % Go up one level from matlab/
    end
end

