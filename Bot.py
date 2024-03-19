import discord
from discord.ext import commands, tasks
import asyncio

bot = commands.Bot(command_prefix="!", help_command=None, intents=discord.Intents.all())

unverify_role_id = 1198464485116084345
male_role_id = 1196479484736589835
female_role_id = 1196480882375135295
nedo_role_id = 1198468259230515290
support_role_id = 1198471060547457074
verify_log_channel_id = 1198834645807149126
nedo_log_channel_id = 1198829443653832734
ultimate_role_id = 1198471038510579752
administrator_role_id = 1196481123883175986
odyssy_role_id = 1198479407229182102
nedo_auto_log_channel_id = 1199128914983931994


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')

def create_embed(title=None, description=None, color=None):
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(1162180511289057292)
    role = discord.utils.get(member.guild.roles, id=unverify_role_id)
    await member.add_roles(role)
    
    embed = discord.Embed(
        title="Добро пожаловать!",
        description=f"New member{member.mention}!member ID: {member.id}",
        color=discord.Color.blue()
    )
    await channel.send(embed=embed)


@bot.command(name='verify')
async def verify(ctx, member_id: int):
    allowed_roles = [ultimate_role_id, administrator_role_id, support_role_id, odyssy_role_id]
    if not any(role.id in allowed_roles for role in ctx.author.roles):
        embed = create_embed(
            title="Ошибка",
            description="У вас нет прав использовать эту команду.",
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)

    member = ctx.guild.get_member(member_id)

    if member is None:
        embed = create_embed(
            title="Ошибка",
            description="Участник не найден.",
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)

    unverify_role = discord.utils.get(ctx.guild.roles, id=unverify_role_id)
    await member.remove_roles(unverify_role)

    await ctx.send(embed=create_embed(
        title="Выбор роли",
        description=f"{ctx.author.mention}, выберите роль для участника {member.mention}: `male`, `female` или `nedo`. Если выбрана роль `nedo`, укажите длительность в секундах.",
        color=discord.Color.blue()
    ))

    try:
        response = await bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60)
    except asyncio.TimeoutError:
        return await ctx.send(embed=create_embed(
            title="Ошибка",
            description="Время на выбор роли и длительности истекло.",
            color=discord.Color.red()
        ))

    role_id = None
    duration = None
    choices = response.content.lower().split()
    
    if len(choices) < 1 or choices[0] not in ["male", "female", "nedo"]:
        return await ctx.send(embed=create_embed(
            title="Ошибка",
            description="Неверный выбор роли. Пожалуйста, введите `male`, `female` или `nedo`.",
            color=discord.Color.red()
        ))
    
    role_id = nedo_role_id if choices[0] == "nedo" else (male_role_id if choices[0] == "male" else female_role_id)
    
    if role_id == nedo_role_id and len(choices) == 2 and choices[1].isdigit():
        duration = int(choices[1])

    role = discord.utils.get(ctx.guild.roles, id=role_id)

    await member.add_roles(role)
    await ctx.send(embed=create_embed(
        title="Верификация завершена",
        description=f"{member.mention}, вы были верифицированы с ролью {role.name}.",
        color=discord.Color.green()
    ))

    if role_id == nedo_role_id:
        log_channel = bot.get_channel(nedo_log_channel_id)
        await log_channel.send(embed=create_embed(
            title="НЕДОПУСК выдан",
            description=f"{ctx.author.name}#{ctx.author.discriminator} выдал НЕДОПУСК участнику {member.name}#{member.discriminator} на {duration} секунд.",
            color=discord.Color.green()
        ))
        remove_nedo_role.start(ctx.guild.id, member.id, duration, nedo_auto_log_channel_id) if duration else None
    else:
        log_channel = bot.get_channel(verify_log_channel_id)
        await log_channel.send(embed=create_embed(
            title="Верификация",
            description=f"{ctx.author.name}#{ctx.author.discriminator} верифицировал участника {member.name}#{member.discriminator} с ролью {role.name}.",
            color=discord.Color.green()
        ))

@tasks.loop(seconds=1)
async def remove_nedo_role(guild_id, member_id, duration, log_channel_id):
    guild = bot.get_guild(guild_id)
    member = guild.get_member(member_id)
    nedo_role = discord.utils.get(guild.roles, id=nedo_role_id)
    unverify_role = discord.utils.get(guild.roles, id=unverify_role_id)
    log_channel = bot.get_channel(log_channel_id)

    if member and nedo_role in member.roles:
        await asyncio.sleep(duration)
        await member.remove_roles(nedo_role)
        await member.add_roles(unverify_role)

        embed = discord.Embed(
            title="НЕДОПУСК снят",
            description=f"Убран НЕДОПУСК с {member.name}#{member.discriminator} и добавлена роль Unverify",
            color=discord.Color.green()
        )
        await log_channel.send(embed=embed)
        
        
#Help code
@bot.command(name='help')
async def help_command(ctx):
    embed = discord.Embed(
        description="List of available commands:",
        color=discord.Color.blue()
    )
    embed.add_field(name="!ping", value="Check if the bot is working", inline=False)
    embed.add_field(name="!userinfo [@mention]", value="Get information about a user", inline=False)
    embed.add_field(name="!kick [@mention]", value="Kick a user from the server", inline=False)
    await ctx.send(embed=embed)
    
@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Pong! Latency is {0}'.format(round(bot.latency * 1000)))

@bot.command(name='userinfo')
async def userinfo(ctx, member: discord.Member):
    embed = discord.Embed(title="User Info", description=member.mention, color=member.color)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d"), inline=False)
    embed.add_field(name="Joined Discord", value=member.created_at.strftime("%Y-%m-%d"), inline=False)
    await ctx.send(embed=embed)

# Function to count the number of members in a channel
def count_members_in_channel(channel):
    return len(channel.members)

# Function to count the number of messages sent within a specific timeframe
def count_messages_in_timeframe(messages, timeframe):
    count = 0
    for message in messages:
        if message.created_at >= timeframe:
            count += 1
    return count

# Example usage
@bot.command(name='members_day')
async def members_day(ctx):
    channel = ctx.channel
    member_count = count_members_in_channel(channel)
    await ctx.send(f"Number of members in the channel: {member_count}")

@bot.command(name='messages_day')
async def messages_day(ctx):
    messages = await ctx.channel.history(limit=None).flatten()
    day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
    message_count = count_messages_in_timeframe(messages, day_ago)
    await ctx.send(f"Number of messages in the last day: {message_count}")

@bot.command(name='code')
async def code_command(ctx, command_name):
    if command_name == 'help':
        await ctx.send("Here is the code for the help command: `@bot.command(name='help') async def help_command(ctx): ...`")
    elif command_name == 'ping':
        await ctx.send("Here is the code for the ping command: `@bot.command(name='ping') async def ping_command(ctx): ...`")
    else:
        await ctx.send("Command not found.")
        
#Economy code

user_balances = {}

@bot.command(name='balance')
async def balance(ctx):
    user = ctx.author
    user_id = str(user.id)
    if user_id not in user_balances:
        user_balances[user_id] = 100
    await ctx.send(f'Your balance is: {user_balances[user_id]} coins')

@bot.command(name='work')
async def work(ctx):
    user = ctx.author
    user_id = str(user.id)
    if user_id not in user_balances:
        user_balances[user_id] = 100
    earnings = 50
    user_balances[user_id] += earnings
    await ctx.send(f'You earned {earnings} coins from work!')

@bot.command(name='gamble')
async def gamble(ctx, amount: int):
    user = ctx.author
    user_id = str(user.id)
    if user_id not in user_balances:
        user_balances[user_id] = 100
    if amount > user_balances[user_id]:
        await ctx.send("You don't have enough coins to gamble that amount!")
        return
    # Implement gamble logic and update user_balances accordingly
    await ctx.send("Gambling logic goes here!")

        
bot.run("")
