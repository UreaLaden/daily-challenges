import json 

def complete_challenge(name:str):
    with open('challenges.json','rw') as file:
        data = json.loads(file.read())
    
    if name in data:
        data[name]['is_completed'] = True
    
    with open('challenges.json','w') as file:
        json.dump(data,file,indent=4)
