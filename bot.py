import discord, ast, random, time, itertools

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

cards_per_hand = 7
min_players = 3

f_b = open('blackcards.txt','r')
default_b = f_b.readlines()
f_b.close()

#default_b = []

f_w = open('whitecards.txt','r')
default_w = f_w.readlines()
f_w.close()

def quickwrite(path, content):
    f = open(path,'w')
    f.write(content)
    f.close()

def quickread(path):
    try:
        f = open(path,'r')
        content = f.read()
        f.close()
    except:
        content = ""
    return content

def applyCustomDecks(game):
    host = ast.literal_eval(quickread('users/'+str(game['host'])))
    deck_w = list(itertools.chain(default_w, *[host['custom_decks'][i]['cards_w'] for i in game['custom_decks']]))
    deck_b = list(itertools.chain(default_b, *[host['custom_decks'][i]['cards_b'] for i in game['custom_decks']]))
    return [deck_w, deck_b]

def createDataIfNecessary(user):
    try:
        dummy = open('users/'+str(user.id),'r')
        dummy.close()
    except:
        f_user = open('users/'+str(user.id),'w')
        f_user.write(str(user_template))
        f_user.close()

game_template = {
    'host':0,
    'czar':0,
    'card':0,
    'pick_no':1,
    'pile':[],
    'discard_w':[],
    'discard_b':[],
    'last_active':0,
    'players':{},
    'custom_decks':[]
    }

user_template = {
    "custom_decks": [],
    "wins":0
    }
    

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.id in ast.literal_eval(quickread('sessions')):
        games = ast.literal_eval(quickread('sessions'))
        game = games[message.channel.id]
        if message.author.id == [i for i in game['players']][game['czar']] and len(game['pile']) >= len(game['players'])-1 and len(game['players']) > 1 and message.clean_content.isdigit():
            selection = int(message.clean_content)
            if selection <= len(game['pile']) and selection > 0:
                game['last_active'] = time.time()
                decks = applyCustomDecks(game)
                winner = await client.fetch_user(game['pile'][selection-1]['played_by'])
                game['players'][winner.id]['score'] += 1
                await message.channel.send(winner.mention + " got the point! (Total score: " + str(game['players'][winner.id]['score']) + ")")
                if game['players'][winner.id]['score'] >= 7:
                    await message.channel.send(winner.mention + " **wins the game!**")
                    games.pop(message.channel.id)
                else:
                    game['pile'] = []
                    if game['czar']+1 < len(game['players']):
                        game['czar'] += 1
                    else:
                        game['czar'] = 0
                    newczar = await client.fetch_user([i for i in game['players']][game['czar']])
                    game['discard_b'].append(game['card'])
                    game['card'] = random.choice([i for i in range(len(decks[1])) if not i in game['discard_b']])
                    await message.channel.send(newczar.mention + " is the new Czar.\nThe black card is: \N{BLACK LARGE SQUARE} **" + decks[1][game['card']].strip('\n') + "**")
                    for i in game['players']:
                        game['players'][i]['played'] = 0
                        user = await client.fetch_user(i)
                        usrhand = game['players'][user.id]['hand']
                        if i == newczar.id:
                            continue
                        embed = discord.Embed(
                                title="Cards Against Humanity",
                                description="The black card is: \N{BLACK LARGE SQUARE} **" + decks[1][game['card']] + "**\n**" + newczar.display_name + "** is the Czar.",
                                color = 16777215
                                )
                        embed.add_field(name="Your hand",value='\n'.join(['`'+str(i+1)+'` \N{WHITE LARGE SQUARE} ' + decks[0][usrhand[i]].strip('\n') for i in range(len(usrhand))]))
                        embed.set_footer(text=message.guild.name + " #" + message.channel.name + " | Game: " + str(message.channel.id))
                        msg = await user.send(embed=embed)
                        [await msg.add_reaction(str(i+1)+'\N{COMBINING ENCLOSING KEYCAP}') for i in range(len(usrhand))]
                quickwrite('sessions',str(games))
            return
            
    #this whole thing is atrocious
    if message.content.lower().startswith(']ping') and message.author.id == 266389941423046657:
        user = await client.fetch_user(266389941423046657)
        await user.send(message.channel.type)
        return
    if message.content.lower().startswith(']sessions read') and message.author.id == 266389941423046657:
        await message.channel.send('```json\n'+quickread('sessions')+'```')
        return
    if message.content.lower().startswith(']sessions write ') and message.author.id == 266389941423046657:
        quickwrite('sessions',message.clean_content.split(']sessions write ')[1])
        await message.channel.send('changes applied')
        return
    if message.content.lower().startswith(']kill') and message.author.id == 266389941423046657:
        await message.channel.send('stopping')
        await client.close()
        
    if message.content.lower().startswith(']cards start'):
        games = ast.literal_eval(quickread('sessions'))
        if not(message.channel.id in games) or (message.channel.id in games and time.time() - games[message.channel.id]['last_active'] > 600):
            createDataIfNecessary(message.author)
            games[message.channel.id] = game_template
            games[message.channel.id]['host'] = message.author.id
            games[message.channel.id]['last_active'] = time.time()
            games[message.channel.id]['players'][message.author.id] = {}
            games[message.channel.id]['players'][message.author.id]['score'] = 0
            games[message.channel.id]['players'][message.author.id]['played'] = 0
            decks = applyCustomDecks(games[message.channel.id])
            games[message.channel.id]['card'] = random.randint(0,len(decks[1]))
            games[message.channel.id]['discard_b'] = [games[message.channel.id]['card']]

            hand = []
            for i in range(cards_per_hand):
                hand.append(random.choice([j for j in range(len(decks[0])) if not j in hand]))
            games[message.channel.id]['players'][message.author.id]['hand'] = hand
            games[message.channel.id]['discard_w'] = hand

            quickwrite('sessions',str(games))

            embed = discord.Embed(
                title="Cards Against Humanity",
                description=message.author.display_name+" started a game. Type `]cards join` to join.\nThe first black card is: \N{BLACK LARGE SQUARE} **"+decks[1][games[message.channel.id]['card']].strip('\n')+"**",
                color=16777215
                )
            embed.set_footer(text="Make sure your DMs are enabled so no one can see your hand.")

            await message.channel.send(embed=embed)
            #await message.author.send("the black card is: " + default_b[games[message.channel.id]['card']] + "your hand is:\n" + ''.join([default_w[i] for i in hand]))

        elif message.channel.id in games:
            await message.channel.send("There is already an active game in this channel!")
        return

    if message.content.lower().startswith(']cards stop'):
        games = ast.literal_eval(quickread('sessions'))
        if not message.channel.id in games:
            await message.channel.send("There's no game to stop in this channel.")
        elif message.author.id != games[message.channel.id]['host']:
            await message.channel.send(message.author.mention + " You're not the host. You can't do that.")
        else:
            games.pop(message.channel.id)
            quickwrite('sessions',str(games))
            await message.channel.send("Game ended.")
        return

    if message.content.lower().startswith(']cards join'):
        games = ast.literal_eval(quickread('sessions'))
        if not message.channel.id in games:
            await message.channel.send("There's no game to join in this channel.")
        elif message.author.id in games[message.channel.id]["players"]:
            await message.channel.send("You've already joined this game.")
        else:
            decks = applyCustomDecks(games[message.channel.id])
            hand = []
            for i in range(cards_per_hand):
                card = random.choice([j for j in range(len(decks[0])) if not(j in hand) and not(j in games[message.channel.id]["discard_w"])])
                hand.append(card)
                games[message.channel.id]["discard_w"].append(card)
            games[message.channel.id]['last_active'] = time.time()
            games[message.channel.id]['players'][message.author.id] = {}
            games[message.channel.id]['players'][message.author.id]['score'] = 0
            games[message.channel.id]['players'][message.author.id]['hand'] = hand
            games[message.channel.id]['players'][message.author.id]['played'] = 0
            quickwrite('sessions',str(games))

            if len(games[message.channel.id]['players']) < min_players:
                await message.channel.send("**"+message.author.display_name+"** joined the game. " + str(3-len(games[message.channel.id]['players'])) + " more players required to start.")

            elif len(games[message.channel.id]['players']) == min_players:
                await message.channel.send("**"+message.author.display_name+"** joined the game.")
                czar = await client.fetch_user([i for i in games[message.channel.id]['players']][games[message.channel.id]['czar']])
                for i in games[message.channel.id]['players']:
                    user = await client.fetch_user(i)
                    usrhand = games[message.channel.id]['players'][user.id]['hand']
                    if i == czar.id:
                        continue
                    embed = discord.Embed(
                            title="You've been dealt in!",
                            description="The black card is: \N{BLACK LARGE SQUARE} **" + decks[1][games[message.channel.id]['card']] + "**\n**" + czar.display_name + "** is the Czar.",
                            color = 16777215
                            )
                    embed.add_field(name="Your hand",value='\n'.join(['`'+str(i+1)+'` \N{WHITE LARGE SQUARE} ' + decks[0][usrhand[i]].strip('\n') for i in range(len(usrhand))]))
                    embed.set_footer(text=message.guild.name + " #" + message.channel.name + " | Game: " + str(message.channel.id))
                    msg = await user.send(embed=embed)
                    [await msg.add_reaction(str(i+1)+'\N{COMBINING ENCLOSING KEYCAP}') for i in range(len(usrhand))]

            else:
                await message.channel.send("**"+message.author.display_name+"** joined the game.")
                czar = await client.fetch_user([i for i in games[message.channel.id]['players']][games[message.channel.id]['czar']])
                usrhand = games[message.channel.id]['players'][message.author.id]['hand']
                embed = discord.Embed(
                            title="You've been dealt in!",
                            description="The black card is: \N{BLACK LARGE SQUARE} **" + decks[1][games[message.channel.id]['card']] + "**\n**" + czar.display_name + "** is the Czar.",
                            color = 16777215
                            )
                embed.add_field(name="Your hand",value='\n'.join(['`'+str(i+1)+'` \N{WHITE LARGE SQUARE} ' + decks[0][usrhand[i]].strip('\n') for i in range(len(usrhand))]))
                embed.set_footer(text=message.guild.name + " " + message.channel.name + " | Game: " + str(message.channel.id))
                msg = await message.author.send(embed=embed)
                [await msg.add_reaction(str(i+1)+'\N{COMBINING ENCLOSING KEYCAP}') for i in range(len(usrhand))]
        return

@client.event
async def on_reaction_add(reaction, user):
    if user == client.user:
        return
    
    if str(reaction.message.channel.type) == 'private' and len(reaction.message.embeds) == 1 and reaction.count >= 1: #if the reaction is in dms (requires members intent which SUCKS)
        games = ast.literal_eval(quickread('sessions'))
        game = int(reaction.message.embeds[0].footer.text.split('Game: ')[1]) # grab the channel ID out of the footer embed
        game_channel = await client.fetch_channel(game)
        if user.id in games[game]['players']: # if they're actually participating
            if not [i for i in games[game]['players']][games[game]['czar']] == user.id and not games[game]['players'][user.id]['played'] >= games[game]['pick_no']:
                # necessary stuff / readability
                decks = applyCustomDecks(games[game])
                games[game]['last_active'] = time.time()
                hand = games[game]['players'][user.id]['hand']
                index = int(reaction.emoji[0])-1
                # play the card
                games[game]['pile'].append({'played_by':user.id,'ids':[hand[index]]})
                games[game]['players'][user.id]['played'] += 1
                await user.send('You played \N{WHITE LARGE SQUARE} **' + decks[0][hand[index]].strip('\n') + '**')
                await game_channel.send("\N{WHITE LARGE SQUARE} " + user.mention + " played a card.")
                hand.pop(index)
                # draw a new card
                new_card = random.choice([j for j in range(len(decks[0])) if not(j in hand) and not(j in games[game]["discard_w"])])
                hand.append(new_card)
                games[game]['discard_w'].append(new_card)
                games[game]['players'][user.id]['hand'] = hand

                # if this is the last card to be played
                if len(games[game]['pile']) == len(games[game]['players'])-1:
                    #send selection to the game channel
                    czar = await client.fetch_user([i for i in games[game]['players']][games[game]['czar']])
                    embed = discord.Embed(
                        title = "All the cards are in!",
                        description = "The black card for this round was: \N{BLACK LARGE SQUARE} **" + decks[1][games[game]['card']].strip('\n') + "**\n\n**" + czar.display_name + "** is the Czar.",
                        color = 16777215
                        )
                    random.shuffle(games[game]['pile'])
                    embed.add_field(name="White cards", value = '\n'.join(['`'+str(i+1)+'` \N{WHITE LARGE SQUARE} **' + ' / '.join([decks[0][j].strip('\n') for j in games[game]['pile'][i]['ids']]) + '**' for i in range(len(games[game]['pile']))]))
                    embed.set_footer(text="Respond with the card's number to select it.")
                    await game_channel.send(embed=embed)
                quickwrite('sessions',str(games))
                
            elif games[game]['players'][user.id]['played'] >= games[game]['pick_no']:
                await user.send("You've already played!")
                
                
            
        
            
client.run('ODc3Mzg5NTkyNTE1NDU3MDU0.YRx6uw.9pKF7Tj0izMKPgC4Rq7_5CDLwxk')
