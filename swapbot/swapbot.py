import discord
import asyncio
from discord.ext import commands
from discord.ext.commands import Bot

import datetime
from dateutil.relativedelta import relativedelta

from pymongo import MongoClient

import subprocess
import json
import requests

#logging purposes
import sys

# Set the date and time format
date_format = "%Y-%m-%d %H:%M:%S"
# Set deadline date/time and put in date format, move to seperate function file later and include.
DEADLINE = datetime.datetime.strptime('2018-12-04 00:00:00', date_format)

# Set the bot prefix
BOT_PREFIX = ("$")

# Bot token generated from Discord
TOKEN = 'DISCORD-API-TOKEN'

#List of administrators DiscordID's for Bot control (shameless, gwal)
authorized_admins = ['322163518046732288','428230231158161409']

#Monitoring ChannelID for bot messages (swapmonitor)
monitor_channel = '483670065116479491'

# Channel restriction for bot commands (coinswap, botadmins)
restrictChannel = '478988009514074143'
restrictChannelAdmin = '483670065116479491'

#Balance threshold for swap bot
balanceThreshold = 1000000

#Confirmations Required
startingConfirmsNeeded = 7
confirmsNeeded = 7
finalConfirmsNeeded = 7
adminFinalConfirmsNeeded = 7

#Coinswap Ratio 1:10
csRatio = 10

#Old Chain Program Path
oldProgramPath = '/home/VPSUSERNAME/PROJECTNAME-old/./PROJECTNAME-cli'

#New Chain Program Path
newProgramPath = '/home/VPSUSERNAME/swapwallet/./PROJECTNAME-cli'

#New Chain Swap Wallet Account (leave blank for change account)
swapWalletAccount = ''
swapWalletAddress = ''

#website link to new wallets
walletDLLink = 'https://github.com/project-PROJECTNAME/PROJECTNAMEcoin/releases'

#RPC Commands
programCMD_gettransaction = 'gettransaction'
programCMD_getaccountaddress = 'getaccountaddress'
programCMD_sendfrom = 'sendfrom'
programCMD_validateaddress = 'validateaddress'
programCMD_getbalance = 'getbalance'

client = Bot(command_prefix=BOT_PREFIX)

# Remove the default Help in order to construct our own
client.remove_command('help')

standardMenu = """
**$alert** *Halts your swap process, sends message to administrators, and places you in queue for assistance from PROJECTNAME Core Team.*
**$snapshot** *Shows the approved balance against the snapshot block for the [address] sent.*
**$help** *Shows this message and describes what each function does.*
**$info** *Gives information about the swap (the necessity, where it can be performed, estimated time left available to perform).*
**$simple** *Provides simplified instructions for advanced users regarding the process of performing swap with me.*
**$instructions** *Provides ordered instructions regarding the process of performing swap with me.*
**$status** *Displays where in the swap process you are currently located.*
**$start** *Initiates the swap process.*
**$sent** *Informs me that you have sent [amount] of PROJECTNAME from [consolidatedAddress] to address I provided along with the [txID].*
**$clearsent** *Clears the [amount] and [txID] that you have submitted.*
**$address** *Informs me of the [address] to send the new coins to. Please triple check this address for accuracy!*
**$agree** *Indicates that you agree to the accuracy of the address you provided and have read the disclaimer*
**$disagree** *Indicates that you have found a discrepancy with the address you provided and allows you to re-enter*
**$confirm** *Informs me that you have received the test transaction on [txID].*
"""

adminMenu = """
===================
**ADMIN FUNCTIONS**
===================
**$export** *Exports swap collection to csv file for review*
**$lookupuser** *Looks up the username associated with the [userID] provided.*
**$alertlist** *Shows all the discord ID's in alert mode.*
**$unalert** *Informs me to clear alert status for [userID] provided.*
**$dumpuser** *Dumps all DB information pertaining to [userID].*
**$resetuser** *Resets swap process to beginning for [userID].  Does not remove generated swap address*
**$monitoruser** *Sets the monitor flag for [userID]. Toggle value 1 (on) or 0 (off)*
**$setbalance** *Sets balance for [userID] (only to be used when remediating a user that didn't consolidate in time).*
**$setoldbalance** *Sets old balance for [userID].*
**$setphase** *Sets phase for [userID].*
**$sweepcomplete** *Searches database for users in phase 9, if confirmations above threshold then bot updates their entry to completed.*
**$swapstats** *Pulls latest coinswap statistics and prints them to the admin channel.*
**$duplicate** *Checks the database for either a new chain or old chain wallet address you provide.*
"""

disclaimer = """

You are hereby certifying that the above address is correct and you are the owner of the funds you authorize to be swapped.  You assume responsibility for any lost funds due to an improper address being submitted.  PROJECTNAME reserves the right to halt your swap process at anytime, should any malicious intent be detected.  **Developers of this bot or PROJECTNAME are not responsible for any coins lost.**   Please triple-check all the information you submit for complete accuracy!
"""

# Channel restriction check
def in_channel(channel_id):
    def predicate(ctx):
        if ctx.message.channel.id == channel_id or ctx.message.channel.is_private == True:
            return True
    return commands.check(predicate)

@client.event
async def on_ready():
    print("Logged in as " + client.user.name)

@client.command(pass_context=True)
@in_channel(restrictChannel)
async def help(ctx):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    if author.id in authorized_admins:
        await client.say(author.mention + ', you can use the following commands:\n' + standardMenu)
        await client.send_message(author, author.mention + ', you can use the following commands:\n' + adminMenu)
    else:
        await client.say(author.mention + ', you can use the following commands:' + standardMenu)

@help.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue commands through DM (direct message) or in the #swapbot channel, Thank you!')

@client.command(pass_context=True)
async def info(ctx):
    monitorValue = logCommand(ctx)
    d = datetime.datetime.now()
    diff = relativedelta(DEADLINE,d)
    author = ctx.message.author
    await client.say(author.mention + """
Greetings fellow PROJECTNAME investors!  I'm the PROJECTNAME SwapBot and I'm going to assist you with completing the OLDCOINTICKER coin swap.  I have some simple instructions for advanced users and detailed instructions for those of you that would like a more in depth explanation of each step.\n  
Here are a few useful commands if you need assistance:\n
**$help** *Shows this message and describes what each function does.*
**$simple** *Provides simplified instructions for advanced users regarding the process of performing swap with me.*
**$instructions** *Provides ordered instructions in detail regarding the process of performing swap with me.*
**$alert** *Halts your swap process, sends message to administrators, and places you in queue for assistance from PROJECTNAME Core Team.*
     \n""" + """
Time remaining to complete coinswap: %d months, %d days, %d hours and %d minutes.""" % (diff.months, diff.days, diff.hours, diff.minutes))

@client.command(pass_context=True)
async def simple(ctx):
    author = ctx.message.author
    await client.say(author.mention + ', below are the simplified instructions.  For more detailed instructions, please use the **$instructions** command.\n' + """
Each of the sentences that start with the "$" are commands that you will be sending directly to me, the SwapBot.\n
**$start** [oldwalletaddress]
VERIFY: Confirm the balance amount.
**$sent** [netamountsent] [txid]
**$status**
**$address** [newwalletaddress]
VERIFY: Triple check the new PROJECTNAME receiving address before proceeding.
**$agree**
VERIFY: Verify that .01 NEWCOINTICKER was received in the new wallet.
**$confirm** [txid]
**$status**\n
**Congratulations**, your coin swap is complete!  When you perform the final $status command your swap will be marked as completed by the bot.

    """)

@client.command(pass_context=True)
async def instructions(ctx):
    author = ctx.message.author
    await client.say(author.mention + ', below are the detailed instructions for performing a successful coin swap utilizing my services.\n' + """
Each of the sentences that start with the "$" are commands that you will be sending directly to me, the SwapBot.\n
1.  1st Command: **$start** [oldwalletaddress]
    a.  Example: `$start LhhLFMj8SHdNpCHoWV5wmQxC7rHnBJEnzs`
    b.  Explanation: To initiate the swap, please respond with the **$start** command and your consolidated wallet address. I will respond with the coin swap receiving address you and the approved balance for your registered OLDCOINTICKER address.  Only the balance displayed will be accepted on the new chain.  If you have a discrepancy with the balance that the snapshot is reporting, then issue the **$alert** command to be placed into the queue for manual administrative intervention.
2.  VERIFY: Confirm the balance is correct and send PROJECTNAME balance in a single transaction to the address that I provided.
3.  2nd Command: **$sent** [amountsent] [txid]
    a.  Example: `$sent 15 1e98ae132f5a277fc1e2ad51cb1e79ec8e9d422e7496c65455a67c212fc98f11`
    b.  NOTE: After sending all PROJECTNAME in a single transaction, respond with the $sent command using the ***After Fee amount*** and txhash for the transaction.
    c.  NOTE: If you copy and paste your transaction, be sure to remove any spaces in the thousands place. 1000 is okay, 1 000 is not okay  
4.  3rd Command: $status
    a.  Example: `$status`
    b.  Explanation: Check your current status by responding with the $status command. I will indicate if I have successfully confirmed the transaction.
Upon enough successful confirmations you will be instructed to download the new wallet.
\n...
""")
    await client.say(author.mention + ',...continued:\n'+"""
5.  4th Command: **$address** [newwalletaddress]
    a.  Example: `$address XANLeD7efUBtVxMWEiYyYfiewGypspSMFj`
    b.  Explanation: After installing the new wallet, syncing the wallet fully, and generating a new address, respond with the $address command with your new address.  This will confirm the wallet address that the bot will be sending the new coins to. New wallets can be found at """+walletDLLink+""".
6.  VERIFY:  Triple check my confirmation of new address received and read the disclaimer before proceeding.
7.  5th Command: **$agree**
    a.  Example: `$agree`
    b.  Explanation:  Respond with $agree to confirm the new receiving address is correct and that the disclaimer has been read.
8.  VERIFY:  Verify that .01 NEWCOINTICKER was received in the new wallet. 
9.  6th Command: **$confirm** [txid]
    a.  Example: `$confirm 138173567d430b154877e4e004ebafefce90c38038f920a0aacb03055c72514b`
    b.  Explanation: Confirm the test transaction by issuing the $confirm command along with the txid (txhash) of the test transaction.  Once the test transaction has been confirmed, then your remaining balance will begin to transfer.
    c.  NOTE: You may need to enter this command multiple times until all confirmations have been completed.  Expect this wait time to be around 75 minutes.
10. 7th Command: **$status**
    a.  Example: `$status`
    b.  Explanation: Respond with $status to check that the final transaction has been completed successfully.

Congratulations, your coin swap is complete!  When you perform the final $status command your swap will be marked as completed by the bot
    """)

@client.command(pass_context=True)
@in_channel(restrictChannel)
async def status(ctx):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    try:
        mc = MongoClient('localhost', 27017)
        db = mc.coinswap
        swaps = db.swaps
        cur = swaps.find_one({'discordID':author.id})
        if cur is None:
            await client.say(author.mention + ', you have not started the coin swap process yet. Please utilize the **$start** command once you are ready to begin.')
        else:
            phase = cur['assignedPhase']
            generatedAddress = cur['oldAddress']
            if phase == ''or phase == 1:
                await client.say(author.mention + ', you have not started the coin swap process yet. Please utilize the **$start** command once you are ready to begin.')
            elif phase == 2:
                await client.send_message(author,author.mention + ', I am currently awaiting for you to send your approved balance of '+ str(cur['snapshotBalance']) +' (minus any transaction fees) to **' + str(generatedAddress) + '**, and then issue the **$sent** command.')
            elif phase == 3 or phase == 4 or phase == 5:
                balanceReported = cur['oldBalance']
                txReported = cur['oldTxID']
                txLookup = subprocess.Popen([oldProgramPath,programCMD_gettransaction,str(txReported)], shell=False, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip()
                txLookup = json.loads(txLookup)
                txAmount = txLookup['amount']
                txConfirms = txLookup['confirmations']
                txID = txLookup['txid']
                accountID = txLookup['details'][0]['account']
                amountConfirm = txLookup['details'][0]['amount']
                addressConfirm = txLookup['details'][0]['address']
                if txConfirms is not '':
                    if addressConfirm == cur['oldAddress'] and accountID == cur['discordID']:
                        if float(balanceReported) == float(txAmount) and str(txReported) == str(txID) and int(txConfirms) < int(startingConfirmsNeeded):
                            await client.send_message(author,author.mention + ', your transfer is currently pending. ' + str(txConfirms) + ' out of ' + str(startingConfirmsNeeded) + ' confirmations received. Please check back later.')
                        elif float(balanceReported) == float(txAmount) and str(txReported) == str(txID) and int(txConfirms) >= int(startingConfirmsNeeded):
                            swaps.update_one({'discordID':author.id}, {'$set':{'assignedPhase':6}})
                            await client.say(author.mention + ', your transfer has been successfully confirmed! Please install the new wallet found here '+walletDLLink+'. Once the wallet is installed, synced fully with the blockchain, and you have generated a receiving address, you are then ready to issue the **$address** command.')
                        else:
                            await client.say(author.mention + ', I have yet to find your transaction. Please check back later. If I cannot locate within 15 minutes, please run **$clearsent**, double verify your amount and transaction id, then run **$sent** again.  If you still are having issues, then run **$alert** to contact a team member.')
                    else:
                        swaps.update_one({'discordID':author.id}, {'$set': {'monitor':1 }})
                        await client.send_message(discord.Object(id=monitor_channel),'ALERT! - Discord userID '+author.id+' checked their status but the txid does not match their old chain swap address or discord user account')
                        await client.say(author.mention + ', I have yet to find your transaction. Please check back later. If I cannot locate within 15 minutes, please run **$clearsent**, double verify your amount and transaction id, then run **$sent** again.  If you still are having issues, then run **$alert** to contact a team member.')
            elif phase == 6:
                await client.say(author.mention + ', please ensure you have installed the new wallet found here '+walletDLLink+'. Once the wallet is installed, synced fully with the blockchain, and you have generated a receiving address, you are then ready to issue the **$address** command.')
            elif phase == 7:
                newAddress = cur['newAddress']
                await client.send_message(author,author.mention + ', you have indicated that your new address is **' + str(newAddress) + '**. If this is correct please ensure you have read the below disclaimer and then issue the **$agree** command. If the address is incorrect, please issue the **$disagree** command to re-enter the address.\n' + disclaimer)
            elif phase == 8:
                await client.say(author.mention + ', thank you for confirming your address and agreeing to the disclaimer. Please be on the lookout for a test transaction of .01 OLDCOINTICKER sent to your new wallet. Upon receipt please utilize the **$confirm** command along with the txID.')
            elif phase == 9:
                newTxID = cur['newTxID']
                txLookup = subprocess.Popen([newProgramPath,programCMD_gettransaction,str(newTxID)], shell=False, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip()
                txLookup = json.loads(txLookup)
                txConfirms = txLookup['confirmations']
                if int(txConfirms) < int(finalConfirmsNeeded):
                    await client.send_message(author,author.mention + ', your final transfer is currently pending. ' + str(txConfirms) + ' out of ' + str(finalConfirmsNeeded) + ' recommended confirmations received on txID ' + str(newTxID) + ' . Please check back later.')
                elif int(txConfirms) >= int(finalConfirmsNeeded):
                    swaps.update_one({'discordID':author.id}, {'$set':{'assignedPhase':10, 'endDate':datetime.datetime.now(), 'processCompleted':1}})
                    await client.say(author.mention + ', you have now successfully finished the coin swap! Thank you for being a dedicated member of the PROJECTNAME Community!')
                else:
                    await client.say(author.mention + ', I have yet to find your transaction. Please check back later.')
            elif phase == 10:
                await client.say(author.mention + ', you have already finished the coin swap. Thank you for being a dedicated member of the PROJECTNAME Community! Please reach out to a team member if you believe you have encountered an error.')
    except Exception as e:
        print(e)
    finally:
        mc.close()

@status.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue commands through DM (direct message) or in the #swapbot channel, Thank you!')

@client.command(pass_context=True)
@in_channel(restrictChannel)
async def alert(ctx):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    try:
        mc = MongoClient('localhost', 27017)
        db = mc.coinswap
        swaps = db.swaps
        cur = swaps.find_one({'discordID':author.id})
        if cur is None:
            genAddress = subprocess.Popen([oldProgramPath,programCMD_getaccountaddress,str(author.id)], shell=False, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip()
            swaps.insert_one({
                'discordID':author.id,
                'oldAddress':genAddress,
                'oldBalance':'',
                'oldTxID':'',
                'snapshotBalance':'',
                'startDate':'',
                'assignedPhase':1,
                'newAddress':'',
                'agreedToDisclaimer':'',
                'agreedOnDate':'',
                'newBalance':'',
                'newTxID':'',
                'endDate':'',
                'processCompleted':0,
                'testTxID':'',
                'alert':1,
                'swappingAddress':'',
                'monitor':0
            })
            await client.say(author.mention + ", your swap has been locked and the PROJECTNAME Core Team notified.  A team member will be contacting you to resolve your issue.")
            await client.send_message(discord.Object(id=monitor_channel),'Discord userID '+author.id+' issued alert command **before starting!**')
        else:
            swaps.update_one({'discordID':author.id}, {'$set': {'alert':1,'monitor':1 }})
            await client.say(author.mention + ', your swap has been locked and the PROJECTNAME Core Team notified.  A team member will be contacting you to resolve your issue.')
            await client.send_message(discord.Object(id=monitor_channel),'Discord userID '+author.id+' issued alert command!')
    except Exception as e:
        print(e)
    finally:
        mc.close()

@alert.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue commands through DM (direct message) or in the #swapbot channel, Thank you!')

@client.command(pass_context=True)
@in_channel(restrictChannel)
async def start(ctx, address):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    address = cleaner(address)
    result = checkOldAddress(address)
    result = json.loads(result)
    #Check if address is valid by examining rpc call to wallet and json result.
    balance = lookupBalance(address)
    if not 'False' in str(result['isvalid']) and not 'error' in str(balance):
        try:
            mc = MongoClient('localhost', 27017)
            db = mc.coinswap
            swaps = db.swaps
            addressCheck = swaps.find_one({'swappingAddress':address})
            if addressCheck is None:
                cur = swaps.find_one({'discordID':author.id})
                if cur is None:
                    genAddress = subprocess.Popen([oldProgramPath,programCMD_getaccountaddress,str(author.id)], shell=False, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip()
                    swaps.insert_one({
                        'discordID':author.id,
                        'oldAddress':genAddress,
                        'oldBalance':'',
                        'oldTxID':'',
                        'snapshotBalance':balance,
                        'startDate':datetime.datetime.now(),
                        'assignedPhase':2,
                        'newAddress':'',
                        'agreedToDisclaimer':'',
                        'agreedOnDate':'',
                        'newBalance':'',
                        'newTxID':'',
                        'endDate':'',
                        'processCompleted':0,
                        'testTxID':'',
                        'alert':0,
                        'swappingAddress':address,
                        'monitor':0
                    })
                    await client.send_message(author,author.mention + ", let's begin. Your authorized snapshot balance is **"+str(balance)+"** OLDCOINTICKER, please send your entire balance in one transaction to **" + str(genAddress) + "** (Please ensure to record the exact amount sent along with the txID for the next step)")
                else:
                    if int(monitorValue) > 0:
                        await client.send_message(discord.Object(id=monitor_channel),str(author) + ' , discord userID '+author.id+'\nLast Command Monitored - \n'+str(ctx.message.content))
                    phase = cur['assignedPhase']
                    if phase == 1:
                        swaps.update_one({'discordID':author.id}, {'$set': {
                        'startDate':datetime.datetime.now(),
                        'assignedPhase':2,
                        'processCompleted':0,
                        'snapshotBalance':balance,
                        'alert':0,
                        'swappingAddress':address}})
                        await client.send_message(author,author.mention + ", let's begin. Your authorized snapshot balance is **"+str(balance)+"** OLDCOINTICKER, please send your entire balance in one transaction to **" + str(cur['oldAddress']) + "** (Please ensure to record the exact amount sent along with the txID for the next step)")
                    else:
                        await client.say(author.mention + ', please utilize the **$status** command to find out what to do next.')
            else:
                await client.say(author.mention + ', the address that you have submitted already exists in the swap database.  Please issue the **$alert** to signal a team member for help.')
        except Exception as e:
            print(e)
        finally:
            mc.close()
    else:
        await client.say(author.mention + ', please ensure you are submitting a valid OLDCOINTICKER **address**. Ex. **$start LhhLFMj8SHdNpCHoWV5wmQxC7rHnBJEnzs**')

@start.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue commands through DM (direct message) or in the #swapbot channel, Thank you!')
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        author = ctx.message.author
        await client.say(author.mention + ', please ensure you are including your consolidated OLDCOINTICKER **address**. Ex. **$start LhhLFMj8SHdNpCHoWV5wmQxC7rHnBJEnzs**')

@client.command(pass_context=True)
@in_channel(restrictChannel)
async def sent(ctx, amount, txID):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    numberCheck = validNumber(amount)
    txID = cleaner(txID)
    if numberCheck == True:
        try:
            mc = MongoClient('localhost', 27017)
            db = mc.coinswap
            swaps = db.swaps
            cur = swaps.find_one({'discordID':author.id})
            if cur is None:
                await client.say(author.mention + ', you have not started the coin swap process yet. Please utilize the **$start** command once you are ready to begin.')
            else:
                if float(amount) <= float(cur['snapshotBalance']):
                    phase = cur['assignedPhase']
                    if int(monitorValue) > 0:
                            await client.send_message(discord.Object(id=monitor_channel),str(author) + ' , discord userID '+author.id+'\nLast Command Monitored - \n'+str(ctx.message.content))
                    if phase == 2:
                        if float(amount) < float(cur['snapshotBalance'])-0.01:
                            await client.say(author.mention + ', the amount that you have submitted varies too much from the authorized Snapshot block balace amount for your given address.  Please use the **$alert** command to notify the team.')
                        else:
                            swaps.update_one({'discordID':author.id}, {'$set': {'oldBalance':float(amount), 'oldTxID':str(txID), 'assignedPhase':3}})
                            await client.send_message(author,author.mention + ', I will be on the lookout for ' + str(amount) + ' OLDCOINTICKER found on txID ' + str(txID) + '!')
                    elif phase > 2:
                        await client.say(author.mention + ', you have already issued the **$sent** command! Please utilize **$status** to see if I have recieved the transaction yet.')
                else:
                    swaps.update_one({'discordID':author.id}, {'$set': {'monitor':1}})
                    if int(monitorValue) > 0:
                            await client.send_message(discord.Object(id=monitor_channel),str(author) + ' , discord userID '+author.id+'\nLast Command Monitored - \n'+str(ctx.message.content))
                    await client.say(author.mention + ', the amount that you have submitted cannot exceed the authorized Snapshot block balance amount for your given address.')
        except Exception as e:
            print(e)
        finally:
            mc.close()
    else:
        await client.say(author.mention + ', the amount that you have submitted does not match the Snapshot block amount for your given address.  Please submit the exact amount sent (this means the amount **After Fee**) with the transaction id.')

@sent.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue commands through DM (direct message) or in the #swapbot channel, Thank you!')
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        author = ctx.message.author
        await client.say(author.mention + ', please ensure you are including the exact **amount** and **txID** ex. **$sent** 15 7531174f5c68047ea0ad4a5445d134842b1d749cfa48279b1f93b8e66f95f07f')

@client.command(pass_context=True)
@in_channel(restrictChannel)
async def clearsent(ctx):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    try:
        mc = MongoClient('localhost', 27017)
        db = mc.coinswap
        swaps = db.swaps
        cur = swaps.find_one({'discordID':author.id})
        if cur is None:
            await client.say(author.mention + ', you have not started the coin swap process yet. Please utilize the **$start** command once you are ready to begin.')
        else:
            if int(monitorValue) > 0:
                    await client.send_message(discord.Object(id=monitor_channel),str(author) + ' , discord userID '+author.id+'\nLast Command Monitored - \n'+str(ctx.message.content))
            phase = cur['assignedPhase']
            if phase == 3:
                swaps.update_one({'discordID':author.id}, {'$set': {'oldBalance':'', 'oldTxID':'', 'assignedPhase':2}})
                await client.say(author.mention + ', I have cleared your $sent amount and trasaction ID information! Please run the $sent command again using the proper information.')
            else:
                await client.say(author.mention + ', you may only run this command if you just issued the $sent command and need to re-enter the information.')
    except Exception as e:
        print(e)
    finally:
        mc.close()

@clearsent.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue commands through DM (direct message) or in the #swapbot channel, Thank you!')

@client.command(pass_context=True)
@in_channel(restrictChannel)
async def address(ctx, address):
    monitorValue = logCommand(ctx)
    logWalletAddress(ctx,address)
    address = cleaner(address)
    #input validation on new chain address var and duplicate address check for new wallet address
    result = checkNewAddress(address)
    result = json.loads(result)
    version = address[:1]
    if not 'false' in str(result['isvalid']) or version != "X":
        author = ctx.message.author
        try:
            mc = MongoClient('localhost', 27017)
            db = mc.coinswap
            swaps = db.swaps
            addressCheck = swaps.find_one({'newAddress':address})
            if addressCheck is None:
                print("passed adress check")
                cur = swaps.find_one({'discordID':author.id})
                if cur is None:
                    await client.say(author.mention + ', you have not started the coin swap process yet. Please utilize the **$start** command once you are ready to begin.')
                else:

                    if int(monitorValue) > 0:
                            await client.send_message(discord.Object(id=monitor_channel),str(author) + ' , discord userID '+author.id+'\nLast Command Monitored - \n'+str(ctx.message.content))
                    phase = cur['assignedPhase']
                    if phase < 6:
                        await client.say(author.mention + ', you are not allowed to run this command yet. Please utilize the **$status** command to find out what to do next.')
                    elif phase == 6:
                        swaps.update_one({'discordID':author.id}, {'$set': {'newAddress':str(address), 'assignedPhase':7}})
                        await client.send_message(author,author.mention + ', please verify that this address is correct and ensure you have read the disclaimer. After doing so you may then utilize the **$agree** or **$disagree** command.\n\nYour submitted address to transfer the new coins to is:\n'+ str(address) + '\n' + disclaimer)
                    else:
                        await client.say(author.mention + ', you have already issued the **$address** command. Please utilize the **$status** command to find out what to do next.')
            else:
                await client.say(author.mention + ', the address that you have submitted already exists in the swap database.  Please issue the **$alert** to signal a team member for help.')
        except Exception as e:
            print(e)
        finally:
            mc.close()
    else:
        await client.say(author.mention + ', please ensure you are submitting a valid NEW NEWCOINTICKER **address**. Ex. **$start XDYdNHywM3Jfazuk97dJUfqFUuAvEyMrgm**')

@address.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue commands through DM (direct message) or in the #swapbot channel, Thank you!')
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        author = ctx.message.author
        await client.say(author.mention + ', please ensure you are including your new wallet **address**')

@client.command(pass_context=True)
@in_channel(restrictChannel)
async def disagree(ctx):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    try:
        mc = MongoClient('localhost', 27017)
        db = mc.coinswap
        swaps = db.swaps
        cur = swaps.find_one({'discordID':author.id})
        if cur is None:
            await client.say(author.mention + ', you have not started the coin swap process yet. Please utilize the **$start** command once you are ready to begin.')
        else:
            if int(monitorValue) > 0:
                    await client.send_message(discord.Object(id=monitor_channel),str(author) + ' , discord userID '+author.id+'\nLast Command Monitored - \n'+str(ctx.message.content))
            phase = cur['assignedPhase']
            if phase < 7:
                await client.say(author.mention + ', you are not allowed to run this command yet. Please utilize the **$status** command to find out what to do next.')
            elif phase == 7:
                swaps.update_one({'discordID':author.id}, {'$set': {'newAddress':'', 'assignedPhase':6}})
                await client.say(author.mention + ', please issue the **$address** command again with the correct address.')
            else:
                await client.say(author.mention + ', you are not allowed to run this command. Please utilize the **$status** command to find out what to do next.')
    except Exception as e:
        print(e)
    finally:
        mc.close()

@disagree.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue commands through DM (direct message) or in the #swapbot channel, Thank you!')

@client.command(pass_context=True)
@in_channel(restrictChannel)
async def agree(ctx):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    try:
        mc = MongoClient('localhost', 27017)
        db = mc.coinswap
        swaps = db.swaps
        cur = swaps.find_one({'discordID':author.id})
        if cur is None:
            await client.say(author.mention + ', you have not started the coin swap process yet. Please utilize the **$start** command once you are ready to begin.')
        else:
            if int(monitorValue) > 0:
                    await client.send_message(discord.Object(id=monitor_channel),str(author) + ' , discord userID '+author.id+'\nLast Command Monitored - \n'+str(ctx.message.content))
            phase = cur['assignedPhase']
            if phase < 7:
                await client.say(author.mention + ', you are not allowed to run this command yet. Please utilize the **$status** command to find out what to do next.')
            elif phase == 7:
                newAddress = cur['newAddress']
                testAmount = '0.01'
                testTxID = subprocess.Popen([newProgramPath,programCMD_sendfrom,swapWalletAccount,str(newAddress),testAmount], shell=False, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip()
                #input a verification check on the txID returned.  if it is blank in the db then the transaction failed
                if testTxID == '':
                    await client.send_message(author,author.mention + ', the swap process will resume shortly, bot is at maximum outbound transfers currently.  Please try again in 30 minutes.')
                    await client.send_message(discord.Object(id=monitor_channel),str(author) + ' , discord userID '+author.id+'\nUnable to do $agree for test amount because swap bot is lacking sufficient available funds.')
                else:
                    swaps.update_one({'discordID':author.id}, {'$set': {'agreedToDisclaimer':1, 'agreedOnDate':datetime.datetime.now(), 'assignedPhase':8, 'testTxID':str(testTxID), 'newBalance':.01}})
                    await client.say(author.mention + ', thank you for confirming the accuracy of the address and agreeing to the disclaimer. Please be on the lookout for a small test transaction of .01 NEWCOINTICKER sent to your new wallet. Once received, please utilize the **$confirm** command.')
                    swapBalance = subprocess.Popen([newProgramPath,programCMD_getbalance], shell=False, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip()
                    if float(swapBalance) <= balanceThreshold:
                        await client.send_message(discord.Object(id=monitor_channel),'**WARNING** Bot is getting low on funds, transfer more to swap address.')
            else:
                await client.say(author.mention + ', you have already utilized this command. Please utlize the **$status** command to find out what to do next.')
    except Exception as e:
        print(e)
    finally:
        mc.close()

@agree.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue commands through DM (direct message) or in the #swapbot channel, Thank you!')

@client.command(pass_context=True)
@in_channel(restrictChannel)
async def confirm(ctx, txID):
    monitorValue = logCommand(ctx)
    txID = cleaner(txID)
    author = ctx.message.author
    try:
        mc = MongoClient('localhost', 27017)
        db = mc.coinswap
        swaps = db.swaps
        cur = swaps.find_one({'discordID':author.id})
        if cur is None:
            await client.say(author.mention + ', you have not started the coin swap process yet. Please utilize the **$start** command once you are ready to begin.')
        else:
            if int(monitorValue) > 0:
                    await client.send_message(discord.Object(id=monitor_channel),str(author) + ' , discord userID '+author.id+'\nLast Command Monitored - \n'+str(ctx.message.content))
            phase = cur['assignedPhase']
            if phase < 8:
                await client.say(author.mention + ', you are not allowed to run this command yet. Please utilize the **$status** command to find out what to do next.')
            elif phase == 8:
                testTxID = cur['testTxID']
                txLookup = subprocess.Popen([newProgramPath,programCMD_gettransaction,str(testTxID)], shell=False, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip()
                txLookup = json.loads(txLookup)
                txConfirms = txLookup['confirmations']
                txFee = cur['snapshotBalance']-cur['oldBalance']
                if str(txID) == str(testTxID) and int(txConfirms) < int(confirmsNeeded):
                    await client.send_message(author,author.mention + ', the transfer is currently pending. ' + str(txConfirms) + ' out of ' + str(confirmsNeeded) + ' recommended confirmations received. Please check back later.')
                elif str(txID) == str(testTxID) and int(txConfirms) >= int(confirmsNeeded):
                    remainingBalTran = float((float(cur['oldBalance']) + float(txFee)) * csRatio) - float(cur['newBalance'])
                    newAddress = cur['newAddress']
                    newTxID = subprocess.Popen([newProgramPath,programCMD_sendfrom,swapWalletAccount,str(newAddress),str(remainingBalTran)], shell=False, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip()
                    if newTxID == '':
                        await client.send_message(author,author.mention + ', the swap process will resume shortly, bot is at maximum outbound transfers currently.  Please try again in 30 minutes.')
                        await client.send_message(discord.Object(id=monitor_channel),str(author) + ' , discord userID '+author.id+'\nUnable to do $confirm because swap bot is lacking sufficient available funds.')
                    else:
                        swaps.update_one({'discordID':author.id}, {'$set': {'assignedPhase':9, 'newBalance':float(cur['newBalance']) + float(remainingBalTran), 'newTxID':str(newTxID)}})
                        await client.send_message(author,author.mention + ', your wallet address has been successfully confirmed. I will send out the remaining balance of ' + str(remainingBalTran) + ' NEWCOINTICKER momentarily. Use the **$status** command to check for a txID.')
                else:
                    await client.say(author.mention + ', that txID does not match what I have on file. Please ensure you are entering the correct txID.')
            else:
                await client.say(author.mention + ', you have already confirmed the test transaction. Please utilize the **$status** command to find out what to do next.')

    except Exception as e:
        print(e)
    finally:
        mc.close()

@confirm.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue commands through DM (direct message) or in the #swapbot channel, Thank you!')
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        author = ctx.message.author
        await client.say(author.mention + ', Please ensure you are submitting the txID when using the **$confirm** command. Ex. $confirm feb2df0456aa3f0871a4011ed4e8107cce96fad3aab226955f4bbbdfd9912f04')

@client.command(pass_context=True)
async def snapshot(ctx, address):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    result = lookupBalance(address)
    #Check if address is valid by examining json result.  Need to add search of collection for duplicate address check
    if not 'error' in str(result):
        if int(monitorValue) > 0:
            await client.send_message(discord.Object(id=monitor_channel),str(author) + ' , discord userID '+author.id+'\nSnapshot Command Monitored - \nThe approved balance for wallet address **'+str(address)+'** is **'+str(result)+'**.')
        await client.send_message(author,author.mention + ', the approved balance for wallet address **'+str(address)+'** is **'+str(result)+'**. If you feel this balance is wrong then issue the **$alert** command.  This will place you in queue to speak with someone from the PROJECTNAME Core Team.')
    else:
        await client.say(author.mention + ', sorry but you have not supplied a valid OLDCOINTICKER address')

@snapshot.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue commands through DM (direct message) or in the #swapbot channel, Thank you!')
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        author = ctx.message.author
        await client.send_message(author,author.mention + ', Please ensure you are including the OLDCOINTICKER wallet address to check against the snapshot block.')

@client.command(pass_context=True)
@in_channel(restrictChannelAdmin)
async def export(ctx):
    timestamp = datetime.datetime.now()
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    if author.id in authorized_admins:
        pushrecords = "mongoexport --db coinswap --collection swaps --type=csv --fields discordID,oldAddress,oldBalance,oldTxID,snapshotBalance,startDate,assignedPhase,newAddress,agreedToDisclaimer,agreedOnDate,newBalance,newTxID,endDate,processCompleted,monitor,alert --out /home/botadmin/swapbot/exports/coinswap"+str(timestamp.year)+str(timestamp.month)+str(timestamp.day)+".csv"
        process = subprocess.Popen(pushrecords.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        await client.send_message(author,author.mention + ', csv backup created successfully')
    else:
        await client.send_message(author,author.mention + ', sorry but you are not allowed to run this command.')

@export.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue admin commands through DM (direct message) or from the admin channel, Thank you!')

@client.command(pass_context=True)
@in_channel(restrictChannelAdmin)
async def alertlist(ctx):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    if author.id in authorized_admins:
        try:
            mc = MongoClient('localhost', 27017)
            db = mc.coinswap
            swaps = db.swaps
            cur = swaps.find({'alert':1})
            idList = []
            if cur is not None:
                for document in cur:
                    print(document['discordID'])
                    idList.append(document['discordID'])
            print(idList)
            await client.say(author.mention + ', the following discord users are in alert mode '+str(idList)+' \n use the $dumpuser command and their ID to gather more information on the potential issue.')
        except Exception as e:
            logException(e)
        finally:
            mc.close()
    else:
        await client.send_message(author,author.mention + ', sorry but you are not allowed to run this command.')

@alertlist.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue admin commands through DM (direct message) or from the admin channel, Thank you!')

@client.command(pass_context=True)
@in_channel(restrictChannelAdmin)
async def lookupuser(ctx, userid):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    if author.id in authorized_admins:
        for user in client.get_all_members():
            if user.id == userid:
                await client.send_message(author,author.mention + ', username for '+str(user.id)+' is '+str(user)+' and may also go by '+str(user.display_name))
    else:
        await client.send_message(author,author.mention + ', sorry but you are not allowed to run this command.')

@lookupuser.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue admin commands through DM (direct message) or from the admin channel, Thank you!')
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        author = ctx.message.author
        await client.send_message(author,author.mention + ', please ensure you are including the discord user ID when using **$lookupuser**.')

@client.command(pass_context=True)
@in_channel(restrictChannelAdmin)
async def unalert(ctx, userid):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    if author.id in authorized_admins:
        try:
            mc = MongoClient('localhost', 27017)
            db = mc.coinswap
            swaps = db.swaps
            cur = swaps.find_one({'discordID':userid})
            if cur is None:
                await client.send_message(author,author.mention + ", user not in swap database.")
            else:
                swaps.update_one({'discordID':userid}, {'$set': {'alert':0, 'monitor':0}})
                await client.send_message(author,author.mention + ', discord user ID '+str(userid)+' is no longer in alert status.')
                await client.send_message(discord.Object(id=monitor_channel),author.mention + ', discord user ID '+str(userid)+' is no longer in alert status.')
        except Exception as e:
            print(e)
        finally:
            mc.close()
    else:
        await client.send_message(author,author.mention + ', sorry but you are not allowed to run this command.')

@unalert.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue admin commands through DM (direct message) or from the admin channel, Thank you!')
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        author = ctx.message.author
        await client.send_message(author,author.mention + ', please ensure you are including the discord user ID when using **$unalert**.')

@client.command(pass_context=True)
@in_channel(restrictChannelAdmin)
async def resetuser(ctx, userid):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    if author.id in authorized_admins:
        try:
            mc = MongoClient('localhost', 27017)
            db = mc.coinswap
            swaps = db.swaps
            cur = swaps.find_one({'discordID':userid})
            if cur is None:
                await client.send_message(author,author.mention + ", user not in swap database.")
            else:
                swaps.update_one({'discordID':userid}, {'$set': {
                    'oldBalance':'',
                    'oldTxID':'',
                    'startDate':'',
                    'assignedPhase':1,
                    'newAddress':'',
                    'agreedToDisclaimer':'',
                    'agreedOnDate':'',
                    'newBalance':'',
                    'newTxID':'',
                    'endDate':'',
                    'processCompleted':0,
                    'testTxID':'',
                    'snapshotBalance':'',
                    'alert':0,
                    'swappingAddress':''}})
                await client.send_message(author,author.mention + ', discord user ID '+str(userid)+' reset completely.')
                await client.send_message(discord.Object(id=monitor_channel),author.mention + ', discord user ID '+str(userid)+' reset completely.')  
        except Exception as e:
            print(e)
        finally:
            mc.close()
    else:
        await client.send_message(author,author.mention + ', sorry but you are not allowed to run this command.')

@resetuser.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue admin commands through DM (direct message) or from the admin channel, Thank you!')
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        author = ctx.message.author
        await client.send_message(author,author.mention + ', please ensure you are including the discord user ID when using **$resetuser**.')

@client.command(pass_context=True)
@in_channel(restrictChannelAdmin)
async def monitoruser(ctx, userid, t):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    if author.id in authorized_admins:
        try:
            mc = MongoClient('localhost', 27017)
            db = mc.coinswap
            swaps = db.swaps
            cur = swaps.find_one({'discordID':userid})
            if cur is None:
                await client.send_message(author,author.mention + ", user not in swap database.")
            else:
                swaps.update_one({'discordID':userid}, {'$set': {'monitor':int(t)}})
                await client.send_message(author,author.mention + ', discord user ID '+str(userid)+' monitor set to '+str(t))
                await client.send_message(discord.Object(id=monitor_channel),author.mention + ', discord user ID '+str(userid)+' monitor set to '+str(t))  
        except Exception as e:
            print(e)
        finally:
            mc.close()
    else:
        await client.send_message(author,author.mention + ', sorry but you are not allowed to run this command.')

@monitoruser.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue admin commands through DM (direct message) or from the admin channel, Thank you!')
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        author = ctx.message.author
        await client.send_message(author,author.mention + ', please ensure you are including the discord user ID and toggle value when using **$monitoruser**. Ex. **$monitoruser** [discordID] [1 or 0]')

@client.command(pass_context=True)
@in_channel(restrictChannelAdmin)
async def dumpuser(ctx, userid):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    if author.id in authorized_admins:
        try:
            mc = MongoClient('localhost', 27017)
            db = mc.coinswap
            swaps = db.swaps
            cur = swaps.find_one({'discordID':userid})
            if cur is None:
                await client.send_message(author,author.mention + ", user not in swap database.")
            else:
                await client.say(author.mention + ', discord user ID '+str(userid)+' has the following data:\n'+str(cur))
        except Exception as e:
            print(e)
        finally:
            mc.close()
    else:
        await client.send_message(author,author.mention + ', sorry but you are not allowed to run this command.')

@dumpuser.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue admin commands through DM (direct message) or from the admin channel, Thank you!')
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        author = ctx.message.author
        await client.send_message(author,author.mention + ', please ensure you are including the discord user ID when using **$dumpuser**.')

@client.command(pass_context=True)
@in_channel(restrictChannelAdmin)
async def setbalance(ctx, userid, balance):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    if author.id in authorized_admins:
        try:
            mc = MongoClient('localhost', 27017)
            db = mc.coinswap
            swaps = db.swaps
            cur = swaps.find_one({'discordID':userid})
            if cur is None:
                await client.send_message(author,author.mention + ", user not in swap database.")
            else:
                swaps.update_one({'discordID':userid}, {'$set': {'snapshotBalance':float(balance)}})
                await client.send_message(author,author.mention + ', discord user ID '+str(userid)+' has a manual balance set of :\n'+str(balance))
                await client.send_message(discord.Object(id=monitor_channel),author.mention + ', discord user ID '+str(userid)+' has a manual balance set of :\n'+str(balance))
        except Exception as e:
            print(e)
        finally:
            mc.close()
    else:
        await client.send_message(author,author.mention + ', sorry but you are not allowed to run this command.')

@setbalance.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue admin commands through DM (direct message) or from the admin channel, Thank you!')
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        author = ctx.message.author
        await client.send_message(author,author.mention + ', please ensure you are including the discord user ID and balance when using **$setbalance**.')

@client.command(pass_context=True)
@in_channel(restrictChannelAdmin)
async def setoldbalance(ctx, userid, balance):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    if author.id in authorized_admins:
        try:
            mc = MongoClient('localhost', 27017)
            db = mc.coinswap
            swaps = db.swaps
            cur = swaps.find_one({'discordID':userid})
            if cur is None:
                await client.send_message(author,author.mention + ", user not in swap database.")
            else:
                swaps.update_one({'discordID':userid}, {'$set': {'oldBalance':float(balance)}})
                await client.send_message(author,author.mention + ', discord user ID '+str(userid)+' has a manual balance set of :\n'+str(balance))
                await client.send_message(discord.Object(id=monitor_channel),author.mention + ', discord user ID '+str(userid)+' has a manual balance set of :\n'+str(balance))
        except Exception as e:
            print(e)
        finally:
            mc.close()
    else:
        await client.send_message(author,author.mention + ', sorry but you are not allowed to run this command.')

@setoldbalance.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue admin commands through DM (direct message) or from the admin channel, Thank you!')
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        author = ctx.message.author
        await client.send_message(author,author.mention + ', please ensure you are including the discord user ID and balance when using **$setoldbalance**.')

@client.command(pass_context=True)
@in_channel(restrictChannelAdmin)
async def setphase(ctx, userid, phase):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    if author.id in authorized_admins:
        try:
            mc = MongoClient('localhost', 27017)
            db = mc.coinswap
            swaps = db.swaps
            cur = swaps.find_one({'discordID':userid})
            if cur is None:
                await client.send_message(author,author.mention + ", user not in swap database.")
            else:
                swaps.update_one({'discordID':userid}, {'$set': {'assignedPhase':int(phase)}})
                await client.send_message(author,author.mention + ', discord user ID '+str(userid)+' had their phase manually set to :\n'+str(phase))  
                await client.send_message(discord.Object(id=monitor_channel),author.mention + ', discord user ID '+str(userid)+' had their phase manually set to :\n'+str(phase))  
        except Exception as e:
            print(e)
        finally:
            mc.close()
    else:
        await client.send_message(author,author.mention + ', sorry but you are not allowed to run this command.')

@setphase.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue admin commands through DM (direct message) or from the admin channel, Thank you!')
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        author = ctx.message.author
        await client.send_message(author,author.mention + ', please ensure you are including the discord user ID and phase number when using **$setphase**.')

@client.command(pass_context=True)
@in_channel(restrictChannelAdmin)
async def swapstats(ctx):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    if author.id in authorized_admins:
        try:
            mc = MongoClient('localhost', 27017)
            db = mc.coinswap
            swaps = db.swaps
            previous24 = datetime.datetime.today() - datetime.timedelta(days=1)
            regTotal = swaps.count()
            startTotal = swaps.find({"assignedPhase":{"$gt":0}}).count()
            finalStepTotal = swaps.find({"assignedPhase":{"$eq":9}}).count()
            newWalletTotal = swaps.find({"assignedPhase":{"$eq":6}}).count()
            completedTotal = swaps.find({"assignedPhase":{"$gt":9}}).count()
            alertTotal = swaps.find({"alert":1}).count()
            monitorTotal = swaps.find({"monitor":{"$gt":0}}).count()
            start24 = swaps.find({"startDate":{"$gt":previous24}}).count()
            complete24 = swaps.find({"endDate":{"$gt":previous24}}).count()
            swapBalance = subprocess.Popen([newProgramPath,programCMD_getbalance], shell=False, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip()
            await client.send_message(discord.Object(id=monitor_channel),author.mention + ',\n '+ """
**Swap Statistics**
===============
"""+"Total registered:** "+str(regTotal)+"\n"+"**Total coinswaps started:** "+str(startTotal)+"\n"+"**Total coinswaps in final stage:** "+str(finalStepTotal)+"\n"+"**Total coinswaps Completed:** "+str(completedTotal)+"\n"+"**Total users at new wallet stage:** "+str(newWalletTotal)+"\n"+"**Total users in alert mode:** "+str(alertTotal)+"\n"+"**Total users being monitored:** "+str(monitorTotal)+"\n"+"**Coinswaps started in past 24hrs:** "+str(start24)+"\n"+"**Coinswaps completed in past 24hrs:** "+str(complete24)+"**\n\n"+"Current Total Balance of Swap Wallet **"+swapBalance+"**")
            if float(swapBalance) <= balanceThreshold:
                await client.send_message(discord.Object(id=monitor_channel),'**WARNING** Bot is getting low on funds, transfer more to swap address.')  
        except Exception as e:
            print(e)
        finally:
            mc.close()
    else:
        await client.send_message(author,author.mention + ', sorry but you are not allowed to run this command.')

@swapstats.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue admin commands through DM (direct message) or from the admin channel, Thank you!')

@client.command(pass_context=True)
@in_channel(restrictChannelAdmin)
async def sweepcomplete(ctx):
    monitorValue = logCommand(ctx)
    author = ctx.message.author
    if author.id in authorized_admins:
        try:
            mc = MongoClient('localhost', 27017)
            db = mc.coinswap
            swaps = db.swaps
            userCount = 0
            for each in swaps.find({'assignedPhase':9}):
                newTxID = each['newTxID']
                txLookup = subprocess.Popen([newProgramPath,programCMD_gettransaction,str(newTxID)], shell=False, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip()
                txLookup = json.loads(txLookup)
                txConfirms = txLookup['confirmations']
                if int(txConfirms) < int(adminFinalConfirmsNeeded):
                    print('Users close but lets give them some time to finish') 
                elif int(txConfirms) >= int(adminFinalConfirmsNeeded):
                    swaps.update_one({'discordID':each['discordID']}, {'$set':{'assignedPhase':10, 'endDate':datetime.datetime.now(), 'processCompleted':1}})
                    print('Completed user '+str(each['discordID']))
                    logtime = datetime.datetime.now()
                    logfile = open("commands.log", "a+")
                    logfile.write(str(logtime)+" : "+str(each['discordID'])+" has had their process completed.\n")
                    logfile.close()
                    userCount += 1
            await client.send_message(discord.Object(id=monitor_channel),author.mention + ', Finished a total of '+str(userCount)+' users.')
        except Exception as e:
            print(e)
        finally:
            mc.close()
    else:
        await client.send_message(author,author.mention + ', sorry but you are not allowed to run this command.')

@sweepcomplete.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue admin commands through DM (direct message) or from the admin channel, Thank you!')

@client.command(pass_context=True)
@in_channel(restrictChannelAdmin)
async def duplicate(ctx, address):
    monitorValue = logCommand(ctx)
    address = cleaner(address)
    version = address[:1]
    print(version)
    author = ctx.message.author
    if author.id in authorized_admins:
        try:
            mc = MongoClient('localhost', 27017)
            db = mc.coinswap
            swaps = db.swaps
            if version == "L":
                check = checkDupAddress(address)
                if check is True:
                    cur = swaps.find_one({'swappingAddress':address})
                    owner = cur['discordID']
                    await client.say(author.mention + ', Is a duplicate old address.  Address currently belongs to discordID '+str(owner))
                else:
                    await client.say(author.mention + ', Not a duplicate old address.')
            elif version.upper() == "X":
                check = checkDupAddress(address)
                if check is True:
                    cur = swaps.find_one({'newAddress':address})
                    owner = cur['discordID']
                    await client.say(author.mention + ', Is a duplicate new address.  Address currently belongs to discordID '+str(owner))
                else:
                    await client.say(author.mention + ', Not a duplicate new address.')
            else:
                await client.say(author.mention + ', please make sure you are submitting a valid PROJECTNAME address')
        except Exception as e:
            print(e)
        finally:
            mc.close()
    else:
        await client.send_message(author,author.mention + ', sorry but you are not allowed to run this command.')

@duplicate.error
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CheckFailure):
        author = ctx.message.author
        await client.say(author.mention + ', you must issue admin commands through DM (direct message) or from the admin channel, Thank you!')
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        author = ctx.message.author
        await client.send_message(author,author.mention + ', please ensure you are including the PROJECTNAME wallet address when using **$duplicate**.')

#Function to log all commands sent
def logCommand(cmdtolog):
    logtime = datetime.datetime.now()
    logfile = open("commands.log", "a+")
    logfile.write(str(logtime)+" : "+str(cmdtolog.message.author)+" "+str(cmdtolog.message.content)+"\n")
    logfile.close()
    author = cmdtolog.message.author
    try:
        mc = MongoClient('localhost', 27017)
        db = mc.coinswap
        swaps = db.swaps
        cur = swaps.find_one({'discordID':author.id})
        if cur is not None:
            monitorValue = cur['monitor']
        else:
            monitorValue = 0
    except Exception as e:
        logException(e)
    finally:
        mc.close()
    return monitorValue;

# Function to log all exceptions
def logException(e):
    logtime = datetime.datetime.now()
    logfile = open("exceptions.log", "a+")
    logfile.write(str(logtime)+" : "+str(e)+"\n")
    logfile.close()
    return;

#Function to check for duplicate old address in the database, returns true or false
def checkDupAddress(address):
    try:
        mc = MongoClient('localhost', 27017)
        db = mc.coinswap
        swaps = db.swaps
        cur = swaps.find_one({'oldAddress':address})
        if cur is None:
            return False;
        else:
            return True;
    except Exception as e:
        print(e)
    finally:
        mc.close()

#Function to check for duplicate new address in the database, returns true or false
def checkDupAddressNew(address):
    try:
        mc = MongoClient('localhost', 27017)
        db = mc.coinswap
        swaps = db.swaps
        cur = swaps.find_one({'newAddress':address})
        if cur is None:
            return False;
        else:
            return True;
    except Exception as e:
        print(e)
    finally:
        mc.close()

#Function to log new wallet addresses registered
def logWalletAddress(msg,addresstolog):
    logtime = datetime.datetime.now()
    logfile = open("registeredaddy.log", "a+")
    logfile.write(str(logtime)+","+str(msg.message.author)+","+str(addresstolog)+"\n")
    logfile.close()
    return;

#Function to strip illegal characters from inputs
def cleaner(stripChar):
    cleaned = ''.join(e for e in str(stripChar) if e.isalnum())
    return cleaned;

#Function to determine if valid number submitted, returns true or false
def validNumber(number):
    try:
        float(number)
        return True
    except ValueError:
        return False

#Function to check if valid old-chain address
def checkOldAddress(address):
    result = subprocess.Popen([oldProgramPath,programCMD_validateaddress,str(address)], shell=False, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip()
    return result;

#Function to check if valid new-chain address
def checkNewAddress(address):
    result = subprocess.Popen([newProgramPath,programCMD_validateaddress,str(address)], shell=False, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip()
    return result;

#Function to lookup submitted OLDCOINTICKER balance
def lookupBalance(address):
    explorer_api = 'http://IQUIDUSIP:3001/ext/getbalance/'+address
    r = requests.get(explorer_api)
    balance = r.json()
    return balance;

client.run(TOKEN)