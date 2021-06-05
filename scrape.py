"""
@author: Goh Kok Han
"""
from bs4 import BeautifulSoup
import re
import pandas as pd
import configparser
import requests
from github import Github
from datetime import date

config = configparser.ConfigParser()
try:
    #if you want to get notification in telegram 
    config.read('conf.ini')
    github_accessKey=config['GITHUB']['access_key']
    bot_key=config['TELEGRAM']['bot_key']
    chat_id=config['TELEGRAM']['chat_id']
    
except:
    pass

fileName='covid-19-malaysia-death-cases.csv'
links=[]
rows = []
keyword=['no. kematian','kes kematian','kes no. kematian','kes']
message="Updated: "+str(date.today())
data=''


def parse(r):
    if r.status_code==200:
        notify('*Successfully Scraped*')
        return BeautifulSoup(r.content,'lxml')
    else:
        notify('Error: '+str(r.status_code))
     
        
def simple_scrape(link):
    r=requests.get(link)
    return parse(r)    
 
def get_sitemap():
    sitemap=simple_scrape('https://kpkesihatan.com/sitemap.xml')
    
    for loc in sitemap.select('url > loc'):
           if  re.search(r'coronavirus-2019-covid-19-di-malaysia/$',loc.text.strip() ) :
                links.append(loc.text)
    return links

def append(rows,Table,link):
    data_rows = Table.find_all('tr')
    for index,row in enumerate(data_rows):
        value = row.find_all('td')
        beautified_value = [ele.text.strip() for ele in value]
        # Remove data arrays that are empty
        if len(beautified_value) == 0 or index==0:
            continue
        beautified_value.insert(len(beautified_value),link)
        rows.append(beautified_value)
    return rows


def pushToGithub(data):
    
    g = Github(github_accessKey)
    
    repo = g.get_repo("gohkokhan/covid19-death-malaysia")
    
    contents = repo.get_contents(fileName)
    
    repo.update_file(contents.path,message,data, contents.sha, branch="main")
    
    
def send_telegram(message):
    send_message_url = f'https://api.telegram.org/bot{bot_key}/sendMessage?chat_id={chat_id}&text={message}&parse_mode=markdown'
    requests.post(send_message_url)        

def notify(message):
    try:
        send_telegram(message)
    except:
        print(message)
       
link=get_sitemap()[0]
df=None
allTable = pd.read_html(link, header =0, flavor = 'lxml')
for table in allTable:
    if (table.columns[0].strip().lower()) in keyword:
        df=table
        break

if df is None or len(df.columns)!=6:
    notify('*Error: No data is loaded.*\n'+str(link))
   
else:
    df['link']=link
    df.to_csv(fileName, encoding='utf-8-sig',mode='a', header=False, index=False)
    notify('*Success! Preview of the data*: \n\n'+'_'+str(df.info)+'_')
    with open(fileName, 'r',encoding='utf-8-sig') as f:
        for row in f:
            data+=str(row)
    try:
        pushToGithub(data)
    except Exception as e:
        notify('*Error Push to GitHub: *\n'+str(e))



