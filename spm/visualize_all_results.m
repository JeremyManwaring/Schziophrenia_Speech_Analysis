% Visualize All GLM Results
% Run this after GLM analysis is complete

init_spm;

% Visualize T-tests for subject 01
show_glm_results('01', 1);
pause(2);

show_glm_results('01', 2);
pause(2);

show_glm_results('01', 3);
pause(2);

show_glm_results('01', 4);
pause(2);

show_glm_results('01', 5);
pause(2);

show_glm_results('01', 6);
pause(2);

show_glm_results('01', 7);
pause(2);

% Visualize F-tests for subject 01
show_glm_results('01', 1, true);  % All Conditions
pause(2);
show_glm_results('01', 2, true);  % Condition Differences
