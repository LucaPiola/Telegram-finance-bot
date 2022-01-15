from ast import Return
from getpass import getpass
import time
import os
import shutil
import logging
import csv
import pandas as pd
import requests
from datetime import date 
from telegram import Bot
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
import matplotlib
import matplotlib.pyplot as pp

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)
token = ""
MODIFICA, SCELTA, ENTRATA, USCITA,DESCRIZIONE_EN,DESCRIZIONE_US,  GRAFICO, BILANCIO_MENS1  = range(8)
entrate = 0
uscite = 0
entrataTemp = 0
uscitaTemp = 0
thumbs_up_emoji = u'\U0001F44D' 
reply_keyboard = [['Entrata', 'Uscita', 'Bilancio', 'Bilancio mensile']]
scelteMenu = [['Entrata'], ['Uscita'], ['Bilancio'], ['Bilancio mensile'], ['Download dati'], ['Rimuovi ultimo']]
def start(update: Update, context: CallbackContext) -> int:
    name = update.message.from_user.first_name
    
    update.message.reply_text(
        u'\U0001F4B6' 
        f' Benvenuto *{name}*, scegli un\'operazione dal menù ' u'\U0001F4B6' ,
        
        reply_markup=ReplyKeyboardMarkup(scelteMenu, one_time_keyboard=True), parse_mode='Markdown'
    )

    #spazio debug
    

    return SCELTA
           
def scelta(update: Update, context: CallbackContext) -> int:
    global reply_keyboard
    attivita =  update.message.text
    
    if (attivita == 'Entrata'):
        update.message.reply_text('Inserisci l\'entrata \U00002B06')
        return ENTRATA
    if (attivita == 'Uscita'):
        update.message.reply_text('Inserisci l\'uscita \U00002B07')
        return USCITA
    if (attivita == 'Bilancio'):
        update.message.reply_text(f'\U00002B06 Entrate = € {sumEntrate(update)} \n\U00002B07 Uscite = € {sumUscite(update)} \n\U0001F504 Saldo = € *{readBalance(update)}*',  reply_markup=ReplyKeyboardMarkup(scelteMenu), parse_mode='Markdown')
        return SCELTA
    if (attivita == 'Bilancio mensile'):
        update.message.reply_text('Scegli il mese che vuoi vedere: (da 1 a 12)')
        return BILANCIO_MENS1
    if (attivita == 'Download dati'):
        update.message.reply_text('Invio i dati salvati \U00002B07')
        sendFile(update)
    if (attivita == 'Rimuovi ultimo'):
        if ((sumEntrate(update) != 0) | (sumUscite(update) != 0)):
            update.message.reply_text('Rimuovo l\'ultimo dato salvato.')
            removeLastRow(update)
            update.message.reply_text('Aggiorno il bilancio...')
            time.sleep(1.5)
            update.message.reply_text(f'\U00002B06 Entrate = € {sumEntrate(update)} \n\U00002B07 Uscite = € {sumUscite(update)} \n\U0001F504 Saldo = € *{readBalance(update)}*',  reply_markup=ReplyKeyboardMarkup(scelteMenu), parse_mode='Markdown')
            return SCELTA
        else:
            update.message.reply_text('Non ci sono dati da rimuovere.')
    

def bilancio_mens1(update: Update, context: CallbackContext) -> int: 
    global entrate, uscite
    mese = int(update.message.text)
    balanceMensile = readBalance(update, mese)
    entrateMensile = sumEntrate(update, mese)
    usciteMensile= sumUscite(update, mese)
    update.message.reply_text(f'Bilancio del mese di {getMonth(mese)} pari a € {balanceMensile}\nEntrate pari a € {entrateMensile}\nUscite pari a € {usciteMensile}',  reply_markup=ReplyKeyboardMarkup(scelteMenu))
    return SCELTA

def entrata(update: Update, context: CallbackContext) -> int: 
    global entrate, uscite, entrataTemp
    try:
        entrataTemp = float(update.message.text)
    except:
        update.message.reply_text('\U0000203C  Errore nell\'inserimento dei dati \U0000203C',  reply_markup=ReplyKeyboardMarkup(scelteMenu))
        return SCELTA
    update.message.reply_text('\U00002753 Inserisci la descrizione dell\'entrata')
    return DESCRIZIONE_EN

def descrizione_en(update: Update, context: CallbackContext) -> int: 
    desc = str(update.message.text)
    logMoney(entrataTemp, update, desc)
    update.message.reply_text(f'Aggiungo €{entrataTemp} al tuo saldo \U0001F63B',  reply_markup=ReplyKeyboardMarkup(scelteMenu))
    return SCELTA

def uscita(update: Update, context: CallbackContext) -> int: 
    global entrate, uscite, uscitaTemp
    try:
        uscitaTemp =  float(update.message.text)
    except:
        update.message.reply_text('\U0000203C Errore nell\'inserimento dei dati \U0000203C',  reply_markup=ReplyKeyboardMarkup(scelteMenu))
        return SCELTA
    update.message.reply_text('\U00002753 Inserisci la descrizione dell\'uscita')
    return DESCRIZIONE_US

def descrizione_us(update: Update, context: CallbackContext) -> int: 
    desc = str(update.message.text)
    logMoney(-uscitaTemp, update, desc)
    update.message.reply_text(f'Aggiungo €{uscitaTemp} alle tue uscite \U0001F63F',  reply_markup=ReplyKeyboardMarkup(scelteMenu))
    return SCELTA

#this function might be removed
def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

        
#main bot function to handle the conversation
def main() -> None:
    
    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher


    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SCELTA: [MessageHandler(Filters.regex('^(Entrata|Uscita|Bilancio|Bilancio mensile|Download dati|Rimuovi ultimo)$'), scelta)],
            ENTRATA: [MessageHandler(Filters.text, entrata, pass_user_data=True)],
            USCITA: [MessageHandler(Filters.text, uscita, pass_user_data=True)],
            BILANCIO_MENS1: [MessageHandler(Filters.text, bilancio_mens1, pass_user_data=True)],
            DESCRIZIONE_EN: [MessageHandler(Filters.text, descrizione_en, pass_user_data=True)],
            DESCRIZIONE_US: [MessageHandler(Filters.text, descrizione_us, pass_user_data=True)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
         allow_reentry = True,
    )

    dispatcher.add_handler(conv_handler)

    #starting bot
    updater.start_polling()
    updater.idle()

def getTimeInfo():
    month = date.today().month
    day = date.today().day
    year = date.today().year
    return [day, month, year]

def logMoney(cash, update, desc):
    logName = update.message.from_user['id']
    nomeFile = "LOG/" + str(logName) +".csv"
    file = open(nomeFile, 'a', newline ='') 
    dataLog = [cash, getTimeInfo()[0], getTimeInfo()[1], getTimeInfo()[2], desc]
    with file:
        writer = csv.writer(file, delimiter =';',quotechar =';',quoting=csv.QUOTE_MINIMAL)
        try: #Se non c'è il file scrivo prima riga 
            pd.read_csv(nomeFile, low_memory = True , usecols = [0], sep = ';')
        except:
            writer.writerow(['Cash', 'Giorno', 'Mese', 'Anno', 'Descrizione'])
        writer.writerow(dataLog)

def readBalance(update, mese=None):
    logName = update.message.from_user['id']
    nomeFile = "LOG/" + str(logName) +".csv"
    if mese == None:
        df = pd.read_csv(nomeFile, low_memory = True , usecols = [0], sep = ';')
        balance = df.sum()
        return round(balance[0], 2)
    else:
        df = pd.read_csv(nomeFile, low_memory = True , usecols = [0,2], sep = ';')
        balance = 0
        for index, row in df.iterrows():
            if row[1] == mese:
                balance += row[0]
        return round(balance, 2)

def sumEntrate(update, mese=None):
    logName = update.message.from_user['id']
    nomeFile = "LOG/" + str(logName) +".csv"
    entrate = 0
    if mese==None:
        df = pd.read_csv(nomeFile, low_memory = True , usecols = [0], sep = ';')
        for index, row in df.iterrows():
            if row[0] > 0:
                entrate += row[0]
        return round(entrate, 2)
    else:
        df = pd.read_csv(nomeFile, low_memory = True , usecols = [0,2], sep = ';')
        for index, row in df.iterrows():
            if (row[1] == mese) & (row[0] >0):
                entrate += row[0]
        return round(entrate, 2)

def sumUscite(update, mese=None):
    logName = update.message.from_user['id']
    nomeFile = "LOG/" + str(logName) +".csv"
    uscite = 0
    if mese == None:
        df = pd.read_csv(nomeFile, low_memory = True , usecols = [0], sep = ';')
        for index, row in df.iterrows():
            if row[0] < 0:
                uscite += row[0]
        return round(uscite, 2)
    else:
        df = pd.read_csv(nomeFile, low_memory = True , usecols = [0,2], sep = ';')
        for index, row in df.iterrows():
            if (row[1] == mese) & (row[0] < 0):
                uscite += row[0]
        return round(uscite, 2)

def getMonth(mese):
    monthDict = {
        "1": "Gennaio",
        "2": "Febbraio",
        "3": "Marzo",
        "4": "Aprile",
        "5": "Maggio",
        "6": "Giugno",
        "7": "Luglio",
        "8": "Agosto",
        "9": "Settembre",
        "10": "Ottobre",
        "11": "Novembre", 
        "12": "Dicembre"
    }
    return monthDict[str(mese)]

def sendFile(update):
    chat_id = update.effective_chat.id
    user_id = update.message.from_user['id']
    caption = "Spese e guadagni di " + update.message.from_user.first_name
    file = {'document':open(f'LOG/{user_id}.csv', 'rb')}
    url = 'https://api.telegram.org/bot' + str(token) + '/sendDocument?chat_id='+str(chat_id) + "&caption=" + caption
    resp = requests.post(url, files=file )

def removeLastRow(update):
    logName = update.message.from_user['id']
    nomeFile = "LOG/" + str(logName) +".csv"
    f = open(nomeFile, "r+")
    lines = f.readlines()
    lines.pop()
    f = open(nomeFile, "w+")
    f.writelines(lines)

if __name__ == '__main__':
    main()


