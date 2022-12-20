import json
import requests
import base64
import dataclasses
import time
from typing import Optional

from datatypes import *

import discord
from discord import app_commands

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
                 num_inference_steps: Optional[int]=50,
                 alpha: Optional[float]=0.75,
                 seed_image: Optional[str]="og_beat"):
    await interaction.response.defer()

    name = prompt.replace(" ", "_")

    if end_prompt is None:
        end_prompt = prompt
    else:
        name = name + end_prompt.replace(" ", "_")
    input = InferenceInput(
        start=PromptInput(
            prompt=prompt,
            seed=int(time.time())
        ),
        end=PromptInput(
            prompt=end_prompt,
            seed=int(time.time()) + 1),
        alpha=alpha,
        num_inference_steps=num_inference_steps,
        seed_image_id=seed_image
    )
    resp = requests.post(url, json=dataclasses.asdict(input))
    audio = base64.b64decode(resp.json()['audio'])

    filename = f'outputs/{name}.mp3'
    with open(filename, 'wb') as f:
        f.write(audio)

    await interaction.followup.send(file=discord.File(filename))

client.run(token)