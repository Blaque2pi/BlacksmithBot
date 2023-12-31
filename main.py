import openai
import random
import discord
import asyncio
import json
from decouple import config

openai.api_key = config('OPENAI_API_KEY')

async def run_bot(client, bot_num):
    await client.start(config(f"NPC{bot_num}_DISCORD_TOKEN"))

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

def get_new_profiles(location, number):
    message = ""
    message += f"I want you to generate {number} profiles for NPCs in dungeons and dragons. "
    message += f"They all live in a town/city named {location}. "
    message += "You will output the following traits for each profile, each trait containing one string of information and each trait name being in lower case type: "
    message += "name, "
    message += "surname, "
    message += "greeting (this will be a piece of dialogue that this character will say at the start of the conversation with a player), "
    message += "age, "
    message += "personality, "
    message += "race, "
    message += "occupation, "
    message += "location (this should just be the town/city name, "
    message += "connections (this will describe the relationships this character has with other generated NPCs in the town), "
    message += "knowledge (this will include rumors that this character has heard or interesting things that the character will want to talk about), "
    message += "antiknowledge (this will detail specific information that this character does not know), "
    message += "secrets (these are things that this character is keeping secret from the players, but can be persuaded to share if they succeed their skill checks). "
    message += "Only respond with a single keyless json code object, each individual profile in that object should also be keyless. It should also be recognized as a list rather than a dictionary in python."
    prompt = [
        {"role": "system", "content": f"You are an AI helper for a dungeon master in the game of Dungeons and Dragons"},
        {"role": "user", "content": f"{message}"}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt,
        max_tokens=1500
    )
    print(response)
    response_content = response.choices[0].message.content
    print(response_content)
    code_str = ""
    if "\n[" in response_content:
        code_start = response_content.find("[")
        code_end = response_content.find("]", code_start)
        code_str = response_content[code_start:code_end].strip()
        print(code_str)
    if response_content.startswith("["):
        code_str = response_content
        print(code_str)
    code_json = json.loads(code_str)
    return code_json

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
    def __init__(self, profile, bot_num, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Ensure you call the base class's init
        self.bot_num = bot_num
        self.profile = profile
        self.is_convinced = False
        self.hasAttemptedConvince = False
        self.name = self.profile["name"]
        self.surname = self.profile["surname"]
        self.full_name = f"{self.name} {self.surname}"
        self.greeting = self.profile["greeting"]
        self.location = self.profile["location"]
        self.channel_name = f"{self.name.lower()}-{self.surname.lower()}"
        self.channel_id = f"{self.name.upper()}_{self.surname.upper()}_CHANNEL_ID"
        self.default_conversation_history = [
            {"role": "system", "content": f"{get_system_prompt(self.profile, self.is_convinced)}"},
            {"role": "assistant", "content": f"{self.name}: {self.greeting}"}
        ]
        self.conversation_history = self.default_conversation_history[:]

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        if not self.user.name == self.full_name:
            await self.user.edit(username=f"{self.full_name}")
            print(f"Bot's name changed to {self.full_name}!")
        guild = self.guilds[0]
        found_category = discord.utils.get(guild.categories, name=self.location)
        found_channel = discord.utils.get(guild.text_channels, name=self.channel_name)
        if not found_category:
            print(f'Catergory "{self.location}" not found, creating... ')
            await guild.create_category(self.location)
            print(f'Category "{self.location}" created!')
        if found_channel:
            print(f'Found channel {self.channel_name}!')
        else:
            print(f'Text channel "{self.channel_name}" not found, creating... ')
            category = discord.utils.get(guild.categories, name=self.location)
            await guild.create_text_channel(self.channel_name, category=category)
            print(f'Text channel "{self.channel_name}" created in {self.location}!')
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            await channel.send(f"{self.greeting}")

    async def on_message(self, message):
        if not message.channel.name == self.channel_name:
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
intents.guilds = True

input_location = input("Where are we? ").capitalize()
with open('npc.json', 'r') as file:
    input_npcs = json.load(file)
while True:
    with open('npc.json', 'r') as file:
        input_npcs = json.load(file)
    input_profiles = [npc for npc in input_npcs if npc["location"] == f"{input_location}"]
    if len(input_profiles) > 0:
        input_location_okay = input(f"There are {len(input_profiles)} profiles for {input_location}. Press Enter to proceed, or enter a new location. ")
        if input_location_okay == "":
            print("Generating NPCs... ")
            break
    else:
        new_location_okay = input(f"There are no profiles for {input_location}. Press Enter to generate profiles, or enter a new location. ")
        if new_location_okay == "":
            while True:
                new_profiles_number = input(f"Please enter a number of new profiles to generate for {input_location} (Maximum 5), or enter a new location. ")
                if 1 <= int(new_profiles_number) <= 5:
                    new_profiles = get_new_profiles(input_location, new_profiles_number)
                    print("new profiles loaded")
                    input_npcs.extend(new_profiles)
                    with open("npc.json", "w") as file:
                        json.dump(input_npcs, file, indent=4)
                    break
                else:
                    input_location = new_profiles_number
                    break

print("success!")
loop = asyncio.get_event_loop()
for i in range(len(input_profiles)):
    profile_index = i
    input_profile = input_profiles[profile_index]
    bot_num = i+1
    print(bot_num)
    client = MyClient(intents=intents, profile=input_profile, bot_num=bot_num)
    loop.create_task(run_bot(client, bot_num))
loop.run_forever()