%% Report GLM Statistics
% Generates detailed statistical reports for voxel-wise GLM results
%
% Usage:
%   report_glm_statistics('first_level', '01', 1, 0.001, 10)
%   report_glm_statistics('second_level', 'Words_Baseline', 1, 0.001, 10)

function report_glm_statistics(level, identifier, contrast_num, threshold, extent)

%% Configuration
if nargin < 1, level = 'first_level'; end
if nargin < 2
    if strcmp(level, 'first_level')
        identifier = '01';
    else
        identifier = 'Words_Baseline';
    end
end
if nargin < 3, contrast_num = 1; end
if nargin < 4, threshold = 0.001; end
if nargin < 5, extent = 10; end

DATASET_ROOT = evalin('base', 'DATASET_ROOT');

fprintf('\n');
fprintf('╔══════════════════════════════════════════════════════════╗\n');
fprintf('║              GLM Statistical Report                      ║\n');
fprintf('╚══════════════════════════════════════════════════════════╝\n');
fprintf('\n');

%% Determine paths
if strcmp(level, 'first_level')
    spm_file = fullfile(DATASET_ROOT, sprintf('sub-%s', identifier), ...
        'spm', 'first_level', 'SPM.mat');
    title_str = sprintf('Subject %s - Contrast %d', identifier, contrast_num);
else
    spm_file = fullfile(DATASET_ROOT, 'spm', 'second_level', identifier, 'SPM.mat');
    title_str = sprintf('Group Analysis: %s - Contrast %d', identifier, contrast_num);
end

if ~exist(spm_file, 'file')
    error('SPM.mat not found: %s', spm_file);
end

load(spm_file);

%% Get contrast information
if contrast_num > length(SPM.xCon)
    error('Contrast number %d exceeds available contrasts (%d)', contrast_num, length(SPM.xCon));
end

con_info = SPM.xCon(contrast_num);

%% Display header
fprintf('Analysis Level: %s\n', level);
fprintf('Identifier: %s\n', identifier);
fprintf('Contrast: %s\n', con_info.name);
fprintf('Test Type: %s-test\n', con_info.STAT);
fprintf('Threshold: p < %.4f (uncorrected)\n', threshold);
fprintf('Cluster Extent: %d voxels\n', extent);
fprintf('\n');

%% Calculate statistics
fprintf('────────────────────────────────────────────────────────────\n');
fprintf('Contrast Details\n');
fprintf('────────────────────────────────────────────────────────────\n');
fprintf('Weights: ');
if strcmp(con_info.STAT, 'T')
    fprintf('%s\n', mat2str(con_info.c'));
else
    fprintf('\n');
    for i = 1:size(con_info.c, 2)
        fprintf('  %s\n', mat2str(con_info.c(:, i)'));
    end
end

fprintf('\nDegrees of Freedom:\n');
fprintf('  Error DF: %d\n', SPM.xX.erdf);

if strcmp(con_info.STAT, 'T')
    fprintf('  Contrast DF: 1\n');
    fprintf('  Total DF: %d\n', SPM.xX.erdf);
else
    fprintf('  Contrast DF: %d\n', size(con_info.c, 2));
    fprintf('  Total DF: %d\n', SPM.xX.erdf);
end

%% Threshold and find significant clusters
fprintf('\n────────────────────────────────────────────────────────────\n');
fprintf('Thresholding Results\n');
fprintf('────────────────────────────────────────────────────────────\n');

% Determine contrast image file
if strcmp(level, 'first_level')
    con_file = fullfile(DATASET_ROOT, sprintf('sub-%s', identifier), ...
        'spm', 'first_level', sprintf('con_%04d.nii', contrast_num));
    spmT_file = fullfile(DATASET_ROOT, sprintf('sub-%s', identifier), ...
        'spm', 'first_level', sprintf('spmT_%04d.nii', contrast_num));
else
    spmT_file = fullfile(DATASET_ROOT, 'spm', 'second_level', identifier, ...
        sprintf('spmT_%04d.nii', contrast_num));
end

if strcmp(con_info.STAT, 'F')
    % For F-tests, use spmF file
    spmT_file = strrep(spmT_file, 'spmT', 'spmF');
end

if ~exist(spmT_file, 'file')
    fprintf('Warning: Statistical image not found: %s\n', spmT_file);
    fprintf('Results may not be available yet. Run voxelwise_glm_tests first.\n');
    return;
end

% Load statistical image
V = spm_vol(spmT_file);
Y = spm_read_vols(V);

% Calculate threshold
if strcmp(con_info.STAT, 'T')
    % T-test threshold
    df = SPM.xX.erdf;
    t_threshold = spm_invTcdf(1 - threshold, df);
    fprintf('T-threshold (df=%d): %.3f\n', df, t_threshold);
    
    % Find significant voxels
    sig_voxels = Y > t_threshold;
    
else
    % F-test threshold
    df1 = size(con_info.c, 2);
    df2 = SPM.xX.erdf;
    f_threshold = spm_invFcdf(1 - threshold, [df1, df2]);
    fprintf('F-threshold (df=[%d,%d]): %.3f\n', df1, df2, f_threshold);
    
    sig_voxels = Y > f_threshold;
end

n_sig_voxels = sum(sig_voxels(:));
fprintf('Significant voxels: %d (%.2f%% of brain)\n', n_sig_voxels, ...
    100 * n_sig_voxels / numel(Y));

%% Cluster analysis
if n_sig_voxels > 0
    fprintf('\n────────────────────────────────────────────────────────────\n');
    fprintf('Cluster Analysis\n');
    fprintf('────────────────────────────────────────────────────────────\n');
    
    % Find clusters
    [L, num_clusters] = spm_bwlabel(sig_voxels, 26);
    
    if num_clusters > 0
        cluster_sizes = zeros(num_clusters, 1);
        cluster_max = zeros(num_clusters, 1);
        cluster_coords = zeros(num_clusters, 3);
        
        for c = 1:num_clusters
            cluster_mask = (L == c);
            cluster_sizes(c) = sum(cluster_mask(:));
            cluster_vals = Y(cluster_mask);
            [cluster_max(c), max_idx] = max(cluster_vals);
            
            % Find coordinates of max
            [x, y, z] = ind2sub(size(cluster_mask), find(cluster_mask, max_idx, 'first'));
            if ~isempty(x)
                cluster_coords(c, :) = [x(max_idx), y(max_idx), z(max_idx)];
            end
        end
        
        % Sort by size
        [~, sort_idx] = sort(cluster_sizes, 'descend');
        
        fprintf('Number of clusters: %d\n\n', num_clusters);
        fprintf('Top 10 clusters:\n');
        fprintf('%-6s %-12s %-12s %-10s %-10s %-10s\n', ...
            'Cluster', 'Size (vox)', 'Max Stat', 'X (mm)', 'Y (mm)', 'Z (mm)');
        fprintf('────────────────────────────────────────────────────────────\n');
        
        n_display = min(10, num_clusters);
        for i = 1:n_display
            c = sort_idx(i);
            if cluster_sizes(c) >= extent
                coords_mm = V.mat * [cluster_coords(c, :)'; 1];
                fprintf('%-6d %-12d %-12.3f %-10.1f %-10.1f %-10.1f\n', ...
                    c, cluster_sizes(c), cluster_max(c), ...
                    coords_mm(1), coords_mm(2), coords_mm(3));
            end
        end
        
        % Report clusters above extent threshold
        above_threshold = sum(cluster_sizes >= extent);
        fprintf('\nClusters >= %d voxels: %d\n', extent, above_threshold);
    end
else
    fprintf('\nNo significant clusters found at p < %.4f\n', threshold);
end

%% Summary
fprintf('\n────────────────────────────────────────────────────────────\n');
fprintf('Summary\n');
fprintf('────────────────────────────────────────────────────────────\n');
fprintf('Analysis: %s\n', title_str);
fprintf('Contrast: %s\n', con_info.name);
fprintf('Significant voxels: %d\n', n_sig_voxels);
if exist('num_clusters', 'var')
    fprintf('Significant clusters: %d\n', sum(cluster_sizes >= extent));
    fprintf('Largest cluster: %d voxels\n', max(cluster_sizes));
end
fprintf('────────────────────────────────────────────────────────────\n');
fprintf('\n');

fprintf('Note: For multiple comparisons correction, use:\n');
fprintf('  - FWE correction (family-wise error)\n');
fprintf('  - FDR correction (false discovery rate)\n');
fprintf('  - Cluster-level inference\n');
fprintf('These can be applied in SPM Results GUI.\n\n');

end

