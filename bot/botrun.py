from ctypes import util
from email import utils
from logging import warning
import discord
from discord.ext import commands,tasks
import os, sqlite3
import string
import youtube_dl
import json
import requests
import asyncio
from logger import logg


TOKEN = "MTAwNjE2OTU0NTk2ODQ1OTg4Ng.Gd2HTu.mvwI368Xpk6ZLnFnuTS4jAwMjWoAPLTNVm4JAs"
bot = commands.Bot(command_prefix=">")

bot.remove_command('help')

@bot.event
async def on_ready():
    print('Я проснулся')
    logg()
    global base, cur
    base = sqlite3.connect('./Bot/BFF.db')
    cur = base.cursor()
    if base:
        print('DataBase connected...OK')

@bot.event
async def on_member_join(member):
    await member.send(f'Привет! Просмотр команд начинается с >info')

    for ch in bot.get_guild(member.guild.id).channels:
        if ch.name == 'основной': # или любой другой, куда мы хотим, чтобы бот обратился
            await bot.get_channel(ch.id).send(f'{member}, я очень рад видеть тебя рядом с нами *(^o^)*')
    logg(head = f'join {member}',
        body = f'join channel') 

@bot.event
async def on_member_remove(member):
    for ch in bot.get_guild(member.guild.id).channels:
        if ch.name == 'основной': # или любой другой, куда мы хотим, чтобы бот обратился
            await bot.get_channel(ch.id).send(f'{member}, нам будет тебя не хватать (;-;)')
    logg(head = f'leave {member}',
        body = f'leave channel') 

@bot.command()
async def hi(ctx): 
    author = ctx.message.author 

    await ctx.send(f'Hello, {author.mention}!')

@bot.command()
async def test(ctx):
    await ctx.send('Я на месте')

@bot.command()
async def info(ctx, arg=None):
    author = ctx.message.author
    if arg ==None:
        await ctx.send(f'{author.mention} Введите: \n>info general\n>info commands')
    elif arg =='general':
        await ctx.send(f'{author.mention} Я слежу за порядком в чате')
    elif arg =='commands':
        await ctx.send(f'{author.mention}  >test - Проверка бота на онлайн\n >status - мои нарушения\n >fox - случайная картинка лисы')
    else:
        await ctx.send(f'{author.mention} Такой команды нет')
    logg(head = f'get info by {ctx.message.guild.name}',
        body = f'get info') 

@bot.command()
async def status(ctx):
    base.execute('CREATE TABLE IF NOT EXISTS {}(userid INT, count INT)'.format(ctx.message.guild.name))
    base.commit()
    warning = cur.execute('SELECT * FROM {} WHERE userid == ?'.format(ctx.message.guild.name)\
        ,(ctx.message.guild.name)).fetchone()
        
    if warning == None:
        await ctx.send(f'{ctx.message.guild.name}, предупреждений нет (*-*)')
    else:
        await ctx.send(f'{ctx.message.guild.name}, {warning[1]} предупреждений! (-_-;)')
    
    logg(head = f'get status by {ctx.message.guild.name}',
        body = f'status warning is {warning}') 
      
@bot.command()
async def fox(ctx):
    author = ctx.author
    response = requests.get('https://some-random-api.ml/img/fox')
    json_data = json.loads(response.text)

    embed = discord.Embed(color = 0xff9900, title = 'Random Fox')
    embed.set_image(url = json_data['link'])
    await ctx.send(embed=embed)
    logg(head = f'get fox by {author}',
        body = f'fox picture') 

@bot.event
async def on_message(message):
    if {i.lower().translate(str.maketrans('','', string.punctuation)) for i in message.content.split(' ')}\
        .intersection(set(json.load(open('./bot/bannwords.json')))) != set():
        await message.channel.send(f'{message.author.mention}, Ай-ай-ай негодяй!')
        await message.delete()
    
        name = message.guild.name

        base.execute('CREATE TABLE IF NOT EXISTS {}(userid INT, count INT)'.format(name))
        base.commit()

        warning = cur.execute('SELECT * FROM {} WHERE userid == ?'.format(name), (message.author.id,)).fetchone()

        if warning == None:
            cur.execute('INSERT INTO {} VALUES (?, ?)'.format(name),(message.author.id,1))
            base.commit()
            await message.channel.send(f'{message.author.mention}, первое предупреждение (o_O)')
        elif warning[1] == 1:
            cur.execute('UPDATE {} SET count == ? WHERE userid == ?'.format(name),(2, message.author.id))
            base.commit()
            await message.channel.send(f'{message.author.mention}, ещё чуть-чуть и будет бан. ОДУМОЙСЯ (O_O)')
        elif warning[2]==2:
            cur.execute('UPDATE {} SET count == ? WHERE userid == ?'.format(name),(3, message.author.id))
            base.commit()
            await message.channel.send(f'{message.author.mention}, ПОЗДРАВЛЯЮ! Ты получаешь бан (X.X)')
            await message.author.ban(reason='Нецензурное выражение')

    await bot.process_commands(message)


server, server_id, name_channel = None, None, None

domains = ['https://www.youtube.com/', 'http://www.youtube.com/', 'https://youtu.be/', 'http://youtu.be/']

async def check_domains(link):
    for x in domains:
        if link.startswith(x):
            return True
    return False

@bot.command()
async def play(ctx, *, command = None):
    global server, server_id, name_channel
    author = ctx.author
    if command == None:
        server = ctx.guild
        name_channel = ctx.author.voice.channel.name
        voice_channel= discord.utils.get(server.voice_channels, name = name_channel)
    params = command.split(' ')
    if len(params) == 1:
        source = params[0]
        server = ctx.guild
        name_channel = author.voice.channel.name
        voice_channel= discord.utils.get(server.voice_channels, name = name_channel)
        print('param 1')
    elif len(params) == 3:
        server_id = params[0]
        voice_id = params[1]
        source = params[2]
        try:
            server_id = int(server_id)
            voice_id = int(voice_id)
        except:
            await ctx.channel.send(f'{author.mention}, id сервера или войса должно быть целочисленным')
            return
        print('param 3')
        server = bot.get_guild(server_id)
        voice_channel = discord.utils.get(server.voice_channels, id=voice_id)
    else:
        await ctx.channel.send(f'{author.mention}, комманда некорректна')
        return
    voice = discord.utils.get(bot.voice_clients, guild = server)
    if voice is None:
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild = server) 
    
    if source == None:
        pass
    elif source.startswith('http'):
        if not await check_domains(source):
            await ctx.channel.send(f'{author.mention}, ссылка не является разрешенной')
            return

        song_there = os.path.isfile('song.mp3')

        try:
            if song_there:
                os.remove('song.mp3')
        except PermissionError:
            await ctx.channel.send('Недостаточно прав')


        ytdl_format_options = {
            'format': 'bestaudio/best',
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec':'mp3',
                    'preferredquality':'192',
                }
            ],
        }   
        
        
        with youtube_dl.YoutubeDL(ytdl_format_options) as ydl:
            ydl.download([source])
            logg(head = f'Add link by {author}',
             body = f'Input data: {source}')   
        for file in os.listdir(f'./'):
            if file.endswith('.mp3'):
                os.rename(file, 'song.mp3')
        voice.play(discord.FFmpegPCMAudio('song.mp3'))
    else:
        voice.play(discord.FFmpegPCMAudio(f'{source}'))
        
@bot.command()
async def pause(ctx):
    author = ctx.author
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.channel.send(f'{ctx.author.mention}, уже на паузе')
    logg(head = f'pause command by {author}',
        body = f'pause song') 
        

@bot.command()
async def resume(ctx):
    author = ctx.author
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice.is_paused():
        voice.resume() 
    else:
        await ctx.channel.send(f'{ctx.author.mention}, уже воспроизводится')
    logg(head = f'resume command by {author}',
        body = f'resume song') 

@bot.command()
async def stop(ctx):
    author = ctx.author
    global server, name_channel
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice.is_connected():
        await voice.disconnect()
    else:
        await ctx.channel.send(f'{ctx.author.mention}, бот уже отключен')
    
    logg(head = f'stop command by {author}',
        body = f'stop song') 

bot.run(TOKEN)
