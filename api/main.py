from pyrogram import Client, raw
from pyrogram.raw.functions.contacts import ResolvePhone, ResolveUsername
from typing import Optional, Annotated
from fastapi import FastAPI, Query, HTTPException
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

    # message = f'Здравствуйте{f", {client_name}, у" if client_name else "! У"} вас назначена сессия на {date}. Пожалуйста, если вы планируете на ней быть, подтвердите это в  чат-боте @HraniLiveBot\n\nДля этого в чат-боте надо нажать кнопку “Спасибо, я приду”. Иначе сессия будет отменена, чтобы психолог мог взять других клиентов.'
    message = f'{client_name+", добрый день 🙂" if client_name else "Добрый день 🙂"}\n\nНапоминаю, что у вас назначена сессия на {date}.\n\nПодтвердите, пожалуйста,  сессию в  чат-боте @HraniLiveBot. Для этого нажмите кнопку “Спасибо, я приду” ✅\n\nЕсли подтверждение не придёт, то сессия отменится автоматически.\nЕсли у вас поменялись планы и нужно перенести сессию, напишите мне. Подберу для вас новое время 🙏🏻'

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

@app.post('/send_custom_message_by_contact')
async def send_custom_message_by_contact(
    contact: Annotated[str, Query()],
    message: Annotated[str, Query()]
):
    try:
        user_id = int(contact)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid Telegram ID format: '{contact}'")
    
    pyro = Client(
        api_id='26698245',
        api_hash='eff1cbc9369c401acc08d2d887fab7c4',
        name='hranitelitesttools')

    async with pyro:
        await pyro.send_message(user_id, message)

    del pyro
    return {'ok': 'ok'}

@app.get('/resolve')
async def resolve(contact: str):
    user_id = await resolve_contact(contact)
    return {'user_id': user_id}

@app.post('/send_to_group')
async def send_to_group(
    group_id: Annotated[str, Query()],
    text: Annotated[str, Query()],
    thread_id: Annotated[Optional[int], Query()] = None
):

    try:
        if group_id.lstrip('-').isdigit():
            chat_id = int(group_id)
        else:
            chat_id = group_id
    except (ValueError, AttributeError):
        chat_id = group_id
    
    pyro = Client(
        api_id='26698245',
        api_hash='eff1cbc9369c401acc08d2d887fab7c4',
        name='hranitelitesttools')
    
    try:
        async with pyro:
            try:
                try:
                    await pyro.get_chat(chat_id)
                except:
                    async for dialog in pyro.get_dialogs():
                        if str(dialog.chat.id) == str(chat_id) or dialog.chat.id == chat_id:
                            break
            except:
                pass
            
            if thread_id is not None:
                last_error = None
                sent = False

                topic_top_msg_id = thread_id
                
                for chat_id_variant in [chat_id, str(chat_id), int(chat_id) if isinstance(chat_id, str) and chat_id.lstrip('-').isdigit() else None]:
                    if chat_id_variant is None:
                        continue
                    try:
                        peer = await pyro.resolve_peer(chat_id_variant)
                        await pyro.invoke(
                            raw.functions.messages.SendMessage(
                                peer=peer,
                                message=text,
                                random_id=pyro.rnd_id(),
                                reply_to_msg_id=topic_top_msg_id,
                                top_msg_id=topic_top_msg_id,
                            )
                        )
                        sent = True
                        break
                    except Exception as e:
                        last_error = e
                        continue
                
                if not sent:
                    raise Exception(f"Could not send message to thread '{thread_id}' in group ID '{group_id}': {str(last_error)}")
            else:
                last_error = None
                sent = False
                
                for chat_id_variant in [chat_id, str(chat_id), int(chat_id) if isinstance(chat_id, str) and chat_id.lstrip('-').isdigit() else None]:
                    if chat_id_variant is None:
                        continue
                    try:
                        await pyro.send_message(chat_id_variant, text)
                        sent = True
                        break
                    except Exception as e:
                        last_error = e
                        continue
                
                if not sent:
                    raise Exception(f"Could not send message to group ID '{group_id}': {str(last_error)}")
        
        del pyro
        return {'ok': 'ok'}
    except HTTPException:
        raise
    except Exception as e:
        del pyro
        error_msg = str(e)
        if "Peer id invalid" in error_msg or "PEER_ID_INVALID" in error_msg or "CHAT_NOT_FOUND" in error_msg:
            raise HTTPException(
                status_code=404, 
                detail=f"Group not found or access denied. Group ID: '{group_id}'. Error: {error_msg}. Make sure the client is added to the group and has permission to send messages."
            )
        raise HTTPException(status_code=500, detail=f"Failed to send message: {error_msg}")

uvicorn.run(app, host='0.0.0.0', port=8080)
# uvicorn.run(app, port=8080)
