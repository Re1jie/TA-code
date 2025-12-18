function Positions = initialization(SearchAgents_no, dim, ub, lb)
    %   Initialize Population Positions
    %   Input:
    %   SearchAgents_no - Population size
    %   dim - Problem dimension
    %   ub - Upper bound (scalar or vector)
    %   lb - Lower bound (scalar or vector)
    %   Output:
    %   Positions - Initialized population position matrix

    Boundary_no = size(ub, 2); % Boundary Count

    % If all variables share the same boundary
    if Boundary_no == 1
        Positions = rand(SearchAgents_no, dim) .* (ub - lb) + lb;
    end

    % If each variable has different boundaries
    if Boundary_no > 1
        Positions = zeros(SearchAgents_no, dim);
        for i = 1:dim
            ub_i = ub(i);
            lb_i = lb(i);
            Positions(:, i) = rand(SearchAgents_no, 1) .* (ub_i - lb_i) + lb_i;
        end
    end
end