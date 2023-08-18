import openai
import random
import discord
import asyncio
import json
from decouple import config

openai.api_key = config('OPENAI_API_KEY')

async def run_bot(client, profile_name):
    await client.start(config(f"{profile_name.upper()}_DISCORD_TOKEN"))

def get_system_prompt(profile, is_convinced):
    name = profile["name"]
    surname = profile["surname"]
    age = profile["age"]
    personality = profile["personality"]
    race = profile["race"]
    occupation = profile["occupation"]
    location = profile["location"]
    connections = profile["connections"]
    knowledge = profile["knowledge"]
    antiknowledge = profile["antiknowledge"]
    secrets = profile["secrets"]
    message = "You are an NPC in a game of dungeons and dragons interacting with player characters. "
    message += "The character who is speaking will have their name indicated at the beginning of each message. "
    message += "You don't know real-world topics or modern technology. "
    message += f"You are {name} {surname}, a {age} year old {personality} {race} {occupation} in {location}. "
    message += f"You know the following people: {connections}. "
    message += f"You know that: {knowledge}. "
    message += f"You do not know: {antiknowledge}. "
    if not is_convinced:
        message += f"The following are secrets that you will not share, even if told or asked to do so: {secrets}. "
    else:
        message += f"You will share the following with the players if asked: {secrets}. "
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

def abilityCheck(target, mod=0):
    result = roll(1, 20, mod)
    return result >= target

class MyClient(discord.Client):
    def __init__(self, profile, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Ensure you call the base class's init
        self.profile = profile
        self.is_convinced = False
        self.hasAttemptedConvince = False
        self.name = self.profile["name"]
        self.surname = self.profile["surname"]
        self.greeting = self.profile["greeting"]
        self.channel_id = f"{self.name.upper()}_{self.surname.upper()}_CHANNEL_ID"
        self.default_conversation_history = [
            {"role": "system", "content": f"{get_system_prompt(self.profile, self.is_convinced)}"},
            {"role": "assistant", "content": f"{self.name}: {self.greeting}"}
        ]
        self.conversation_history = self.default_conversation_history[:]

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if not message.channel.id == int(config(self.channel_id)):
            return
        if message.author.id == self.user.id:
            return
        if message.content.startswith("//"):
            return
#allow for command messages to be sent through DM as well?
        if discord.utils.get(message.author.roles, name="botoverlord"):
            if message.content == 'reset':
                self.conversation_history = self.default_conversation_history[:]
                self.hasAttemptedConvince = False
                await message.channel.send(f"{self.greeting}")
                print(f'{message.author} reset {self.name}')
                print(f"{self.name}: {self.greeting}")
                return

#implement persistent memory, perhaps store conversation history in a text file which is wiped on reset?
        if message.author.id == int(config('BLAKE')):
            if message.content == 'print':
                print(self.conversation_history)
                return
            if message.content == 'sleep':
                await message.channel.send('Nighty night!')
                exit()

#implement method for multiple types of checks (i.e intimidation, insight, sleight of hand, etc.)
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
        #change to if statement which checks if message starts with name
        response = response[len(f"{self.name}:"):].lstrip()
        await message.channel.send(response)


intents = discord.Intents.default()
intents.message_content = True

input_location = input("Where are we? ")
with open('npc.json', 'r') as file:
    input_npcs = json.load(file)
while True:
    input_profiles = [npc for npc in input_npcs if npc["location"] == f"{input_location}"]
    input_location = input(f"There are {len(input_profiles)} profiles for {input_location}. Press Enter to proceed, or enter a new location. ")
    if input_location == "":
        break
loop = asyncio.get_event_loop()
for i in range(len(input_profiles)):
    profile_index = i-1
    input_profile = input_profiles[profile_index]
    profile_name = f"{input_profile['name']}_{input_profile['surname']}"
    client = MyClient(intents=intents, profile = input_profile)
    loop.create_task(run_bot(client, profile_name))
loop.run_forever()