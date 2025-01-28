from pyrogram import Client
from pyrogram.raw.functions.contacts import ResolvePhone, ResolveUsername
from typing import Optional
from fastapi import FastAPI
import uvicorn

app = FastAPI()


async def resolve_username(username: str):
    pyro = Client(
        api_id='26698245',
        api_hash='eff1cbc9369c401acc08d2d887fab7c4',
        name='hranitelitesttools')

    user_id = None
    async with pyro:
        r = await pyro.invoke(ResolveUsername(username=username))
        if r.users:
            user_id = r.users[0].id
    del pyro
    return user_id


async def resolve_phone(phone: str):
    pyro = Client(
        api_id='26698245',
        api_hash='eff1cbc9369c401acc08d2d887fab7c4',
        name='hranitelitesttools')

    user_id = None
    async with pyro:
        r = await pyro.invoke(ResolvePhone(phone=phone))
        if r.users:
            user_id = r.users[0].id
    del pyro
    return user_id


def contains_only_digits(contact: str):
    contact = contact.replace('-', '').replace('+', '').replace('@', '').replace('_', '').replace(' ', '')
    return contact.isdigit()


@app.post('/send_message_by_contact')
async def send_message_by_contact(contact: str, date: str, client_name: Optional[str] = None):
    pyro = Client(
        api_id='26698245',
        api_hash='eff1cbc9369c401acc08d2d887fab7c4',
        name='hranitelitesttools')
    user = await resolve_contact(contact)
    message = f'Здравствуйте{f", {client_name}, у" if client_name else "! У"} вас назначена сессия на {date}. Пожалуйста, если вы планируете на ней быть, подтвердите это в  чат-боте @HraniLiveBot\n\nДля этого в чат-боте надо нажать кнопку “Спасибо, я приду”. Иначе сессия будет отменена, чтобы психолог мог взять других клиентов.'

    async with pyro:
        await pyro.send_message(user['user_id'], message)

    del pyro
    return {'ok': 'ok'}

@app.post('/send_message_by_telegram_id')
async def send_message_by_contact(user_id: str, date: str, client_name: Optional[str] = None):
    pyro = Client(
        api_id='26698245',
        api_hash='eff1cbc9369c401acc08d2d887fab7c4',
        name='hranitelitesttools')

    message = f'Здравствуйте{f", {client_name}, у" if client_name else "! У"} вас назначена сессия на {date}. Пожалуйста, если вы планируете на ней быть, подтвердите это в  чат-боте @HraniLiveBot\n\nДля этого в чат-боте надо нажать кнопку “Спасибо, я приду”. Иначе сессия будет отменена, чтобы психолог мог взять других клиентов.'

    async with pyro:
        await pyro.send_message(user_id, message)

    del pyro
    return {'ok': 'ok'}



async def resolve_contact(contact: str):
    contact = contact.replace('@', '')
    user_id = None
    try:
        if contains_only_digits(contact):
            user_id = await resolve_phone(contact)

        if user_id is None:
            user_id = await resolve_username(contact)

        return {'user_id': user_id}

    except:
        return {'user_id': None}


uvicorn.run(app, host='0.0.0.0', port=8080)
# uvicorn.run(app, port=8080)
