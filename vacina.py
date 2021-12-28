import secrets
from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler
from telegram.ext import MessageHandler, Filters
from bs4 import BeautifulSoup
import logging
import requests
import re


running = False
ages_per_type = {
    'regular': -1,
    'janssen': -1,
    'children': -1
}


updater = Updater(token=secrets.TOKEN,
                  use_context=True)
dispatcher = updater.dispatcher
job_queue = updater.job_queue


def get_ages():
    page = requests.get("https://covid19.min-saude.pt/pedido-de-agendamento/")
    if page.status_code == 200:
        soup = BeautifulSoup(page.content, 'html.parser')
        age_indicator = soup.find(id="pedido_content")
        elems = age_indicator.h4.find_all("strong")
        ages = []
        for elem in elems:
            ages.append(int(re.sub("^[^0-9]+", "", elem.string).split()[0]))
        result = {
            'regular': ages[0],
            'janssen': ages[1],
            'children': ages[2]
        }

        return result
    else:
        return ages_per_type


def make_msg():
    msg = "Idades atuais para o autoagendamento da vacina contra a COVID-19:" \
        "\n\n" \
        "- Reforço geral: %d anos ou mais\n" \
        "- Reforço para Janssen: %d anos ou mais\n" \
        "- Crianças: dos %d aos 11 anos\n\n" \
        "Realizar o autoagendamento em: " \
        "https://covid19.min-saude.pt/pedido-de-agendamento/" \
        % (ages_per_type['regular'],
           ages_per_type['janssen'],
           ages_per_type['children'])

    return msg


def run_loop(context: CallbackContext):
    global ages_per_type
    ages = get_ages()
    if ages != ages_per_type:
        ages_per_type = ages
        msg = make_msg()
        context.bot.send_message(chat_id='@vacinas_c19', text=msg)


def start(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id='@vacinas_c19',
        text="Bem-vindo, verifique aqui a(s) idade(s) do "
        "autoagendamento para a vacina contra a COVID-19.\n\n"
        "Source code: https://github.com/rppc/vacina_bot.git"
    )
    global running
    if not running:
        running = True,
        job_queue.run_repeating(run_loop, interval=60, first=1)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Olá! Pergunte-me pelas idades para o "
        "autoagendamento da vacina contra a COVID-19"
    )


def check(update: Update, context: CallbackContext):
    msg = make_msg()
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)


def unknown(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Comando não reconhecido")


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    check_handler = CommandHandler('check', check)
    dispatcher.add_handler(check_handler)

    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
