import numpy as np

def initialization(SearchAgents_no, dim, ub, lb):
    """
    Initialize Population Positions
    
    Parameters:
    SearchAgents_no (int): Ukuran populasi
    dim (int): Dimensi masalah
    ub (float atau list/array): Batas atas
    lb (float atau list/array): Batas bawah
    
    Returns:
    Positions (numpy.ndarray): Matriks posisi awal
    """
    
    Boundary_no = 1
    if isinstance(ub, (list, np.ndarray)):
        Boundary_no = len(ub)
    
    Positions = np.zeros((SearchAgents_no, dim))
    
    # Jika semua variabel memiliki batas yang sama (Skalar)
    if Boundary_no == 1:
        Positions = np.random.rand(SearchAgents_no, dim) * (ub - lb) + lb
        
    # Jika setiap variabel memiliki batas yang berbeda (Vektor)
    if Boundary_no > 1:
        for i in range(dim):
            ub_i = ub[i]
            lb_i = lb[i]
            Positions[:, i] = np.random.rand(SearchAgents_no) * (ub_i - lb_i) + lb_i
            
    return Positions