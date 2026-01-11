%% Unzip NIfTI .gz files for SPM compatibility
% Some versions of SPM cannot directly read .nii.gz files
% This script unzips all compressed NIfTI files in the dataset
%
% Usage:
%   unzip_nifti_files

function unzip_nifti_files(dataset_root, remove_original)
    % UNZIP_NIFTI_FILES Unzip compressed NIfTI files
    %
    % Input:
    %   dataset_root - Path to dataset root (optional, uses DATASET_ROOT if available)
    %   remove_original - If true, remove .gz files after unzipping (default: false)

    if nargin < 1
        try
            dataset_root = evalin('base', 'DATASET_ROOT');
        catch
            script_dir = fileparts(mfilename('fullpath'));
            dataset_root = fileparts(script_dir);
        end
    end
    
    if nargin < 2
        remove_original = false;
    end
    
    fprintf('Dataset root: %s\n', dataset_root);
    fprintf('Remove original .gz files: %s\n', mat2str(remove_original));
    fprintf('\n');
    
    % Find all .nii.gz files
    func_pattern = fullfile(dataset_root, 'sub-*', 'func', '*.nii.gz');
    anat_pattern = fullfile(dataset_root, 'sub-*', 'anat', '*.nii.gz');
    
    func_files = dir(func_pattern);
    anat_files = dir(anat_pattern);
    
    all_files = [func_files; anat_files];
    
    if isempty(all_files)
        fprintf('No .nii.gz files found.\n');
        return;
    end
    
    fprintf('Found %d compressed files to unzip:\n', length(all_files));
    fprintf('  - %d functional files\n', length(func_files));
    fprintf('  - %d anatomical files\n', length(anat_files));
    fprintf('\n');
    
    % Confirm
    response = input('Proceed with unzipping? (y/n): ', 's');
    if ~strcmpi(response, 'y')
        fprintf('Cancelled.\n');
        return;
    end
    
    % Unzip files
    success_count = 0;
    error_count = 0;
    
    for i = 1:length(all_files)
        file_path = fullfile(all_files(i).folder, all_files(i).name);
        output_path = file_path(1:end-3);  % Remove .gz extension
        
        % Check if unzipped file already exists
        if exist(output_path, 'file')
            fprintf('Skipping %s (already exists)\n', all_files(i).name);
            continue;
        end
        
        try
            % Use gunzip function
            gunzip(file_path);
            fprintf('Unzipped: %s\n', all_files(i).name);
            success_count = success_count + 1;
            
            % Remove original if requested
            if remove_original
                delete(file_path);
                fprintf('  Removed original: %s\n', all_files(i).name);
            end
        catch ME
            fprintf('ERROR unzipping %s: %s\n', all_files(i).name, ME.message);
            error_count = error_count + 1;
        end
    end
    
    fprintf('\n========================================\n');
    fprintf('Summary:\n');
    fprintf('  Successfully unzipped: %d files\n', success_count);
    fprintf('  Errors: %d files\n', error_count);
    fprintf('========================================\n');
    
    if error_count > 0
        warning('Some files failed to unzip. Check file permissions and disk space.');
    end
end

