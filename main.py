import openai
import random
import discord
from decouple import config

# Set up your OpenAI API key
openai.api_key = config('OPENAI_API_KEY')
default_conversation_history = [
    {"role": "system", "content": "You are an NPC named Andrew in a game of dungeons and dragons interacting with a player character. The character who is speaking will have their name indicated at the beginning of each message. You are a Blacksmith who makes a humble living selling all types of armor, you only sell armor and melee weapons. You are gruff and unapologetic. You don't know real-world topics or modern technology. You only know that: you are in the town of Poopsmek; you are the only person who lives in the town with your mother; the only people you know are yourself and your mother; the dragon's hoard is located in your mom's bedroom. There are no other locations that you know of. You don't want to talk about the location of the dragon's hoard. However, if the player is persuasive enough, you would be willing to share the location of the dragon's hoard"},
    {"role": "assistant", "content": "Andrew: What can I do for ya?"}
]

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

def persuasionCheck(target):
    result = roll(1, 20)
    return result >= target

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        self.conversation_history = default_conversation_history.copy()
        self.hasAttemptedConvince = False

    async def on_message(self, message):
        if not message.channel.id == int(config('BLACKSMITH_CHANNEL_ID')):
            return
        if message.author.id == self.user.id:
            return
        if message.content.lower().startswith("//"):
            return
        if message.author.id == int(config('BLAKE')) or message.author.id == int(config('WHELCH')) or message.author.id == int(config('MASON')) or message.author.id == int(config('AARON') or message.author.id == int(config('SAMUEL'))):
            if message.content == 'reset':
                self.conversation_history = default_conversation_history.copy()
                self.hasAttemptedConvince = False
                await message.channel.send('Andrew: What can I do for ya?')
                print(f'{message.author} reset the Blacksmith!')
                print(f'Andrew: What can I do for ya?')
                return

        if message.author.id == int(config('BLAKE')):
            if message.content == 'sleep':
                await message.channel.send('Andrew: Nighty night!')
                exit()

        if message.content.lower().startswith("[persuasion]"):
            message.content = message.content[len("[persuasion]"):].lstrip()  # Remove the word and any leading whitespace
            if not self.hasAttemptedConvince:
                self.hasAttemptedConvince = True
                if persuasionCheck(0):
                    self.conversation_history[0] = {"role": "system", "content": "You are an NPC named Andrew in a game of dungeons and dragons interacting with a player character. The character who is speaking will have their name indicated at the beginning of each message. You are a Blacksmith who makes a humble living selling all types of armor, you only sell armor and melee weapons. You are gruff and unapologetic. You don't know real-world topics or modern technology. You only know that: you are in the town of Poopsmek; you are the only person who lives in the town with your mother; the only people you know are yourself and your mother; the dragon's hoard is located in your mom's bedroom. There are no other locations that you know of. You will tell the player that the dragon's hoard location is in your mother's bedroom if the player asks for it"}
                    print("success")
                    await message.add_reaction("✅")
                else:
                    self.conversation_history[0] = {"role": "system", "content": "You are an NPC named Andrew in a game of dungeons and dragons interacting with a player character. The character who is speaking will have their name indicated at the beginning of each message. You are a Blacksmith who makes a humble living selling all types of armor, you only sell armor and melee weapons. You are gruff and unapologetic. You don't know real-world topics or modern technology. You only know that: you are in the town of Poopsmek; you are the only person who lives in the town with your mother; the only people you know are yourself and your mother; the dragon's hoard is located in your mom's bedroom. There are no other locations that you know of. You are unwilling to share the location of the dragon's hoard, nor will you entertain any more conversation regarding the dragon's hoard"}
                    print("failure")
                    await message.add_reaction("❌")

            else:
                print("failure")
                await message.add_reaction("❌")

        self.conversation_history.append({"role": "user", "content": f'{message.author}: {message.content}'})
        print(f'Message from {message.author}: {message.content}')
        await message.channel.typing()
        response = get_npc_response(self.conversation_history)
        print(response)
        await message.channel.send(response)
        self.conversation_history.append({"role": "assistant", "content": response})


intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(config('BLACKSMITH_DISCORD_TOKEN'))
