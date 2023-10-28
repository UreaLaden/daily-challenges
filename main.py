from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import schedule
from bs4 import BeautifulSoup
import pandas as pd
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv 
import os

load_dotenv()

"""
 Write a Script that does the following
 - Extract a list of coding challenges
 - The challenges should be parsed into JSON format and provide the following information:
    - Title
    - Blessing
    - Problem Number
    - Scenario
    - Example
    - URL
 - Script will first obtain the problem and url, convert to JSON and store in a text file
 - Once daily the script will make a request to one of the problem urls, format the data, and email to the address provided

 The intent is to create a power automate flow that will trigger on receipt of this email sending a message via teams notifying the user of the day's challenge
"""
base = os.getenv("BASE_URL")
main_url = f"{base}/index/task_list"

def get_page_source(main_url:str,file_name:str):
    if os.path.exists(f"{file_name}.txt"):
        print(f"File '{file_name}.txt' already exists. Skipping Extraction.\n")
        return 
    
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(main_url)
        page = driver.page_source

        with open(f"{file_name}.txt",'w') as file:
            file.write(page)

        driver.quit()
    except Exception as error:
        print(f"There was an error: {error}")

def convert_source_to_json(source_file:str):
    parsed_data = {}

    with open(source_file,'r') as file:
        data = file.read()

    soup = BeautifulSoup(data,'html.parser') 

    tbody = soup.find_all('tbody')
    largest_body = []
    for body in tbody:
        largest_body = body if len(body) > len(largest_body) else largest_body

    # Get all urls
    for row in largest_body.find_all('td'):  
        url = row.find('a')  
        if url is not None :
            is_user_profile = 'user_profile' in url.get('href') 
            is_locale = url.get('class') != None

            if not is_user_profile and not is_locale:
                endpoint = f"{base}{url.get('href')}"
                challenge_data = {
                    'endpoint':endpoint,
                    'is_completed': False
                }
                url_text = url.text
                if url_text in parsed_data:
                    parsed_data[url.text].append(challenge_data)
                else:
                    parsed_data[url_text] = [challenge_data]

    json_string = json.dumps(parsed_data,ensure_ascii=False,indent=4)
    
    with open('challenges.json','w') as file:
        file.write(json_string)

def get_next_challenge(file_name:str):
    try:
        with open(f'{file_name}.json','r') as file:
            challenge_data = json.load(file)
            for name in challenge_data.keys():
                if challenge_data[name][0]['is_completed'] == False:
                    return (name,challenge_data[name][0])
    except FileNotFoundError as error:
        print(f"JSON file not found - {error}")
        return None
    except json.JSONDecodeError as error:
        print(f"Invalid JSON data. {error}")
        return None
    
    print("No remaining challenges. Great Job!")
    return None

def get_challenge_text(soup:BeautifulSoup):
    return ' '.join([p.text.strip() for p in soup.select('div[dir="ltr"] p')])

def extract_challenge_data(url:str):
    file_name = 'daily_challenge'
    print("Extracting Daily Challenge\n")
    
    get_page_source(url,file_name)

    with open(f"{file_name}.txt",'r') as file:
        soup =  BeautifulSoup(file.read(),'html.parser')
      
    challenge = get_challenge_text(soup)
    return (challenge,url)
    

def send_todays_challenge(challenge:tuple[str,str]):
    service = 'smtp.gmail.com'
    port = 587    
    sender =  os.getenv("SENDER_EMAIL")
    receiver = os.getenv("RECEIVER_EMAIL")
    key = os.getenv("KEY")

    message = MIMEMultipart()
    message['From'] = sender 
    message['To'] = receiver 
    message['Subject'] = f'Code Challenge: {challenge[1].split('/')[-1].title()}'
    
    message.attach(MIMEText(challenge[0],'plain'))
    try:
        server = smtplib.SMTP(service,port)
        server.starttls()
        server.login(sender,key)
        server.sendmail(sender,receiver,message.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send the email: {str(e)}")
    finally:
        server.quit()

def send_challenges():
    next_challenge = get_next_challenge('challenges')
    url = next_challenge[1]['endpoint']
    todays_challenge = extract_challenge_data(url)
    print(f"Todays Challenge:\n{todays_challenge[0]}\n")
    send_todays_challenge(todays_challenge)

def has_challenges():
    with open('challenges.json','r') as file:
        data = json.loads(file.read())
        return False in [data[i][0]['is_completed'] for i in data]

if __name__ == '__main__':
    schedule.every().day.at("09:00").do(send_challenges)
    while has_challenges():
        time.sleep(3600)