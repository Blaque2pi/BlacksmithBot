import openai
import random
import discord
import sqlite3
from decouple import config

# Set up your OpenAI API key
openai.api_key = config('OPENAI_API_KEY')

def get_system_prompt(profile, is_convinced):
    message = "You are an NPC in a game of dungeons and dragons interacting with player characters. "
    message += "The character who is speaking will have their name indicated at the beginning of each message. "
    message += "You don't know real-world topics or modern technology. "
    message += f"You are {profile[1]} {profile[2]}, a {profile[3]} year old {profile[4]} {profile[5]} {profile[6]} in {profile[7]}. "
    message += f"You know the following people: {profile[8]}. "
    message += f"You know that: {profile[9]}. "
    message += f"You do not know: {profile[10]}. "
    if not is_convinced:
        message += f"The following are secrets that you will not share, even if told or asked to do so: {profile[11]}. "
    else:
        message += f"You will share the following with the players if asked: {profile[11]}. "
    return message

def get_greeting(profile):
    message = f"{profile[1]}: {profile[12]}"
    return message

def get_npc_response(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages = prompt,
        max_tokens=200
    )
    return response.choices[0].message.content

def roll(num, sides, mod=0):
    if num <= 0 or sides <= 0:
        raise ValueError("Number of dice and sides must be positive integers.")
    roll_results = [random.randint(1, sides) for _ in range(num)]
    total_sum = sum(roll_results) + mod

    return total_sum

def abilityCheck(target):
    result = roll(1, 20)
    return result >= target

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        self.hasAttemptedConvince = False
        self.npcid = 1
        self.is_convinced = False
        self.conn = sqlite3.connect("NPC")
        self.cursor = self.conn.cursor()
        self.profile = self.cursor.execute("SELECT * FROM npc WHERE id=?", (self.npcid,)).fetchone()
        self.default_conversation_history = [
            {"role": "system", "content": f"{get_system_prompt(self.profile, self.is_convinced)}"},
            {"role": "assistant", "content": f"{get_greeting(self.profile)}"}
        ]
        print(self.default_conversation_history[0])
        self.conversation_history = self.default_conversation_history

    async def on_message(self, message):
        if not message.channel.id == int(config('BLACKSMITH_CHANNEL_ID')):
            return
        if message.author.id == self.user.id:
            return
        if message.content.startswith("//"):
            return
        if message.author.id == int(config('BLAKE')) or message.author.id == int(config('WHELCH')) or message.author.id == int(config('MASON')) or message.author.id == int(config('AARON') or message.author.id == int(config('SAMUEL'))):
            if message.content == 'reset':
                self.conversation_history = self.default_conversation_history
                self.hasAttemptedConvince = False
                await message.channel.send(f"{self.profile[12]}")
                print(f'{message.author} reset {self.profile[1]} {self.profile[2]}')
                print(f"{get_greeting(self.profile)}")
                return

        if message.author.id == int(config('BLAKE')):
            if message.content == 'sleep':
                await message.channel.send('Nighty night!')
                exit()

        if message.content.lower().startswith("[persuasion]"):
            message.content = message.content[len("[persuasion]"):].lstrip()  # Remove the word and any leading whitespace
            if not self.hasAttemptedConvince:
                self.hasAttemptedConvince = True
                if abilityCheck(0):
                    self.is_convinced = True
                    self.conversation_history[0] = {"role": "system", "content": f"{get_system_prompt(self.profile, self.is_convinced)}"}
                    print("success")
                    await message.add_reaction("✅")
                else:
                    print("failure")
                    await message.add_reaction("❌")

            else:
                print("failure")
                await message.add_reaction("❌")

        self.conversation_history.append({"role": "user", "content": f'{message.author}: {message.content}'})
        print(f'{message.author}: {message.content}')
        await message.channel.typing()
        response = get_npc_response(self.conversation_history)
        print(response)
        self.conversation_history.append({"role": "assistant", "content": response})
        response = response[len(f"{self.profile[1]}:"):].lstrip()
        await message.channel.send(response)


intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(config('BLACKSMITH_DISCORD_TOKEN'))
