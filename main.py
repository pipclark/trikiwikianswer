
from flask import Flask, json, jsonify
import flask_cors
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import csv
import random

import time



def getanswer():
    # call a random word from this free random word generator from RazorSh4rk
    #decided the words were a bit too obscure and wanted to make it easier
    #URL = "https://random-word-api.herokuapp.com/word?number=1&swear=0"#"https://en.wikipedia.org/api/rest_v1/page/random/summary"#"https://en.wikipedia.org/w/api.php"

    #print('Sending requests...')
    #WORD = "filler_that's_too_long"

    global WORD # so that it can be sent outside of the function

    S = requests.Session()
    wikiexists = False
    while wikiexists == False:
        wikiexists = False
        #previous stuff from randomword-api
        #R = S.get(url=URL)
        #WORD = R.json()
        #WORD = WORD[0] # get the string inside the array of length 1 requested

        # take a random word from the list
        WORD = random.choice(list)
        print(WORD)
        print(len(WORD))

        # check WORD has got a wikipage
        wikiURL = f'https://en.wikipedia.org/w/api.php?action=parse&format=json&page={WORD}'
        #print(wikiURL)

        R2 = S.get(url=wikiURL)
        DATA = R2.json()
        try:
            TITLE = DATA["parse"]["title"]
            wikiexists = True
            print("wikipage exists")
        except:
            print("wikipage doesn't exist")

    print(f"done, today's word is {WORD}")
    #return WORD

app = Flask(__name__)
CORS(app)

# load the list of 1000 most common nouns in english from https://www.wordexample.com/list/most-common-nouns-english
list = []
with open('most-common-nouns-english.csv') as f:
    reader = csv.reader(f, delimiter=",")
    for row in reader:
        list.append(row[0])
#print(list)
WORD = "filler"

#scheduler to pick a new word from the list that has a wikipage each day
scheduler = BackgroundScheduler(timezone="Europe/Berlin")
job = scheduler.add_job(getanswer, 'interval', seconds=10)
scheduler.start()


@app.route('/')
def index():
    return f"{WORD}"

@app.route('/sendword')
def sendword():
    global WORD

    return jsonify(WORD)


#@app.route('/sendtrikiwiki', methods=['GET', 'POST'])
#def sendtriki():

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run()
