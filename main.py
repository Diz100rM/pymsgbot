# -*- coding: utf-8 -*-
import re
import time
import datetime
import threading
import logging
from os import getenv
from collections import OrderedDict

import pymysql
import telebot
from telebot import types

import config
from config import VOTING_INTERVAL

"""Logging"""
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

"""Add TOKEN to BOT"""
bot = telebot.TeleBot(token=getenv('BOT_TOKEN', config.token))

"""Connecting to DB"""
con = pymysql.connect(user=getenv('USERNAME', config.db_user),
                      password=getenv('PASSWORD', config.db_pass),
                      database=getenv('DATABASE', config.db_name),
                      charset='utf8')
cursor = con.cursor()

"""Parsing Mode for bot messages"""
MDPARSE = "HTML"

timers = {'check': None}


class UpdateMessageTime:
    def __init__(self, lastmessage=0, forward_saving_time=0, chat_id=None):
        self.lastmessage = lastmessage
        self.forward_saving_time = forward_saving_time
        self.chat_id = chat_id
        self.data = {'date': None, 'owner': None, 'quote': [], 'media_id': []}
updateTime = UpdateMessageTime()


def forward_saving_timer(chat_id=None):
    if timers['check']:
        timers['check'].cancel()
    if not updateTime.chat_id:
        try:
            updateTime.chat_id = chat_id
        except AttributeError:
            print("ERROR WHILE TAKING CHAT ID")
    timer = threading.Timer(2.0, forward_saving_timer)
    timers['check'] = timer
    timer.start()
    if time.time() > updateTime.forward_saving_time + 2:
        print("DONE")
        timer.cancel()
        updateTime.forward_saving_time = 0
        format_quote = ''
        media_id = ''
        for i in updateTime.data['quote']:
            for key, value in i.items():
                if value == 'None':
                    value = '<b>Media File</b>'
                format_quote += str('<b>' + key + '</b>\n' + value + '\n\n')
        for i in updateTime.data['media_id']:
            media_id += i
        cursor.execute("INSERT INTO quotes(date, owner, quote, media_id) VALUES(%s, %s, %s, %s)",
                       (updateTime.data['date'], updateTime.data['owner'], format_quote, str(media_id)))
        con.commit()
        updateTime.data = {'date': None, 'owner': None, 'quote': [], 'media_id': []}
        cursor.execute("SELECT max(id) FROM quotes")
        bot.send_message(updateTime.chat_id, "Цитата успешно сохранена под <b>№" + str(cursor.fetchall()[0][0]) +
                         "</b>!", parse_mode=MDPARSE)


@bot.message_handler(content_types=['text', 'audio', 'voice', 'sticker', 'document', 'photo'],
                     func=lambda message: message.chat.type == "private" and message.forward_from)
def forward_saving(message):
    updateTime.forward_saving_time = time.time()
    if not updateTime.data['date']:
        updateTime.data['date'] = str(str(datetime.datetime.now().date()).replace('-', '.'))
    if not updateTime.data['owner']:
        updateTime.data['owner'] = str(message.from_user.first_name)
    someone = str(message.forward_from.first_name)
    quote_text = str(message.text)
    media_dict = {"doc": message.document,
                  "stick": message.sticker,
                  "photo": message.photo,
                  "audio": message.audio,
                  "voice": message.voice
                  }
    for key in media_dict:
        if not media_dict[key]:
            media_id = ""
        elif key == "photo":
            photos = [x.file_id for x in media_dict[key]]
            media_id = str(key + '\t' + photos[0])
            break
        else:
            media_id = str(key + '\t' + media_dict[key].file_id + ';')
            break
    updateTime.data['quote'].append({someone: quote_text.replace('"', '\"')})
    updateTime.data['media_id'].append(media_id)
    forward_saving_timer(message.chat.id)


@bot.message_handler(commands=['kick'])
def kick_user(message):
    if message.reply_to_message:
        bot.kick_chat_member(message.chat.id, message.reply_to_message.from_user.id, until_date=int(message.date) + 1)
        bot.send_message(message.chat.id, "Пользователь изгнан из чата!")
    else:
        bot.reply_to(message, "Функция только для администраторов бота!\nИли вы не указали пользователя для действия")


@bot.message_handler(commands=['save'])
def save_quote(message):
    if message.reply_to_message:
        date = str(datetime.datetime.now().date()).replace('-', '.')
        owner = str(message.from_user.first_name)
        someone = str(message.reply_to_message.from_user.first_name)
        quote_text = str(message.reply_to_message.text)
        media_dict = {"doc": message.reply_to_message.document,
                      "stick": message.reply_to_message.sticker,
                      "photo": message.reply_to_message.photo,
                      "audio": message.reply_to_message.audio,
                      "voice": message.reply_to_message.voice
                      }
        for key in media_dict:
            if not media_dict[key]:
                media_id = ""
            elif key == "photo":
                photos = [x.file_id for x in media_dict[key]]
                media_id = str(key + '\t' + photos[0])
                break
            else:
                media_id = str(key + '\t' + media_dict[key].file_id)
                break
        if message.reply_to_message.document\
                or message.reply_to_message.sticker\
                or message.reply_to_message.photo\
                or message.reply_to_message.audio\
                or message.reply_to_message.voice:
            format_quote = str('<b>[' + someone + ']</b>\n' + '<b>[Media File]</b>' + '\n\n').replace('"', '\"')
        else:
            format_quote = str('<b>[' + someone + ']</b>\n' + quote_text + '\n\n').replace('"', '\"')
        try:
            cursor.execute("INSERT INTO quotes(date, owner, quote, media_id) VALUES(%s, %s, %s, %s)",
                           (date, owner, format_quote, str(media_id)))
            con.commit()
        except AttributeError:
            print("Error while saving quote!")
        else:
            cursor.execute("SELECT max(id) FROM quotes")
            bot.reply_to(message, "Цитата успешно сохранена под <b>№" + str(cursor.fetchall()[0][0]) + "</b>!",
                         parse_mode=MDPARSE)


@bot.message_handler(commands=['quote'])
def show_quote(message, quote_id=None, updated=None, updatemsgid=None):
    msg = message.text
    msg = msg.split(' ')
    if not quote_id and len(msg) != 2:
        print("Error while using command")
    else:
        try:
            if quote_id:
                pass
            else:
                quote_id = int(msg[1])
        except (ValueError, KeyError):
            print("Error while convert ID to INT")
        else:
            if quote_id < 0:
                print("Error because ID < 0")
            else:
                cursor.execute("SELECT * FROM quotes WHERE id=%s", quote_id)
                keys = ['id', 'date', 'owner', 'quote', 'media_id']
                try:
                    db_list = OrderedDict(zip(keys, *cursor.fetchall()))
                except ValueError:
                    bot.send_message(message.chat.id, "Цитата не найдена!")
                else:
                    cursor.execute("SELECT sum(rate) FROM votes WHERE quote_id=%s", quote_id)
                    response = str('Цитата <b>№{id}</b> от <i>{date}</i>  by <b>{owner}</b>:\n\n{quote}'
                                   'Рейтинг цитаты:' + ' <b>[{0}]</b>').format(cursor.fetchall()[0][0], **db_list)
                    keyboard = types.InlineKeyboardMarkup()

                    likebutton = types.InlineKeyboardButton(text="👍🏻",
                                                            callback_data=str("Like{id}".format(**db_list)))
                    dislikebutton = types.InlineKeyboardButton(text="👎🏻",
                                                               callback_data=str("Dislike{id}".format(**db_list)))
                    randomquote = types.InlineKeyboardButton(text="[media]",
                                                             callback_data=str("media{id}".format(**db_list)))

                    keyboard.add(likebutton, randomquote, dislikebutton)
                    if updated == 1:
                        cursor.execute("SELECT * FROM quotes WHERE id=%s", quote_id)
                        keys = ['id', 'date', 'owner', 'quote', 'media_id']
                        db_list = OrderedDict(zip(keys, *cursor.fetchall()))
                        cursor.execute("SELECT sum(rate) FROM votes WHERE quote_id=%s", quote_id)
                        response = str('Цитата <b>№{id}</b> от <i>{date}</i>  by <b>{owner}</b>:\n\n{quote}'
                                       'Рейтинг цитаты:' + ' <b>[{0}]</b>').format(cursor.fetchall()[0][0], **db_list)
                        bot.edit_message_text(chat_id=message.chat.id, message_id=updatemsgid,
                                              text=response, reply_markup=keyboard, parse_mode=MDPARSE)
                    else:
                        bot.send_message(message.chat.id, response, reply_markup=keyboard, parse_mode=MDPARSE)


@bot.message_handler(commands=['delete'])
def delete_quote(message, quote_id=None):
    msg = message.text
    msg = msg.split(' ')
    if not quote_id and len(msg) != 2:
        print("Error while using command")
    else:
        try:
            if quote_id:
                pass
            else:
                quote_id = int(msg[1])
        except (ValueError, KeyError):
            print("Error while convert ID to INT")
        else:
            if quote_id < 0:
                print("Error because ID < 0")
            else:
                cursor.execute("DELETE FROM quotes WHERE id=%s", quote_id)
                con.commit()
                bot.send_message(message.chat.id, str("Цитата №" + str(quote_id) + ", успешно удалена!"))


@bot.callback_query_handler(func=lambda call: True)
def callback_buttons(call):
    if call.message:
        if call.data.startswith("Like"):
            if updateTime.lastmessage == 0 or int(time.time() - updateTime.lastmessage) > VOTING_INTERVAL:
                quote_id = re.search('\d+', call.data).group()
                try:
                    cursor.execute("INSERT INTO votes(quote_id, user_id, rate) VALUES(%s,%s,%s)",
                                   (quote_id, call.from_user.id, 1))
                    bot.answer_callback_query(callback_query_id=call.id, show_alert=False,
                                              text="Вы поставили 👍🏻! Рейтинг цитаты (+1)")
                    con.commit()
                    show_quote(call.message, int(quote_id), 1, call.message.message_id)
                except pymysql.err.IntegrityError:
                    bot.answer_callback_query(callback_query_id=call.id, show_alert=False,
                                              text="Вы уже голосовали за данную цитату!")
                    print("Voted already")
                else:
                    print(updateTime.lastmessage - time.time())
                    updateTime.lastmessage = time.time()
            else:
                bot.answer_callback_query(callback_query_id=call.id, show_alert=False,
                                          text="Подождите несколько секунд, чтобы проголосовать")
        elif call.data.startswith("Dislike"):
            if updateTime.lastmessage == 0 or int(time.time() - updateTime.lastmessage) > VOTING_INTERVAL:
                quote_id = re.search('\d+', call.data).group()
                try:
                    cursor.execute("INSERT INTO votes(quote_id, user_id, rate) VALUES(%s,%s,%s)",
                                   (quote_id, call.from_user.id, -1))
                    bot.answer_callback_query(callback_query_id=call.id, show_alert=False,
                                              text="Вы поставили 👎🏻! Рейтинг цитаты (-1)")
                    con.commit()
                    show_quote(call.message, int(quote_id), 1, call.message.message_id)
                except pymysql.err.IntegrityError:
                    bot.answer_callback_query(callback_query_id=call.id, show_alert=False,
                                              text="Вы уже голосовали за данную цитату!")
                    print("Voted already")
                else:
                    updateTime.lastmessage = time.time()
            else:
                bot.answer_callback_query(callback_query_id=call.id, show_alert=False,
                                          text="Подождите несколько секунд, чтобы проголосовать")
        elif call.data.startswith("media"):
            quote_id = re.search('\d+', call.data).group()
            try:
                cursor.execute("SELECT media_id FROM quotes WHERE id=%s", quote_id)
                media = cursor.fetchall()[0][0].split(';')
                if media == ['']:
                    bot.send_message(call.message.chat.id, str("Медиа файлы из цитаты №" + quote_id + ", отсутствуют!"))
                else:
                    bot.send_message(call.message.chat.id, str("Медиа файлы из цитаты №" + quote_id + "!"))
                for i in media:
                    items = i.split('\t')
                    if items[0] == "stick":
                        bot.send_sticker(call.message.chat.id, items[1])
                    elif items[0] == "doc":
                        bot.send_document(call.message.chat.id, items[1])
                    elif items[0] == "photo":
                        bot.send_photo(call.message.chat.id, items[1])
                    elif items[0] == "audio":
                        bot.send_audio(call.message.chat.id, items[1])
                    elif items[0] == "voice":
                        bot.send_voice(call.message.chat.id, items[1])
            except pymysql.err.IntegrityError:
                print("Error while get Media from quote")

if __name__ == "__main__":
    bot.polling(none_stop=True, timeout=30)
