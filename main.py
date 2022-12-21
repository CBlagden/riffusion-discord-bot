import json
import requests
import base64
import dataclasses
import time
import aiohttp
import logging
from typing import Optional
import numpy as np

from datatypes import *

import discord
from discord import app_commands
from discord import voice_client

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

config = json.load(open('config.json', 'r'))
token = config['token']
url = config['url']
guild = discord.Object(id=config['guild'])

class MyClient(discord.Client):

    async def on_ready(self):
        await tree.sync(guild=guild)
        print(f'Logged on as {self.user}!')

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(guild=guild)
async def listen(interaction: discord.Interaction,
                 prompt: str,
                 end_prompt: Optional[str],
                 seed_image: Optional[str]="og_beat",
                 num_outputs: int=3):
    await interaction.response.defer()
    print("Generating audio...")

    name = prompt.replace(" ", "_")

    if end_prompt is None:
        end_prompt = prompt
    else:
        name = name + '_' + end_prompt.replace(" ", "_")

    filename = f'outputs/{name}.mp3'
    fp = open(filename, 'ab')
    fp.seek(0)
    fp.truncate()

    start_seed = int(time.time())
    end_seed = start_seed + 1
    alphas = np.linspace(0, 1, num=num_outputs)


    vc_channel = interaction.user.voice.channel
    vc_conn = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if vc_conn is None or not vc_conn.is_connected():
        vc_conn = await vc_channel.connect()

    def repeat(vc_conn, audio_queue):
       if len(audio_queue) == 0:
           print("Queue is empty...")
           return None

       fp = open('outputs/tmp.mp3', 'wb')
       while len(audio_queue) > 0:
           audio = audio_queue.pop(0)
           fp.write(audio)
       fp.close()

       print("Playing clip...")
       vc_conn.play(discord.FFmpegPCMAudio('outputs/tmp.mp3'),
                       after=lambda e: repeat(vc_conn, audio_queue))

    audio_queue = []
    for i, alpha in enumerate(alphas):
        input = InferenceInput(
            start=PromptInput(
                prompt=prompt,
                seed=start_seed
            ),
            end=PromptInput(
                prompt=end_prompt,
                seed=end_seed
            ),
            alpha=alpha,
            seed_image_id=seed_image
        )
        resp = requests.post(url, json=dataclasses.asdict(input))
        audio = base64.b64decode(resp.json()['audio'])
        fp.write(audio)
        audio_queue.append(audio)

        if i == 0:
            repeat(vc_conn, audio_queue)

    fp.close()
    await interaction.followup.send(file=discord.File(filename))


client.run(token, log_handler=handler, log_level=logging.INFO)
