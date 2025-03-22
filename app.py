import json
import os

import chainlit as cl
import dotenv
import logfire
import storage
from datalayer import DataLayer
import request
import db

datalayer = DataLayer(conninfo=os.environ.get("DATABASE_URL"), ssl_require=True, show_logger=True,
                      storage_provider=storage.storage)


@cl.data_layer
def get_data_layer():
    return datalayer


@cl.password_auth_callback
async def auth_callback(username: str, password: str):
    if username == 'admin' and password == 'kheopadmin':
        return cl.User(
            identifier="admin", metadata={"role": "admin", "provider": "credentials"}
        )
    return cl.User(
        identifier="metropole2", metadata={"role": "admin", "provider": "credentials"}
    )


dotenv.load_dotenv()
logfire.configure()

model = 'gpt-4o-mini'


@cl.set_starters
async def set_starters():
    questions = [
    ]

    return [
        cl.Starter(
            label=value,
            message=value
        ) for value in questions
    ]


@cl.on_chat_start
async def on_start():
    return
    # element = cl.CustomElement(name='Loader')
    # await cl.Message('', elements=[element]).send()
    #
    # cl.user_session.set('ElementSidebar', cl.ElementSidebar())


async def affichage():
    elements = cl.user_session.get('customElement', None)
    elements.props = cl.user_session.get('props')
    await datalayer.update_element(elements, cl.user_session.get('id'))
    user_id = await get_data_layer()._get_user_id_by_thread(elements.thread_id)
    file_object_key = f"{user_id}/{elements.id}/Source"
    print(file_object_key)

    await elements.update()
    # upload_source(file_object_key, json.dumps(elements.props))
    return


@cl.on_message
async def main(message):
    elements = message.elements
    content = message.content
    if content == '':
        content = await datalayer.get_current_timestamp()
        await cl.context.emitter.emit("first_interaction",
                                {
                                    "interaction": content,
                                    "thread_id": cl.context.session.thread_id,
                                })
        message.content = 'transcription'
        await message.update()

    if len(elements) == 0 and content != '':
        return await cl.Message("Veuillez uploader un fichier audio").send()
    if len(elements) > 1:
        return await cl.Message("Veuillez uploader un seul fichier a la fois").send()

    if len(elements) == 1 and elements[0].mime not in ['audio/mpeg', 'audio/aac', 'audio', 'audio/x-m4a', 'audio/wav']:
        print(elements[0].mime)
        return await cl.Message("Veuillez uploader un fichier audio au format MP3, WAV, M4A ou AAC").send()

    if len(elements) == 1:
        print(elements[0].path)
        response = request.transcribe(elements[0].path, )
        await datalayer.update_tasks(cl.context.session.thread_id, response['task_id'])
        element = cl.CustomElement(name='Loader', props = {'name':'transcription',
                                                           'status':'RUNNING',
                                                           'filename':elements[0].name,})
        await cl.Message('', elements=[element]).send()

@cl.on_chat_resume
async def on_chat_resume(thread):
    # mh = await datalayer.get_messages(thread['id'])
    # cl.user_session.set("message_history", mh)
    for step in thread['elements']:
        if step['type'] == 'custom':
            element = await datalayer.get_element(step['threadId'], step['id'])
            if element['props'].get('name') == 'transcription':
                taks_id = await datalayer.get_task(step['threadId'])
                res = await request.check(taks_id)
                step['props']['status'] = res['status']
                step['props']['task_id'] = taks_id
                step['props']['filename'] = element['props']['filename']
                cl.user_session.set('last_conv',{'id':taks_id,
                                                 'status':res['status'],
                                                 'step_id':step['id'],
                                                 'name':element['props']['filename'],})

    last_conv = cl.user_session.get('last_conv', None)
    if last_conv is not None:
        print(last_conv)
        if last_conv['status'] == 'COMPLETE':
            transcription = db.get(last_conv['id'])
            print(transcription)
        elif thread['elements'][-1]['id'] != last_conv['step_id']:
            element = cl.CustomElement(name='Loader', props={'name': 'transcription',
                                                             'status': 'RUNNING',
                                                             'filename':last_conv['name']})
            await cl.Message('', elements=[element]).send()

