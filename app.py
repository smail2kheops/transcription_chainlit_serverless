import json
import os

import chainlit as cl
import dotenv
import logfire
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.types import ThreadDict
import storage
from datalayer import DataLayer
import request
DataLayer()

datalayer = SQLAlchemyDataLayer(conninfo=os.environ.get("DATABASE_URL"), ssl_require=True, show_logger=True,
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
    cl.user_session.set('ElementSidebar', cl.ElementSidebar())

async def affichage():
    elements = cl.user_session.get('customElement', None)
    elements.props = cl.user_session.get('props')
    await DataLayer.update_element(elements, cl.user_session.get('id'))
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
        message.content = 'transcription'

    if len(elements) == 0 and content != '':
        return await cl.Message("Veuillez uploader un fichier audio").send()
    if len(elements) > 1:
        return await cl.Message("Veuillez uploader un seul fichier a la fois").send()

    if len(elements) == 1 and elements[0].mime not in ['audio/mpeg', 'audio/aac', 'audio', 'audio/x-m4a', 'audio/wav']:
        print(elements[0].mime)
        return await cl.Message("Veuillez uploader un fichier audio au format MP3, WAV, M4A ou AAC").send()

    if len(elements) == 1:
        print(elements[0].path)
        task_id = request.transcribe(elements[0].path,)
    await cl.Message(content, elements=elements).send()
    print(cl.context.session.thread_id)

# @cl.on_chat_resume
# async def on_chat_resume(thread: ThreadDict):
#     mh = await DataLayer.get_messages(thread['id'])
#     cl.user_session.set("message_history", mh)
#     for step in thread['elements']:
#         if step['type'] == 'custom':
#             res = await DataLayer.get_element(step['threadId'], step['id'])
#             print(step)
#             step['props'] = res['props']
#             if 'feedback' in res['props'].keys():
#                 statistic = await DataLayer.count_response(step['props']['args'])
#                 step['props']['source'] = 'cached'
#                 step['props']['feedback'] = statistic
#                 print(statistic)
#
#     json.dump(thread, open('output.json', 'w', encoding='utf-8'), indent=4)
    # print(json.dumps(thread, indent=4))
