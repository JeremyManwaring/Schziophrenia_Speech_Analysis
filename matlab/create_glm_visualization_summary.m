%% Create GLM Visualization Summary
% Creates a comprehensive summary of t-tests and F-tests to be performed
% and generates visualization scripts

function create_glm_visualization_summary()

init_spm;
DATASET_ROOT = evalin('base', 'DATASET_ROOT');

fprintf('\n╔══════════════════════════════════════════════════════════╗\n');
fprintf('║     GLM Analysis: T-tests and F-tests Summary          ║\n');
fprintf('╚══════════════════════════════════════════════════════════╝\n\n');

%% Create summary document
summary_file = fullfile(DATASET_ROOT, 'spm', 'GLM_Analysis_Plan.txt');
summary_dir = fileparts(summary_file);
if ~exist(summary_dir, 'dir')
    mkdir(summary_dir);
end

fid = fopen(summary_file, 'w');

fprintf(fid, '╔══════════════════════════════════════════════════════════╗\n');
fprintf(fid, '║     GLM Analysis Plan: T-tests and F-tests             ║\n');
fprintf(fid, '╚══════════════════════════════════════════════════════════╝\n\n');
fprintf(fid, 'Generated: %s\n\n', datestr(now));
fprintf(fid, 'Dataset: ds004302 - Speech perception in schizophrenia\n');
fprintf(fid, 'Task: Speech perception (block design)\n');
fprintf(fid, 'Conditions: Words, Sentences, Reversed, White-noise (baseline)\n\n');

%% T-Test Contrasts
fprintf(fid, '═══════════════════════════════════════════════════════════\n');
fprintf(fid, 'T-TEST CONTRASTS (7 contrasts)\n');
fprintf(fid, '═══════════════════════════════════════════════════════════\n\n');

contrasts = {
    {1, 'Words > Baseline', '[1 0 0]', 'Tests activation for words vs white-noise baseline'},
    {2, 'Sentences > Baseline', '[0 1 0]', 'Tests activation for sentences vs white-noise baseline'},
    {3, 'Reversed > Baseline', '[0 0 1]', 'Tests activation for reversed speech vs baseline'},
    {4, 'Words > Reversed', '[1 0 -1]', 'Tests intelligible (words) vs unintelligible (reversed) speech'},
    {5, 'Sentences > Reversed', '[0 1 -1]', 'Tests intelligible (sentences) vs unintelligible (reversed) speech'},
    {6, '(Words+Sentences) > Reversed', '[1 1 -2]', 'Tests intelligible speech (words+sentences) vs unintelligible'},
    {7, 'Words > Sentences', '[1 -1 0]', 'Tests words vs sentences (within intelligible speech)'}
};

for i = 1:length(contrasts)
    fprintf(fid, 'Contrast %d: %s\n', contrasts{i}{1}, contrasts{i}{2});
    fprintf(fid, '  Weights: %s\n', contrasts{i}{3});
    fprintf(fid, '  Purpose: %s\n', contrasts{i}{4});
    fprintf(fid, '\n');
end

%% F-Test Contrasts
fprintf(fid, '═══════════════════════════════════════════════════════════\n');
fprintf(fid, 'F-TEST CONTRASTS (2 omnibus tests)\n');
fprintf(fid, '═══════════════════════════════════════════════════════════\n\n');

fprintf(fid, 'F-test 1: All Conditions (Omnibus Test)\n');
fprintf(fid, '  Matrix: eye(3) - Identity matrix\n');
fprintf(fid, '  Purpose: Tests if ANY of the three conditions show significant activation\n');
fprintf(fid, '  Interpretation: High F-value indicates significant effects present\n');
fprintf(fid, '  Use case: Initial screening for task-related activation\n\n');

fprintf(fid, 'F-test 2: Condition Differences\n');
fprintf(fid, '  Matrix: [1 -1 0; 1 0 -1]\n');
fprintf(fid, '  Purpose: Tests if there are ANY differences between conditions\n');
fprintf(fid, '  Tests:\n');
fprintf(fid, '    - Words vs Sentences\n');
fprintf(fid, '    - Words vs Reversed\n');
fprintf(fid, '  Interpretation: High F-value indicates condition differences exist\n');
fprintf(fid, '  Use case: Identify regions showing differential responses\n\n');

%% Analysis Workflow
fprintf(fid, '═══════════════════════════════════════════════════════════\n');
fprintf(fid, 'ANALYSIS WORKFLOW\n');
fprintf(fid, '═══════════════════════════════════════════════════════════\n\n');

fprintf(fid, 'Step 1: Preprocessing (if not done)\n');
fprintf(fid, '  Command: batch_preprocessing\n');
fprintf(fid, '  Output: Smoothed functional images (swr*.nii)\n\n');

fprintf(fid, 'Step 2: First-Level GLM\n');
fprintf(fid, '  Command: run_glm_tests\n');
fprintf(fid, '  Or: voxelwise_glm_tests(true, true, true, false)\n');
fprintf(fid, '  Output: SPM.mat files with GLM results\n\n');

fprintf(fid, 'Step 3: Create Contrasts (T-tests and F-tests)\n');
fprintf(fid, '  Command: voxelwise_glm_tests(false, true, true, false)\n');
fprintf(fid, '  Output: con_*.nii (contrast images)\n');
fprintf(fid, '          spmT_*.nii (T-statistic images)\n');
fprintf(fid, '          spmF_*.nii (F-statistic images)\n\n');

fprintf(fid, 'Step 4: Second-Level Group Analysis (optional)\n');
fprintf(fid, '  Command: voxelwise_glm_tests(false, false, false, true)\n');
fprintf(fid, '  Output: Group-level statistical maps\n\n');

fprintf(fid, 'Step 5: Visualization\n');
fprintf(fid, '  Command: show_glm_results(''01'', 1)  % T-test\n');
fprintf(fid, '  Command: show_glm_results(''01'', 1, true)  % F-test\n');
fprintf(fid, '  Or use SPM GUI: spm > Results\n\n');

%% Expected Results Locations
fprintf(fid, '═══════════════════════════════════════════════════════════\n');
fprintf(fid, 'EXPECTED RESULTS LOCATIONS\n');
fprintf(fid, '═══════════════════════════════════════════════════════════\n\n');

fprintf(fid, 'First-Level Results (per subject):\n');
fprintf(fid, '  sub-*/spm/first_level/SPM.mat\n');
fprintf(fid, '  sub-*/spm/first_level/con_0001.nii - Words > Baseline\n');
fprintf(fid, '  sub-*/spm/first_level/con_0002.nii - Sentences > Baseline\n');
fprintf(fid, '  sub-*/spm/first_level/con_0003.nii - Reversed > Baseline\n');
fprintf(fid, '  sub-*/spm/first_level/con_0004.nii - Words > Reversed\n');
fprintf(fid, '  sub-*/spm/first_level/con_0005.nii - Sentences > Reversed\n');
fprintf(fid, '  sub-*/spm/first_level/con_0006.nii - (Words+Sentences) > Reversed\n');
fprintf(fid, '  sub-*/spm/first_level/con_0007.nii - Words > Sentences\n');
fprintf(fid, '  sub-*/spm/first_level/spmT_0001.nii through spmT_0007.nii\n');
fprintf(fid, '  sub-*/spm/first_level/spmF_0001.nii - All Conditions\n');
fprintf(fid, '  sub-*/spm/first_level/spmF_0002.nii - Condition Differences\n\n');

fprintf(fid, 'Second-Level Results (group):\n');
fprintf(fid, '  spm/second_level/Words_Baseline/\n');
fprintf(fid, '  spm/second_level/Sentences_Baseline/\n');
fprintf(fid, '  spm/second_level/Reversed_Baseline/\n\n');

%% Visualization Commands
fprintf(fid, '═══════════════════════════════════════════════════════════\n');
fprintf(fid, 'VISUALIZATION COMMANDS\n');
fprintf(fid, '═══════════════════════════════════════════════════════════\n\n');

fprintf(fid, 'View T-test Results:\n');
fprintf(fid, '  show_glm_results(''01'', 1)     % Words > Baseline\n');
fprintf(fid, '  show_glm_results(''01'', 2)     % Sentences > Baseline\n');
fprintf(fid, '  show_glm_results(''01'', 3)     % Reversed > Baseline\n');
fprintf(fid, '  show_glm_results(''01'', 4)     % Words > Reversed\n');
fprintf(fid, '  show_glm_results(''01'', 5)     % Sentences > Reversed\n');
fprintf(fid, '  show_glm_results(''01'', 6)     % (Words+Sentences) > Reversed\n');
fprintf(fid, '  show_glm_results(''01'', 7)     % Words > Sentences\n\n');

fprintf(fid, 'View F-test Results:\n');
fprintf(fid, '  show_glm_results(''01'', 1, true)   % All Conditions\n');
fprintf(fid, '  show_glm_results(''01'', 2, true)   % Condition Differences\n\n');

fprintf(fid, 'Generate Statistics Report:\n');
fprintf(fid, '  report_glm_statistics(''first_level'', ''01'', 1, 0.001, 10)\n\n');

%% Interpretation Guide
fprintf(fid, '═══════════════════════════════════════════════════════════\n');
fprintf(fid, 'INTERPRETATION GUIDE\n');
fprintf(fid, '═══════════════════════════════════════════════════════════\n\n');

fprintf(fid, 'T-Test Interpretation:\n');
fprintf(fid, '  Positive values: Activation (condition > baseline/comparison)\n');
fprintf(fid, '  Negative values: Deactivation (condition < baseline/comparison)\n');
fprintf(fid, '  Magnitude: Strength of effect\n');
fprintf(fid, '  Significance: Statistical reliability (p-value)\n\n');

fprintf(fid, 'F-Test Interpretation:\n');
fprintf(fid, '  High F-values: Significant effects present\n');
fprintf(fid, '  Omnibus test: "Is there ANY effect?"\n');
fprintf(fid, '  Follow-up: Use t-tests to identify specific effects\n\n');

fprintf(fid, 'Multiple Comparisons:\n');
fprintf(fid, '  - Uncorrected: p < 0.001 (default, liberal)\n');
fprintf(fid, '  - FWE: Family-wise error correction (conservative)\n');
fprintf(fid, '  - FDR: False discovery rate correction (moderate)\n');
fprintf(fid, '  - Cluster-level: Corrects for multiple clusters\n\n');

fclose(fid);

fprintf('✓ Summary document created: %s\n', summary_file);

%% Create visualization script
create_visualization_commands();

%% Display summary
fprintf('\n═══════════════════════════════════════════════════════════\n');
fprintf('Summary\n');
fprintf('═══════════════════════════════════════════════════════════\n\n');
fprintf('T-tests: 7 contrasts will be created\n');
fprintf('F-tests: 2 omnibus tests will be created\n');
fprintf('Results: Document saved to %s\n', summary_file);
fprintf('\nTo run analysis:\n');
fprintf('  1. Preprocess: batch_preprocessing\n');
fprintf('  2. Run GLM: run_glm_tests\n');
fprintf('  3. Visualize: show_glm_results(''01'', 1)\n');
fprintf('\n');

end

%% Create visualization commands script
function create_visualization_commands()
    DATASET_ROOT = evalin('base', 'DATASET_ROOT');
    
    script_file = fullfile(DATASET_ROOT, 'spm', 'visualize_all_results.m');
    fid = fopen(script_file, 'w');
    
    fprintf(fid, '%% Visualize All GLM Results\n');
    fprintf(fid, '%% Run this after GLM analysis is complete\n\n');
    fprintf(fid, 'init_spm;\n\n');
    fprintf(fid, '%% Visualize T-tests for subject 01\n');
    for i = 1:7
        fprintf(fid, "show_glm_results('01', %d);\n", i);
        fprintf(fid, 'pause(2);\n\n');
    end
    
    fprintf(fid, '%% Visualize F-tests for subject 01\n');
    fprintf(fid, "show_glm_results('01', 1, true);  %% All Conditions\n");
    fprintf(fid, 'pause(2);\n');
    fprintf(fid, "show_glm_results('01', 2, true);  %% Condition Differences\n");
    
    fclose(fid);
    fprintf('✓ Visualization script created: %s\n', script_file);
end

