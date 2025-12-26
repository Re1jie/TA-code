function [gBestScore,gBest,cg_curve] = CAOA(N,iter,lb,ub,dim,fobj,alpha,beta,gamma,delta,initial_energy)
    % Default Parameter Values Handling
    if nargin < 11
        initial_energy = 100.0;
        if nargin < 10
            delta = 1e-4;
            if nargin < 9
                gamma = 0.1;
                if nargin < 8
                    beta = 0.1;
                    if nargin < 7
                        alpha = 0.5;
                    end
                end
            end
        end
    end
    
    % Ensure that the boundary is a vector
    if isscalar(lb)
        lb = repmat(lb, 1, dim);
    end
    if isscalar(ub)
        ub = repmat(ub, 1, dim);
    end
    
    % Initialize Population
    pos = lb + (ub - lb) .* rand(N, dim);
    energies = initial_energy * ones(N, 1);
    fitness = zeros(N, 1);
    
    % Calculate the initial fitness
    for i = 1:N
        fitness(i) = fobj(pos(i, :));
    end
    
    % Global Optimal Initialization
    [gBestScore, best_idx] = min(fitness);
    gBest = pos(best_idx, :);
    cg_curve = zeros(1, iter);
    
    % Optimize the cycle
    for t = 1:iter
        old_positions = pos;
        old_fitness = fitness;
        
        % Selecting Leaders
        probs = 1 ./ (1 + fitness);
        [~, leader_idx] = max(probs);
        leader_position = pos(leader_idx, :);
        
        %Update individual location
        for i = 1:N
            if i == leader_idx, continue; end
            
            r = rand(1, dim);
            new_pos = pos(i, :) + alpha * (leader_position - pos(i, :)) + beta * (1 - 2 * r);
            
            % Boundary Handling
            Flag4ub = new_pos > ub;
            Flag4lb = new_pos < lb;
            new_pos = (new_pos .* (~(Flag4ub+Flag4lb))) + ub.*Flag4ub + lb.*Flag4lb;
            
            new_fit = fobj(new_pos);
            
            if abs(new_fit - old_fitness(i)) > delta && new_fit > old_fitness(i)
                new_pos = lb + (ub - lb) .* rand(1, dim);
                new_fit = fobj(new_pos);
            end
            
            pos(i, :) = new_pos;
            fitness(i) = new_fit;
        end
        
        % Recharge Energy
        distances = sqrt(sum((pos - old_positions).^2, 2));
        energies = energies - gamma * distances;
        
        % Reset depleted individuals
        depleted = energies <= 0;
        if any(depleted)
            n_depleted = sum(depleted);
            pos(depleted, :) = lb + (ub - lb) .* rand(n_depleted, dim);
            energies(depleted) = initial_energy;
            for i = find(depleted)'
                fitness(i) = fobj(pos(i, :));
            end
        end
        
        %Update Global Optimal
        [min_fit, min_idx] = min(fitness);
        if min_fit < gBestScore
            gBestScore = min_fit;
            gBest = pos(min_idx, :);
        end
        
        % Record the convergence curve
        cg_curve(t) = gBestScore;
    end
end


