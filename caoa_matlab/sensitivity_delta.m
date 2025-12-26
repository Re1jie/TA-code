sphere = @(x) sum(x.^2);
delta_values = [1e-6, 1e-5, 1e-4, 1e-3]; % Test value of δ
num_runs = 10; dim = 30; N = 30; iter = 500;
lb = -100; ub = 100;

alpha = 0.5; beta = 0.1; gamma = 0.1;
initial_energy = 100;

results_delta = zeros(length(delta_values), num_runs);

for i = 1:length(delta_values)
    for j = 1:num_runs
        [bestScore, ~, ~] = CAOA(N, iter, lb, ub, dim, sphere, ...
            alpha, beta, gamma, delta_values(i), initial_energy);
        results_delta(i, j) = bestScore;
    end
end

mean_delta = mean(results_delta, 2);
std_delta = std(results_delta, 0, 2);

figure;
errorbar(delta_values, mean_delta, std_delta, '-o', 'LineWidth', 2, 'CapSize', 6);
xlabel('\delta');
ylabel('Best Score (Mean \pm Std)');
title('Sensitivity Analysis of \delta in CAOA');
grid on;