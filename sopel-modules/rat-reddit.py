#coding: UTF-8
"""
rat-reddit.py - Fuel Rat Reddit notification module.
Copyright 2016, Justin "ZeroSteelfist" Fletchall <justin@fletchall.me>
Licensed under the Eiffel Forum License 2.
This module is built on top of the Sopel system.
http://sopel.chat/
"""
#import modules
import sopel.module
import sopel.formatting
import praw
import re
import datetime
import time

def setup(bot):
	global redditSubmissionTitle
	redditSubmissionTitle = "No Entries Yet"
	global ratsignalURL
	ratsignalURL = ""

	#control the submission iterations
	global currentPlaceInSubmissionList
	currentPlaceInSubmissionList = 1

	global numberOfNewCalls
	numberOfNewCalls = 0
	global botTalkToggle
	botTalkToggle = False

	#how the bot is identified by reddit
	user_agent = ("fuelRatChecker 0.2")
	global r
	r = praw.Reddit(user_agent = user_agent)

	#change this to pull data from another location
	global subreddit
	subreddit = r.get_subreddit("fuelrats")

	# global automaticNotificationTimer
	# automaticNotificationTimer = 60

	global redditCheckTimer
	#today = int(datetime.utcnow())
	#current_time = datetime.datetime.now(datetime.timezone.utc)
	#unix_timestamp = current_time.timestamp()
	#today = datetime.datetime.today()
	todayStamp = int(time.time())
	redditCheckTimer =  float(todayStamp) #(float(datetime.datetime.utcfromtimestamp(int(todayStamp)))) #150000 #float(unix_timestamp) - (15000000)
	#redditCheckTimer = 1500000

	global masterTalkToggle
	masterTalkToggle = True

	global signalFound
	signalFound = False

#this handles the reddit links that pass the date check below
def redditBotFunction(submission):
	""" Declare Globals """
	global redditSubmissionTitle
	global botTalkToggle
	global redditCheckTimer
	global ratsignalURL
	global numberOfNewCalls
	global automaticNotificationTimer
	global signalFound
	global currentPlaceInSubmissionList
	""" -------------- """
	ratsignalString='(Ratsignal)'	# use this for searching the post titles below
	lastPostTimestamp = datetime.datetime.fromtimestamp(int(submission.created_utc)).strftime('%Y-%m-%d %H:%M:%S')
	titleText = submission.selftext
	regExCheck = re.compile(ratsignalString,re.IGNORECASE|re.DOTALL)
	checkTitleForRatsignal = regExCheck.search(titleText)
	if checkTitleForRatsignal:
		word1=checkTitleForRatsignal.group(1)
		redditCheckTimer = (float(submission.created_utc))
		redditSubmissionTitle = submission.title
		ratsignalURL = submission.url
		botTalkToggle = True
		numberOfNewCalls += 1
		currentPlaceInSubmissionList = 99
		#this will make the next post cycle wait 5 minutes.
		#automaticNotificationTimer = 300
		signalFound = True
		print ("option one" + redditSubmissionTitle)
		#automaticNotificationTimer += 60 #add one minute to interval per Ratsignal
		#implement lastcall log
	elif (signalFound == False):
		redditSubmissionTitle = ("No new distress calls since " + lastPostTimestamp)
		botTalkToggle = False
		#automaticNotificationTimer = 120
		print ("option two")
		if (currentPlaceInSubmissionList >=9):
			#redditCheckTimer = (float(submission.created_utc))
			print ("option two plus")
		#redditCheckTimer = (float(submission.created_utc))
	elif (signalFound == True):
		signalFound = True
		print ("option three")

#limit is 2 per second or 30 per minute.
#can match it to the post frequency, minus a bit to let it run first. Too fast and it will collect data without posting it.
@sopel.module.interval((25))
def reddit_check(bot):
	""" Declare Globals """
	global currentPlaceInSubmissionList
	global numberOfNewCalls
	global signalFound
	global redditCheckTimer
	global ratsignalURL
	""" ----------- """
	signalFound = False
	numberOfNewCalls = 0
	# print (redditCheckTimer)
	# print ("-+-+-+-+-+-+-+-+")
	currentPlaceInSubmissionList = 1
	for submission in subreddit.get_new(limit = 10):
		if (((submission.created_utc) < (redditCheckTimer))): #or (currentPlaceInSubmissionList >= 9)):
			runItem = False
		elif (currentPlaceInSubmissionList <= 9):
			runItem = True
		print (str(runItem) + "\n")
		#easily compare dates using these two lines
		# print submission.created_utcint
		if ((runItem == False)): # and (float(redditCheckTimer) < (float(submission.created_utc)))):
			print (str(currentPlaceInSubmissionList) + " SKIPPED ")
			currentPlaceInSubmissionList += 1
		elif ((runItem == True) and (submission.created_utc > redditCheckTimer)):
			print ("Item Run")
			print (str(currentPlaceInSubmissionList) + " Run")
			currentPlaceInSubmissionList += 1 
			redditBotFunction(submission)

#this offers the submission title on demand			
#save the last valid call for reference. offer a url too?
#sleeps are to keep from getting kicked - limit is 3 lines per 5 seconds
@sopel.module.commands('reddit')
def check_reddit(bot, trigger):
	lastPostTimestamp = datetime.datetime.fromtimestamp(int(redditCheckTimer)).strftime('%Y-%m-%d %H:%M:%S')
	bot.msg("#rattest", redditSubmissionTitle)
	if signalFound == True:
		bot.msg("#rattest", ratsignalURL)
		if (numberOfNewCalls > 1):
			bot.msg("#rattest", "There are currently " + str(numberOfNewCalls) + " new calls.")
	time.sleep(5)

#this waits and sends a message to #FuelRats if there is a new Ratsignal on r/fuelrats
@sopel.module.interval(15)
def repetition_text(bot):
	if "#rattest" in bot.channels:
		if botTalkToggle == True:
			if masterTalkToggle == True:
				#print ("the system works, and will stay quiet if there is nothing to report.") 
				lastPostTimestamp = datetime.datetime.fromtimestamp(int(redditCheckTimer)).strftime('%Y-%m-%d %H:%M:%S')
				bot.msg("#rattest", redditSubmissionTitle)
				if signalFound == True:
					bot.msg("#rattest", ratsignalURL)
					if (numberOfNewCalls > 1):
						bot.msg("#rattest", "There are currently " + str(numberOfNewCalls) + " new calls.")
					time.sleep(300) #if there has been a ratsignal, this pauses for 5 mintues to prevent spam.


""" These next functions control the masterTalkToggle boolean"""
@sopel.module.commands('silence')
def silent_reddit_bot(bot, trigger):
	global masterTalkToggle
	if masterTalkToggle == True:
		bot.msg("#rattest", "Reddit bot muted.")
		masterTalkToggle = False
	elif masterTalkToggle == False:
		masterTalkToggle = True
		bot.msg("#rattest", "Reddit bot unmuted.")
	else:
		bot.msg("#rattest", "There is a problem with my notification toggle. Contact FR Tech Support.")
	time.sleep(5)

@sopel.module.commands('silenceon')
def mute_reddit_bot(bot, trigger):
	global masterTalkToggle
	if masterTalkToggle == True:
		bot.msg("#rattest", "Reddit bot muted.")
		masterTalkToggle = False
	else:
		bot.msg("#rattest", "Already muted.")
	time.sleep(5)

@sopel.module.commands('silenceoff')
def unmute_reddit_bot(bot, trigger):
	global masterTalkToggle
	if masterTalkToggle == False:
		masterTalkToggle = True
		bot.msg("#rattest", "Reddit bot unmuted.")
	else:
		bot.msg("#rattest", "Already squeaking.")
	time.sleep(5)
