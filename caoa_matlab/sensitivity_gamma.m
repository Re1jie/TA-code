sphere = @(x) sum(x.^2);
gamma_values = [0.01, 0.05, 0.1, 0.2]; % γ test value
num_runs = 10; dim = 30; N = 30; iter = 500;
lb = -100; ub = 100;

% Fixed other parameters
alpha = 0.5; beta = 0.1;
delta = 1e-4;
initial_energy = 100;

results_gamma = zeros(length(gamma_values), num_runs);

for i = 1:length(gamma_values)
    for j = 1:num_runs
        [bestScore, ~, ~] = CAOA(N, iter, lb, ub, dim, sphere, ...
            alpha, beta, gamma_values(i), delta, initial_energy);
        results_gamma(i, j) = bestScore;
    end
end

mean_gamma = mean(results_gamma, 2);
std_gamma = std(results_gamma, 0, 2);

figure;
errorbar(gamma_values, mean_gamma, std_gamma, '-o', 'LineWidth', 2, 'CapSize', 6);
xlabel('\gamma');
ylabel('Best Score (Mean \pm Std)');
title('Sensitivity Analysis of \gamma in CAOA');
grid on;