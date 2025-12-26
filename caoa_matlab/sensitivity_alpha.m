% Define the objective function (Sphere)
sphere = @(x) sum(x.^2);

% Parameter Settings
alpha_values = [0.1, 0.3, 0.5, 0.7, 0.9]; % α test value
num_runs = 10;       % Number of repetitions for each α value
dim = 30;            % Dimension
N = 30;              % Population size
iter = 500;          % Maximum number of iterations
lb = -100; ub = 100; % Search Space Boundary

% Fixed other parameters
beta = 0.1;
gamma = 0.1;
delta = 1e-4;
initial_energy = 100;

% Record the results
results_alpha = zeros(length(alpha_values), num_runs);

% 主循环
for i = 1:length(alpha_values)
    for j = 1:num_runs
        [bestScore, ~, ~] = CAOA(N, iter, lb, ub, dim, sphere, ...
            alpha_values(i), beta, gamma, delta, initial_energy);
        results_alpha(i, j) = bestScore;
    end
end

% Calculate the mean and standard deviation
mean_alpha = mean(results_alpha, 2);
std_alpha = std(results_alpha, 0, 2);

% drawing
figure;
errorbar(alpha_values, mean_alpha, std_alpha, '-o', 'LineWidth', 2, 'CapSize', 6);
xlabel('\alpha');
ylabel('Best Score (Mean \pm Std)');
title('Sensitivity Analysis of \alpha in CAOA');
grid on;