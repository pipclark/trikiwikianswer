
from flask import Flask, json, jsonify
import flask_cors
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import csv
import random
from datetime import date

import time



def getanswer():
    # call a random word from this free random word generator from RazorSh4rk
    #decided the words were a bit too obscure and wanted to make it easier
    #URL = "https://random-word-api.herokuapp.com/word?number=1&swear=0"#"https://en.wikipedia.org/api/rest_v1/page/random/summary"#"https://en.wikipedia.org/w/api.php"

    #print('Sending requests...')
    #WORD = "filler_that's_too_long"

    global WORD # so that it can be sent outside of the function, schedule doesn't allow objects to be returned

    # first check if a word was already set for today
    WORD = check_if_set_today()
    if WORD != '': # word is already set
        return

    # Otherwise, pick a new word for today
    S = requests.Session()
    wiki_exists = False

    while not wiki_exists:
        # take a random word from the list
        WORD = random.choice(list)

        print('random word = ', WORD)
        #print(len(WORD))

        #check word wasn't already used against record of used words
        if check_if_word_already_used(): # when it returns true, word was already used
            continue # pick another word

        # check WORD has got a wikipage
        wikiURL = f'https://en.wikipedia.org/w/api.php?action=parse&format=json&page={WORD}'
        wiki_exists = check_wiki_page(wikiURL, S)
        #print(wiki_exists)

    print(f"the new word for today is {WORD}")

    # write the new answer to the first blank line of the record file to stop words being repeated
    record_word(WORD)

# check if a word was already set for today
def check_if_set_today():
    todaysword = ''
    with open('usedwords.csv') as f:
        reader = csv.reader(f, delimiter=",")
        for row in reader:
            lastdate = row[0]  # date in first column, this will take it's final value from last row
            # a little wasteful since it still reads through all rows though
    print('last date used = ' + lastdate)

    if lastdate == str(date.today()):
        todaysword = row[1]
        print('word for today is already set, words is ' + todaysword)
    return todaysword

# check word wasn't already used against record of used words
def check_if_word_already_used():
    usedwords = []
    with open('usedwords.csv') as f:
        reader = csv.reader(f, delimiter=",")
        for row in reader:
            usedwords.append(row[1])  # words are in the second column

    if WORD in usedwords:
        print('word already used, picking a new word')
        return True  # go back to start of loop and pick a new word
    print("word not used previously")

# check WORD has got a wikipage
def check_wiki_page(wikiURL, session):
    global WORD
    R2 = session.get(url=wikiURL)
    DATA = R2.json()
    try:
        maintext = DATA["parse"]["text"]["*"] # string. up to 'text' is dictionary.
        print("wikipage exists")
    except:
        print("wikipage doesn't exist")
        return False

    # from here we know the page exists so don't need to try
    redirects, redirect_word = check_redirect(maintext)
    if redirects:
        WORD = redirect_word
        # check again if that word was already used
        if check_if_word_already_used():
            return getanswer() # rerun whole function
        redirect_wikiURL = f'https://en.wikipedia.org/w/api.php?action=parse&format=json&page={WORD}'
        print('word changed, go back to start of this function with new page')
        return check_wiki_page(redirect_wikiURL, session)
    elif(check_number_links(maintext) > 100):
        return True
    else:
        print('not enough wiki links on page')
        return False

def check_redirect(maintext):
    if maintext.lower().find('redirect to') != -1: # if it finds 'redirect' in the text returns true. .lower() makes all cases in maintext lower case. Might slow it down though
        #print(maintext)
        print('page redirects to:')
        redirect_str = 'class="redirectText"><li><a href="/wiki/'
        redirect_word_start_idx = maintext.lower().find(redirect_str.lower()) + len(redirect_str)
        redirect_word_end_idx = maintext.lower().find('\" title=\"') #the \" is so can search for "" in string
        redirect_word = maintext[redirect_word_start_idx:redirect_word_end_idx]
        print(redirect_word)
        return True, redirect_word
    print('page does not redirect')
    return False, ''

def check_number_links(maintext):
    print(maintext.count('<a href="/wiki/'), ' links on the page')
    return maintext.count('<a href="/wiki/') # counts number of wiki links on page

def record_word(WORD):
    with open('usedwords.csv', 'a', newline='') as f:  # a for append
        writer = csv.writer(f, delimiter=',', )
        writer.writerow([date.today(), WORD])

app = Flask(__name__)
CORS(app)

# load the list of 1000 most common nouns in english from https://www.wordexample.com/list/most-common-nouns-english
# changed to list of common nouns from www.randomlists as these were less abstract, and had more "real" objects.
list = []
with open('randomnouns.csv') as f:
    reader = csv.reader(f, delimiter=",")
    for row in reader:
        list.append(row[0])
#print(list)
WORD = '' # temporary filler string
getanswer() # initial run so that a random word is chosen when heroku "wakes up"

# Note now that not using schedule could just set WORD = getanswer() and return the word instead of making it global

#scheduler to pick a new word from the list that has a wikipage each day
# NOTE this doesn't work in heroku (free) because it falls asleep after inactivity.
# But still useful for testing if want a bunch of new words.
# In that case disable the function that checks if a word was already set for today

#scheduler = BackgroundScheduler(timezone="Europe/Berlin")
#job = scheduler.add_job(getanswer, 'interval', minutes=10)
#scheduler.start()


@app.route('/')
def index():
    return f"{WORD}" # display the answer word on the page

@app.route('/sendword')
def sendword():
    global WORD

    return jsonify(WORD)


#@app.route('/sendtrikiwiki', methods=['GET', 'POST'])
#def sendtriki():

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run()
