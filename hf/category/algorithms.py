
def worst(category):
    """
    Category status is the worst lowest status of all modules of the same
    type as the category (only plots or rated modules, depending) with
    positive status value (no error, data acquisition succeeded).
    'unrated' modules are always per definition excluded.
    
    If there is no correct module with positive status, the
    category status is set to -1 (no information).
    """
    status = 1.0
    for mod in category.module_list:
        if mod.dataset is None:
            continue
        if status > mod.dataset['status'] >= 0 and mod.type == category.type:
            status = mod.dataset['status']
    return status