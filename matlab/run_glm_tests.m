%% Run Complete Voxel-wise GLM Test Pipeline
% Main script to run the complete GLM analysis with t-tests and F-tests
%
% This script:
% 1. Initializes SPM
% 2. Runs first-level GLM
% 3. Creates t-test contrasts
% 4. Creates F-tests
% 5. Runs second-level group analysis
% 6. Optionally visualizes results
%
% Usage:
%   run_glm_tests  % Run everything
%   run_glm_tests(false, true, true, true)  % Skip first-level, run rest

function run_glm_tests(run_first_level, run_contrasts, run_ftests, run_second_level, visualize)

if nargin < 1, run_first_level = true; end
if nargin < 2, run_contrasts = true; end
if nargin < 3, run_ftests = true; end
if nargin < 4, run_second_level = true; end
if nargin < 5, visualize = false; end

fprintf('\n');
fprintf('╔══════════════════════════════════════════════════════════╗\n');
fprintf('║     Voxel-wise GLM Analysis: T-tests and F-tests        ║\n');
fprintf('╚══════════════════════════════════════════════════════════╝\n');
fprintf('\n');

%% Initialize SPM
fprintf('Step 1: Initializing SPM...\n');
try
    init_spm;
    fprintf('  ✓ SPM initialized\n');
catch ME
    error('Failed to initialize SPM: %s', ME.message);
end

%% Run voxel-wise GLM tests
fprintf('\nStep 2: Running voxel-wise GLM tests...\n');
try
    voxelwise_glm_tests(run_first_level, run_contrasts, run_ftests, run_second_level);
    fprintf('  ✓ GLM analysis complete\n');
catch ME
    fprintf('  ✗ Error during GLM analysis: %s\n', ME.message);
    rethrow(ME);
end

%% Visualize results (optional)
if visualize
    fprintf('\nStep 3: Visualizing results...\n');
    try
        % Visualize a sample first-level result
        [subjects, ~] = load_bids_data();
        if ~isempty(subjects)
            fprintf('  Opening results viewer for subject %s...\n', subjects{1});
            visualize_glm_results('first_level', subjects{1}, 1);
        end
        
        % Visualize group result if available
        if run_second_level
            fprintf('  Opening group results viewer...\n');
            visualize_glm_results('second_level', 'Words_Baseline', 1);
        end
    catch ME
        warning('Visualization failed: %s', ME.message);
    end
end

%% Summary
fprintf('\n');
fprintf('╔══════════════════════════════════════════════════════════╗\n');
fprintf('║                    Analysis Complete                      ║\n');
fprintf('╚══════════════════════════════════════════════════════════╝\n');
fprintf('\n');
fprintf('Results Summary:\n');
fprintf('────────────────────────────────────────────────────────────\n');

if run_first_level
    fprintf('✓ First-level GLM models created\n');
end
if run_contrasts
    fprintf('✓ T-test contrasts created\n');
    fprintf('  - Words > Baseline\n');
    fprintf('  - Sentences > Baseline\n');
    fprintf('  - Reversed > Baseline\n');
    fprintf('  - Words > Reversed\n');
    fprintf('  - Sentences > Reversed\n');
    fprintf('  - (Words+Sentences) > Reversed\n');
    fprintf('  - Words > Sentences\n');
end
if run_ftests
    fprintf('✓ F-tests created\n');
    fprintf('  - All Conditions (omnibus test)\n');
    fprintf('  - Condition Differences\n');
end
if run_second_level
    fprintf('✓ Second-level group analyses completed\n');
    fprintf('  - Words > Baseline (group)\n');
    fprintf('  - Sentences > Baseline (group)\n');
    fprintf('  - Reversed > Baseline (group)\n');
end

fprintf('\n');
fprintf('Next Steps:\n');
fprintf('────────────────────────────────────────────────────────────\n');
fprintf('1. View results:\n');
fprintf('   visualize_glm_results(''first_level'', ''01'', 1)\n');
fprintf('   visualize_glm_results(''second_level'', ''Words_Baseline'', 1)\n');
fprintf('\n');
fprintf('2. Or use SPM GUI:\n');
fprintf('   spm > Results\n');
fprintf('\n');
fprintf('3. Export results:\n');
fprintf('   - Use SPM Results GUI to save thresholded images\n');
fprintf('   - Use SPM > Results > Export to export tables\n');
fprintf('\n');
fprintf('────────────────────────────────────────────────────────────\n');
fprintf('\n');

end

