import json 
import argparse

def complete_challenge(name:str):
    with open('challenges.json','r') as file:
        data = json.loads(file.read())
    
    if name in data:
        data[name][0]['is_completed'] = True
    else:
        print("Invalid Name")
        return
    
    with open('challenges.json','w') as file:
        json.dump(data,file,indent=4)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Command line argument for code challenge completion")
    parser.add_argument("arg1",type=str, help="Challenge name found in 'challenges.json'")
    args = parser.parse_args()
    challenge_name = args.arg1
    complete_challenge(challenge_name)