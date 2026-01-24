import time
import numpy as np

def CAOA(N, max_iter, lb, ub, dim, fobj, 
         alpha=0.5, beta=0.1, gamma=0.8, delta=1e-4, initial_energy=100.0,
         verbose_interval=100):
    
    if np.isscalar(lb): lb = np.full(dim, lb)
    else: lb = np.array(lb)
    if np.isscalar(ub): ub = np.full(dim, ub)
    else: ub = np.array(ub)
    
    pos = lb + (ub - lb) * np.random.rand(N, dim)
    energies = initial_energy * np.ones(N)
    fitness = np.zeros(N)
    
    for i in range(N):
        fitness[i] = fobj(pos[i, :])
        
    best_idx = np.argmin(fitness)
    gBestScore = fitness[best_idx]
    gBest = pos[best_idx, :].copy()
    cg_curve = np.zeros(max_iter)
    
    # Header Verbose
    print(f"{'Iter':<10} | {'Runtime (s)':<12} | {'Depleted':<10} | {'Pop Size':<10} | {'Best Fitness':<20}")
    print("-" * 80)
    
    start_time = time.time()

    for t in range(max_iter):
        old_positions = pos.copy()
        old_fitness = fitness.copy()
        n_depleted_count = 0
        
        probs = 1.0 / (1.0 + np.abs(fitness))
        leader_idx = np.argmax(probs)
        leader_position = pos[leader_idx, :].copy()
        
        for i in range(N):
            if i == leader_idx: continue
            r = np.random.rand(dim)
            new_pos = pos[i, :] + alpha * (leader_position - pos[i, :]) + beta * (1.0 - 2.0 * r)
            new_pos = np.clip(new_pos, lb, ub)
            new_fit = fobj(new_pos)
            
            if abs(new_fit - old_fitness[i]) > delta and new_fit > old_fitness[i]:
                new_pos = lb + (ub - lb) * np.random.rand(dim)
                new_fit = fobj(new_pos)
            
            pos[i, :] = new_pos
            fitness[i] = new_fit

        distances = np.sqrt(np.sum((pos - old_positions)**2, axis=1))
        energies = energies - gamma * distances
        
        depleted = energies <= 0
        if np.any(depleted):
            n_depleted_count = np.sum(depleted)
            random_positions = lb + (ub - lb) * np.random.rand(n_depleted_count, dim)
            pos[depleted, :] = random_positions
            energies[depleted] = initial_energy
            for idx in np.where(depleted)[0]:
                fitness[idx] = fobj(pos[idx, :])

        # Update Global Best
        min_fit = np.min(fitness)
        min_idx = np.argmin(fitness)
        if min_fit < gBestScore:
            gBestScore = min_fit
            gBest = pos[min_idx, :].copy()
            
        cg_curve[t] = gBestScore
        
        if (t + 1) % verbose_interval == 0 or t == 0:
            elapsed = time.time() - start_time
            print(f"{t+1:<10} | {elapsed:<12.2f} | {n_depleted_count:<10} | {N:<10} | {gBestScore:.6e}")

    return gBestScore, gBest, cg_curve