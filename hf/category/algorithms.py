
def worst(category):
    status = -1
    for mod in category.module_list:
        if mod.dataset is None:
            continue
        if status == -1 and int(mod.dataset['status']) != -2:
            status = mod.dataset['status']
        elif(mod.dataset['status'] < status and mod.dataset['status'] >= 0 and mod.config['type'] == 'rated'):
            status = mod.dataset['status']
    return status