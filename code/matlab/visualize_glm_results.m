%% Visualize Voxel-wise GLM Results
% Interactive visualization of t-test and F-test results
%
% Usage:
%   visualize_glm_results('first_level', '01', 1)  % View first-level contrast 1 for sub-01
%   visualize_glm_results('second_level', 'Words_Baseline', 1)  % View group result

function visualize_glm_results(level, identifier, contrast_num, threshold, extent)

%% Configuration
if nargin < 1, level = 'first_level'; end
if nargin < 2
    if strcmp(level, 'first_level')
        identifier = '01';  % Default subject
    else
        identifier = 'Words_Baseline';  % Default second-level analysis
    end
end
if nargin < 3, contrast_num = 1; end
if nargin < 4, threshold = 0.001; end  % p-value threshold
if nargin < 5, extent = 10; end  % Cluster extent threshold (voxels)

DATASET_ROOT = evalin('base', 'DATASET_ROOT');

fprintf('\n========================================\n');
fprintf('Visualizing GLM Results\n');
fprintf('========================================\n');

%% Determine paths
if strcmp(level, 'first_level')
    spm_file = fullfile(DATASET_ROOT, sprintf('sub-%s', identifier), ...
        'spm', 'first_level', 'SPM.mat');
    contrast_file = fullfile(DATASET_ROOT, sprintf('sub-%s', identifier), ...
        'spm', 'first_level', sprintf('con_%04d.nii', contrast_num));
    title_str = sprintf('Subject %s - Contrast %d', identifier, contrast_num);
else
    spm_file = fullfile(DATASET_ROOT, 'spm', 'second_level', identifier, 'SPM.mat');
    contrast_file = fullfile(DATASET_ROOT, 'spm', 'second_level', identifier, ...
        sprintf('spmT_%04d.nii', contrast_num));
    title_str = sprintf('Group Analysis: %s - Contrast %d', identifier, contrast_num);
end

%% Check if files exist
if ~exist(spm_file, 'file')
    error('SPM.mat not found: %s', spm_file);
end

if ~exist(contrast_file, 'file')
    error('Contrast file not found: %s', contrast_file);
end

fprintf('SPM file: %s\n', spm_file);
fprintf('Contrast: %s\n', contrast_file);
fprintf('Threshold: p < %.4f\n', threshold);
fprintf('Cluster extent: %d voxels\n', extent);

%% Load SPM structure
load(spm_file);

%% Get contrast information
if contrast_num > length(SPM.xCon)
    error('Contrast number %d exceeds available contrasts (%d)', contrast_num, length(SPM.xCon));
end

con_info = SPM.xCon(contrast_num);
fprintf('\nContrast: %s\n', con_info.name);
fprintf('Type: %s\n', con_info.STAT);

%% Display results using SPM Results GUI
fprintf('\nOpening SPM Results GUI...\n');
fprintf('  Use SPM GUI to adjust thresholds and view results\n');

% Set display parameters
if strcmp(con_info.STAT, 'T')
    spm('defaults', 'FMRI');
    hReg = spm_results_ui('Setup', spm_file);
    spm_results_ui('Setup', spm_file, contrast_num);
    
    % Set thresholds
    spm_orthviews('ContextMenu', 'threshold', threshold);
    
    fprintf('\nResults Viewer Instructions:\n');
    fprintf('  1. Adjust threshold using the GUI controls\n');
    fprintf('  2. Use cursor to explore significant voxels\n');
    fprintf('  3. Right-click for additional options\n');
    fprintf('  4. Use "Overlays" to add anatomical reference\n');
    
elseif strcmp(con_info.STAT, 'F')
    fprintf('\nF-test results detected.\n');
    fprintf('Use SPM Results GUI to view:\n');
    fprintf('  spm > Results > %s\n', spm_file);
end

%% Display summary statistics
fprintf('\n========================================\n');
fprintf('Contrast Summary\n');
fprintf('========================================\n');
fprintf('Name: %s\n', con_info.name);
fprintf('Type: %s-test\n', con_info.STAT);
fprintf('Weights: %s\n', mat2str(con_info.c'));

%% Print instructions
fprintf('\n========================================\n');
fprintf('Analysis Complete\n');
fprintf('========================================\n');
fprintf('To view results interactively:\n');
fprintf('  1. SPM > Results\n');
fprintf('  2. Select: %s\n', spm_file);
fprintf('  3. Choose contrast: %d (%s)\n', contrast_num, con_info.name);
fprintf('  4. Set threshold: p < %.4f\n', threshold);
fprintf('  5. Apply and explore\n');
fprintf('\nTo create publication figures:\n');
fprintf('  - Use SPM > Results > Render\n');
fprintf('  - Or export slices using SPM > Results > Save > Thresholded SPM\n');
fprintf('========================================\n\n');

end

