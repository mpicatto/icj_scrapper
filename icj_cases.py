#lib imports
import bs4
import requests 
from bs4 import BeautifulSoup
import psycopg2

#globals
cases=[]
pending_cases=[]
db_data="db information here"

#funtion to connect to URL and retrieve html code
def connection(url):
    headers = ({
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'Accept-Lenguage':'en-US, en;q=0.5'})
    r = requests.get(url=url,headers=headers)
    soup = BeautifulSoup(r.content,'lxml')
    return soup

#function to scrape closed case list from ICJ
def scrape_closed_list():
    url = "https://www.icj-cij.org/en/list-of-all-cases"
    soup = connection(url)
    all_rows = [i for i in soup.find_all(['td'])]
    rows=[]
    status="closed"
    for row in all_rows:
        if not row.get("class"):
            link = row.find('a')
            rows.append(row)
            if link!=None:
                link=link.get('href')
                rows.append(link)
    
    create_case_dict(rows,status)        

#function to scrape open cases 
def scrape_open_list():
    url = "https://www.icj-cij.org/en/pending-cases"
    soup = connection(url)
    open_cases = [i for i in soup.find_all('ol')]
    for case in open_cases[0]:
        status='current'
        pending_cases(case,status)
    for case in open_cases[1]:
        status='pending'
        pending_cases(case,status)

#function to create open cases lists 
def pending_cases(case,status):
    rows=[]
    if isinstance(case,bs4.element.Tag):
        link=case.find('a')
        link=link.get('href')
        rows.extend([case,link])
        create_case_dict(rows,status)

#function to create case object (dictionary)
def create_case_dict(rows, status):
    i=0
    base_url='https://www.icj-cij.org'
    while i <len(rows):
        if status=="current" or status=="pending":
            introduction = ""
            culmination = ""
            type=status
        else:
            introduction=rows[i+2].text
            culmination=rows[i+3].text
            type=rows[i+4].text

        icj_case={
            "subject":rows[i].text,
            "link":base_url+rows[i+1],
            "introduction":introduction,
            "culmination":culmination,
            "type":type,
            "status":status,
            "overview":""
        }
        icj_case["subject"]=icj_case["subject"].replace('\n','')
        icj_case["introduction"]=icj_case["introduction"].replace('\n','')
        icj_case["culmination"]=icj_case["culmination"].replace('\n','')
        icj_case["type"]=icj_case["type"].replace('\n','')
        cases.append(icj_case)
        i += 5

# scrape case overview 
def scrape_overview(cases):
    for case in cases:
        url=case["link"]
        soup = connection(url)
        overview = soup.find('section',{'class':'font-serif'})
        if overview == None:
            case["overview"]="Not Available"
        else:
            case["overview"]=overview.text
        db_insert(case)
#Prev db table destroy
def db_destroy():
    conn=psycopg2.connect(db_data)
    cursor=conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS cases")
    conn.commit()
    conn.close              

# db table creation 
def db_creation():
    conn=psycopg2.connect(db_data)
    cursor=conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS cases(id SERIAL PRIMARY KEY,subject TEXT, link VARCHAR(50) ,introduction VARCHAR(15),culmination VARCHAR(15),type VARCHAR(15),status VARCHAR(15),overview TEXT )")
    conn.commit()
    conn.close

#insert values in db
def db_insert(case):
    conn=psycopg2.connect(db_data)
    cursor=conn.cursor()
    cursor.execute("INSERT INTO cases(subject,link,introduction,culmination,type,status,overview) VALUES(%s,%s,%s,%s,%s,%s,%s)",(case["subject"],case["link"],case['introduction'],case['culmination'],case['type'],case['status'],case['overview']))
    conn.commit()
    conn.close

db_destroy()
db_creation()
scrape_closed_list()
scrape_open_list()
scrape_overview(cases)
print("task completed")

