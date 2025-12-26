% Define the objective function (Sphere)
sphere = @(x) sum(x.^2);

% Parameter Settings
beta_values = [0.05, 0.1, 0.2, 0.3, 0.4]; % β test value
num_runs = 10; dim = 30; N = 30; iter = 500;
lb = -100; ub = 100;

% Fixed other parameters
alpha = 0.5;
gamma = 0.1;
delta = 1e-4;
initial_energy = 100;

% Record the results
results_beta = zeros(length(beta_values), num_runs);

% Main Loop
for i = 1:length(beta_values)
    for j = 1:num_runs
        [bestScore, ~, ~] = CAOA(N, iter, lb, ub, dim, sphere, ...
            alpha, beta_values(i), gamma, delta, initial_energy);
        results_beta(i, j) = bestScore;
    end
end

% Calculate the mean and standard deviation
mean_beta = mean(results_beta, 2);
std_beta = std(results_beta, 0, 2);

% drawing
figure;
errorbar(beta_values, mean_beta, std_beta, '-o', 'LineWidth', 2, 'CapSize', 6);
xlabel('\beta');
ylabel('Best Score (Mean \pm Std)');
title('Sensitivity Analysis of \beta in CAOA');
grid on;