import os 

class Options(dict):
    def __getattr__(self, attr):
        if attr in self:
            return self[attr]
        else:
            return None


def load(path):
    if not os.path.exists(path):
        return None

    options = Options() 
    with open(path, 'r') as file:
        for line in file:
            prop, val  = line.split(':')
            options[prop.strip()] = val.strip()
    file.close()

    return options 
