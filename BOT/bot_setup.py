# bot_setup.py
import telebot
from telebot import types
from ServiceAndrey import Part_Andrey

def create_bot():
    bot = telebot.TeleBot('7795186444:AAE-M2N6ywh9PmjUwAzz-A6h39Rc9fvDzj0')
    bot.delete_webhook()
    return bot