%% Show GLM Results - Interactive Visualization
% Displays t-test and F-test results interactively

function show_glm_results(subject_id, contrast_num, show_ftest)

if nargin < 1, subject_id = '01'; end
if nargin < 2, contrast_num = 1; end
if nargin < 3, show_ftest = false; end

init_spm;
DATASET_ROOT = evalin('base', 'DATASET_ROOT');

fprintf('\n╔══════════════════════════════════════════════════════════╗\n');
fprintf('║            GLM Results Visualization                     ║\n');
fprintf('╚══════════════════════════════════════════════════════════╝\n\n');

%% Determine contrast type
if show_ftest
    if contrast_num == 1
        con_name = 'All Conditions';
    else
        con_name = 'Condition Differences';
    end
    fprintf('Showing F-test: %s\n', con_name);
    con_type = 'F';
else
    contrast_names = {
        'Words > Baseline',
        'Sentences > Baseline',
        'Reversed > Baseline',
        'Words > Reversed',
        'Sentences > Reversed',
        '(Words+Sentences) > Reversed',
        'Words > Sentences'
    };
    if contrast_num <= length(contrast_names)
        con_name = contrast_names{contrast_num};
    else
        con_name = sprintf('Contrast %d', contrast_num);
    end
    fprintf('Showing T-test: %s\n', con_name);
    con_type = 'T';
end

%% Check for results
spm_file = fullfile(DATASET_ROOT, sprintf('sub-%s', subject_id), 'spm', 'first_level', 'SPM.mat');

if ~exist(spm_file, 'file')
    fprintf('\n⚠ Results not found for subject %s\n', subject_id);
    fprintf('Please run GLM analysis first:\n');
    fprintf('  run_glm_demo\n');
    fprintf('  or\n');
    fprintf('  run_glm_tests\n');
    return;
end

load(spm_file);

%% Display contrast information
fprintf('\nContrast Information:\n');
fprintf('────────────────────────────────────────────────────────────\n');
fprintf('Subject: %s\n', subject_id);
fprintf('Contrast: %s\n', con_name);
fprintf('Type: %s-test\n', con_type);

if contrast_num <= length(SPM.xCon)
    con_info = SPM.xCon(contrast_num);
    fprintf('Weights: %s\n', mat2str(con_info.c'));
else
    fprintf('⚠ Contrast %d not found\n', contrast_num);
    fprintf('Available contrasts: %d\n', length(SPM.xCon));
    return;
end

%% Open SPM Results GUI
fprintf('\nOpening SPM Results Viewer...\n');
fprintf('────────────────────────────────────────────────────────────\n');

try
    hReg = spm_results_ui('Setup', spm_file);
    spm_results_ui('Setup', spm_file, contrast_num);
    
    fprintf('\n✓ Results viewer opened!\n');
    fprintf('\nInstructions:\n');
    fprintf('  - Use mouse to explore significant regions\n');
    fprintf('  - Right-click for options (overlays, export, etc.)\n');
    fprintf('  - Adjust threshold using GUI controls\n');
    fprintf('  - Use "Render" to create 3D brain renderings\n');
    
catch ME
    fprintf('Error opening results viewer: %s\n', ME.message);
    fprintf('\nAlternative: Use SPM GUI manually:\n');
    fprintf('  1. Type: spm\n');
    fprintf('  2. Click: Results\n');
    fprintf('  3. Select: %s\n', spm_file);
    fprintf('  4. Choose contrast: %d\n', contrast_num);
end

%% Generate statistics report
fprintf('\n────────────────────────────────────────────────────────────\n');
fprintf('Generating Statistics Report...\n');
fprintf('────────────────────────────────────────────────────────────\n');

try
    report_glm_statistics('first_level', subject_id, contrast_num, 0.001, 10);
catch ME
    fprintf('Could not generate report: %s\n', ME.message);
end

fprintf('\n✓ Visualization complete!\n');
fprintf('────────────────────────────────────────────────────────────\n\n');

end

