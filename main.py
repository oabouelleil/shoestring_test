import discord
from fuzzywuzzy import process
from chatbot import ChatBot

adjusted_noise = False

intents = discord.Intents.default()
intents.typing = True
intents.dm_typing = True
intents.members = True
intents.voice_states = True

client = discord.Client(intents=intents)

user_chat_bots = {}  # Key:Author    Value:DiscordChatBot


class DiscordChatBot(ChatBot):

    def __init__(self, author):
        super().__init__()
        self.user = author

    async def stub_output(self, msg, img_name=None):
        if img_name is None:
            await self.user.send(msg)
        else:
            await self.user.send(file=discord.File("emotions/{}".format(img_name), filename="{}".format(img_name)))

    async def reset(self):
        user_chat_bots[self.user] = DiscordChatBot(self.user)


token = open("token.txt", "r").read()


@client.event
async def on_connect():
    print('We have connected to Discord')


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):  # event that happens per any message.
    if message.author.name == "ShoestringApp":
        return
    print(f"{message.channel}: {message.author}: {message.author.name}: {message.content}")
    # virtual_response("hello")

    restart_commands = ["help", "hello", "restart", "reset"]
    match = process.extractOne(message.content.lower(), restart_commands)
    print("restart match: {}".format(match[1]))
    if match[1] > 60:
        if match[0] == restart_commands[0]:
            await user_chat_bots[message.author].print_help(user_chat_bots[message.author].layer)
            return
        user_chat_bots[message.author] = DiscordChatBot(message.author)
        problems = ', '.join(list(user_chat_bots[message.author].base_layer.keys()))

        await user_chat_bots[message.author].stub_output("", img_name="hello.gif")
        await message.author.send("Hey, do you have any issues I can help you with? I know about {}".format(problems))

        return
    await user_chat_bots[message.author].stub_input(message.content)


@client.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="general")
    await channel.send("Check ur DMs <@{}>".format(member.id))
    await member.send("Welcome to the server, if you need help, just send a message here and we'll "
                      "try our best to solve your issue")
    overwrites = {
        member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member.guild.me: discord.PermissionOverwrite(read_messages=True),
        member: discord.PermissionOverwrite(read_messages=True)
    }
    await member.guild.create_voice_channel(member.name, overwrites=overwrites)
    user_chat_bots[member] = DiscordChatBot(member)

    print(f"{member} joined the {member.guild} server")


@client.event
async def on_member_remove(member):
    voice_channel = discord.utils.get(member.guild.voice_channels, name=member.name)
    await voice_channel.delete(reason="Member Left Server")
    if member.dm_channel is not None:
        dm = member.dm_channel
        async for message in dm.history(limit=300):
            if message.author.name == "ShoestringApp":
                await message.delete()


@client.event
async def on_voice_state_update(member, before, after):
    if after.channel is None:
        for x in client.voice_clients:
            if x.guild == member.guild:
                await x.disconnect()
        for vc in member.guild.voice_channels:
            print(f"Checking {vc}")
            if vc.members and vc.members[0].name != "ShoestringApp":
                print(f"Members in {vc}, will join")
                await discord.utils.get(member.guild.voice_channels, name=vc.name).connect()
                break
    elif not client.voice_clients:
        await after.channel.connect()


client.run(token)
