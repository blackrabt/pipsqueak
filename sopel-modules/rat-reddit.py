#coding: utf8
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

#compare current and past entry titles and times with these
#TO-DO rewrite this to not use globals and instead pass values between functions
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
r = praw.Reddit(user_agent = user_agent)

#change this to pull data from another location
subreddit = r.get_subreddit("fuelrats")

global automaticNotificationTimer
automaticNotificationTimer = 60

global redditCheckTimer
redditCheckTimer = 0.0 #(float(datetime.datetime.utcfromtimestamp(todayStamp)))

global masterTalkToggle
masterTalkToggle = True


#this will run at the module initialization to set the first comparison date
def setup(bot):
	for submission in subreddit.get_new(limit =1):
		global redditCheckTimer
		global redditSubmissionTitle
		redditCheckTimer = submission.created_utc
		lastPostTimestamp = datetime.datetime.fromtimestamp(int(submission.created_utc)).strftime('%Y-%m-%d %H:%M:%S')
		redditSubmissionTitle = ("No new distress calls since " + lastPostTimestamp)

#this handles the reddit links that pass the date check below
def redditBotFunction(submission):
	ratsignalString='(Ratsignal)'	# use this for searching the post titles below
	lastPostTimestamp = datetime.datetime.fromtimestamp(int(submission.created_utc)).strftime('%Y-%m-%d %H:%M:%S')
	global currentPlaceInSubmissionList
	global redditSubmissionTitle
	global botTalkToggle
	global redditCheckTimer
	global ratsignalURL
	global numberOfNewCalls
	global automaticNotificationTimer
	titleText = submission.selftext
	regExCheck = re.compile(ratsignalString,re.IGNORECASE|re.DOTALL)
	checkTitleForRatsignal = regExCheck.search(titleText)
	currentPlaceInSubmissionList += 1
	if checkTitleForRatsignal:
		word1=checkTitleForRatsignal.group(1)
		#set current place to 6 so it will not overwrite the valid distress call
		currentPlaceInSubmissionList = 6			    	
		redditCheckTimer = (float(submission.created_utc))
		redditSubmissionTitle = submission.title
		ratsignalURL = submission.url
		botTalkToggle = True
		numberOfNewCalls += 1
		#this will make the next post cycle wait 5 minutes.
		automaticNotificationTimer = 300

		#automaticNotificationTimer += 60 #add one minute to interval per Ratsignal
		#implement lastcall log
	elif (currentPlaceInSubmissionList == 5):
		redditSubmissionTitle = ("No new distress calls since " + lastPostTimestamp)
		botTalkToggle = False
		automaticNotificationTimer = 120

#limit is 2 per second or 30 per minute.
#can match it to the post frequency, minus a bit to let it run first. Too fast and it will collect data without posting it.
@sopel.module.interval((automaticNotificationTimer - 10))
def reddit_check(bot):
	global currentPlaceInSubmissionList
	global numberOfNewCalls
	numberOfNewCalls = 0
	currentPlaceInSubmissionList = 1
	for submission in subreddit.get_new(limit = 5):
		global redditCheckTimer
		global ratsignalURL
		#easily compare dates using these two lines
		# print submission.created_utc
		print redditCheckTimer
		if float(submission.created_utc) <= float(redditCheckTimer):
			if (currentPlaceInSubmissionList == 5):
				ratsignalURL = ""
			#print "Item Skipped"
			#print currentPlaceInSubmissionList
			currentPlaceInSubmissionList += 1
			break
		else:
			#print "Item Run"
			redditBotFunction(submission)

#this offers the submission title on demand			
#save the last valid call for reference. offer a url too?
@sopel.module.commands('reddit')
def check_reddit(bot, trigger):
	lastPostTimestamp = datetime.datetime.fromtimestamp(int(redditCheckTimer)).strftime('%Y-%m-%d %H:%M:%S')
	bot.msg("#rattest", redditSubmissionTitle)
	bot.msg("#rattest", ratsignalURL)
	if (numberOfNewCalls > 1):
		bot.msg("#rattest", "There are currently " + str(numberOfNewCalls) + " new calls.")

#this waits and sends a message to #FuelRats if there is a new Ratsignal on r/fuelrats
@sopel.module.interval(automaticNotificationTimer)
def repetition_text(bot):
	if "#rattest" in bot.channels:
		if botTalkToggle == True:
			if masterTalkToggle == True:
				#the system works, and will stay quiet if there is nothing to report. 
				lastPostTimestamp = datetime.datetime.fromtimestamp(int(redditCheckTimer)).strftime('%Y-%m-%d %H:%M:%S')
				bot.msg("#rattest", redditSubmissionTitle)
				bot.msg("#rattest", ratsignalURL)
				if (numberOfNewCalls > 1):
					bot.msg("#rattest", "There are currently " + str(numberOfNewCalls) + " new calls.")

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

@sopel.module.commands('silenceon')
def mute_reddit_bot(bot, trigger):
	global masterTalkToggle
	if masterTalkToggle == True:
		bot.msg("#rattest", "Reddit bot muted.")
		masterTalkToggle = False
	else:
		bot.msg("#rattest", "Already muted.")


@sopel.module.commands('silenceoff')
def unmute_reddit_bot(bot, trigger):
	global masterTalkToggle
	if masterTalkToggle == False:
		masterTalkToggle = True
		bot.msg("#rattest", "Reddit bot unmuted.")
	else:
		bot.msg("#rattest", "Already squeaking.")
