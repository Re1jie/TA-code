sphere = @(x) sum(x.^2);
energy_values = [10, 50, 100, 200]; % Initial Energy Test Value
num_runs = 10; dim = 30; N = 30; iter = 500;
lb = -100; ub = 100;

alpha = 0.5; beta = 0.1; gamma = 0.1; delta = 1e-4;

results_energy = zeros(length(energy_values), num_runs);

for i = 1:length(energy_values)
    for j = 1:num_runs
        [bestScore, ~, ~] = CAOA(N, iter, lb, ub, dim, sphere, ...
            alpha, beta, gamma, delta, energy_values(i));
        results_energy(i, j) = bestScore;
    end
end

mean_energy = mean(results_energy, 2);
std_energy = std(results_energy, 0, 2);

figure;
errorbar(energy_values, mean_energy, std_energy, '-o', 'LineWidth', 2, 'CapSize', 6);
xlabel('Initial Energy');
ylabel('Best Score (Mean \pm Std)');
title('Sensitivity Analysis of Initial Energy in CAOA');
grid on;