import json
import requests
import base64
import dataclasses
import time
from typing import Optional
import numpy as np

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
                 alpha: Optional[float]=None,
                 seed_image: Optional[str]="og_beat",
                 num_outputs: Optional[int]=3):
    await interaction.response.defer()

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
    if num_outputs is not None:
        if alpha is not None:
            alphas = num_outputs * [alpha]
        else:
            alphas = np.linspace(0, 1, num=num_outputs)
    else:
        alphas = [alpha]

    for alpha in alphas:
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
            num_inference_steps=num_inference_steps,
            seed_image_id=seed_image
        )
        resp = requests.post(url, json=dataclasses.asdict(input))
        audio = base64.b64decode(resp.json()['audio'])

        fp.write(audio)

    await interaction.followup.send(file=discord.File(filename))


@tree.command(guild=guild)
async def help(interaction: discord.Interaction):
    await interaction.message.reply("
    *Basic Commands:*
    ")


client.run(token)
