import re
from collections import defaultdict
from typing import Pattern
import spacy
import random

dst = defaultdict(list)

def nlu(input=""):
    # [YOUR CODE HERE]
    # load in spacy's english model
    nlp = spacy.load("en_core_web_sm")

    # index, slot:
    # 0, yes/no states
    # 1, time
    # 2, date
    # 3, frequency
    # 4, determine_correction
    reg_expressions = [r"([Yy]es)|([Nn]o)", 
                        r"[0-9]{1,2}:[0-9]{2}", 
                        r"([A-Z][a-z]+[\s]{1}[0-9]{1,2})|(today)|(tonight)|(tomorrow)", 
                        r"(once|every)(\s[a-z]+)*",
                        r"([Tt]itle|[Dd]escription|[Tt]ime|[Dd]ate|[Ff]requency)"]

    slots_and_values = []

    # retrieve the last state that was visited
    num_states = len(dst["dialogue_state_history"])
    last_state = dst["dialogue_state_history"][num_states-1]
    # if the chatbot has to repeat any of the states
    if last_state == 'ask_again':
        # use the state that has to be repeated again to find if the input is valid
        last_state = dst['ask_again']

    # if the input does not provide a valid value, then we add the state that needs to be repeated to 'repeat'
    repeat = []

    # states that accept 'yes' or 'no' responses - shortens if-statements
    yes_no_states = ['ask_description', 'ask_confirmation', 'new_reminder', 'correction']

    # chatbot asked a yes/no question
    if last_state in yes_no_states:
        pattern = re.compile(reg_expressions[0])
        match = re.search(pattern, input)
        # if any variation of 'yes' or 'no' is found
        if match:
            if last_state == 'correction':
                # the user indicated whether or not he/she approves the correction
                slots_and_values.append(('correction_accepted', str(match.group(0)).lower()))
            elif last_state == 'ask_description':
                # print('-- nlu - last state was ask_description')
                # print('-- nlu - input was: ', input)
                # if the user responded that he/she does not want to add a description
                if input.lower() == 'no':
                    # print('-- nlu - adding the empty description')
                    # put in a temporary description in dicating that the chatbot asked for a description
                    # but the user decided to not add one
                    # update_dst([('description', '-')])
                    slots_and_values.append(('description', '-'))
                slots_and_values.append((last_state, str(match.group(0)).lower()))
            elif last_state == 'ask_confirmation':
                slots_and_values.append(('confirmation', str(match.group(0)).lower()))
            else:
                slots_and_values.append((last_state, str(match.group(0)).lower()))
        # no match
        else:
            repeat.append(last_state)
    # chatbot asked for title of the reminder
    elif last_state == 'greeting':
        # prompts:
        # - 'Hello! What would you like me to remind you about?'
        # - 'Hello! What would you like to title this reminder?'
        # expecting something about an event
        # tokenize the input with POS-tagging
        tokens = nlp(input)
        # used to store the parts of the title
        title_arr = []

        for t in tokens:
            # print(t.text, t.pos_, t.dep_)
            if t.pos_ == 'NOUN':
                title_arr.append(str(t))
            if t.pos_ == 'ADP':
                if t.text == 'with':
                    title_arr.append(str(t))

        title = ' '.join(k for k in title_arr)
        slots_and_values.append(('title', title))
    elif last_state == 'set_description':
        # assume that the user's response is the complete description
        # the user indicated that he/she wants a description
        slots_and_values.append(('description', input))
    # chatbot asked for the time
    elif last_state == 'ask_time':
        # expecting a time in a X:XX or XX:XX format
        reg_time = re.compile(reg_expressions[1])
        match = re.search(reg_time, input)
        if match:
            slots_and_values.append(('time', match.group(0)))
        else:
             repeat.append(last_state)
    # chatbot asked for the date
    elif last_state == 'ask_date':
        # expecting a date in a MONTH DAY format
        pattern = re.compile(reg_expressions[2])
        match = re.search(pattern, input)
        if match:
            slots_and_values.append(('date', match.group(0)))
        else:
            repeat.append(last_state)
    elif last_state == 'ask_frequency':
        # Prompts:
        # - 'How frequently would you like to be reminded leading up the event?'
        # - 'Leading up the event, how often would you like to be reminded?'
        # expecting "once ..." or "every ..."
        pattern = re.compile(reg_expressions[3])
        match = re.search(pattern, input)
        if match:
            slots_and_values.append(('frequency', str(match.group(0)).lower()))
        else:
            repeat.append(last_state)
    elif last_state == 'determine_correction':
        # prompts:
        # - 'I\'m sorry. What would you like to correct?'
        # - 'Oh. What needs to be corrected?'
        # expecting a slot name
        pattern = re.compile(reg_expressions[4])
        match = re.search(pattern, input)
        if match:
            slots_and_values.append(('to_correct', str(match.group(0)).lower()))
        else:
            repeat.append(last_state)
    elif last_state == 'new_value':
        # reprompted to input a slot value
        # expecting a valid input corresponding to the slot that is being changed
        if dst['to_correct'] == 'title':
            # tokenize the input with POS-tagging
            tokens = nlp(input)
            # used to store the parts of the title
            title_arr = []

            for t in tokens:
                # print(t.text, t.pos_, t.dep_)
                if t.pos_ == 'NOUN':
                    title_arr.append(str(t))
                if t.pos_ == 'ADP':
                    if t.text == 'with':
                        title_arr.append(str(t))

            title = ' '.join(k for k in title_arr)
            slots_and_values.append(('title', title))
        elif dst['to_correct'] == 'description':
            slots_and_values.append(('description', input))
        elif dst['to_correct'] == 'date':
            pattern = re.compile(reg_expressions[2])
            match = re.search(pattern, input)
            if match:
                slots_and_values.append(('date', str(match.group(0)).lower()))
            else:
                repeat.append(last_state)
        elif dst['to_correct'] == 'time':
            pattern = re.compile(reg_expressions[1])
            match = re.search(pattern, input)
            if match:
                slots_and_values.append(('time', str(match.group(0)).lower()))
            else:
                repeat.append(last_state)
        elif dst['to_correct'] == 'frequency':
            pattern = re.compile(reg_expressions[3])
            match = re.search(pattern, input)
            if match:
                slots_and_values.append(('frequency', str(match.group(0)).lower()))
            else:
                repeat.append(last_state)
    # a state needs to be repeated
    if len(repeat) != 0:
        slots_and_values.append(('ask_again', repeat))
    return slots_and_values

# update_dst(input): Updates the dialogue state tracker
# Input: A list ([]) of (slot, value) pairs.  Slots should be strings; values can be whatever is
#        most appropriate for the corresponding slot.  Defaults to an empty list.
# Returns: Nothing
def update_dst(input=[]):
	# [YOUR CODE HERE]
    # Definition of slots and permissable values -----------------------------------------------------------------
    # Slot:             Permissable values:
    # 'title'           string (ex: 'exam', 'finish homework')
    # 'description'     string (ex: 'CS 421', 'NLP')
    # 'time             string (ex: "4:30", "12:34", etc.)
    # 'date'            string (ex: "August 21", "March 1", "today", "tomorrow", etc.)
    # 'freqency'        string (ex: "once a week", "once", "every other day", etc.)
    # 'confirmation'    string ("yes" or "no")
    # 'new_reminder'    string ("yes" or "no")
    # 'to_correct'      string (one of the first 6 slots mentioned above) (ex: 'time', 'date', 'title', etc.)
    # 'ask_description' string ("yes" or "no")
    # 'correction'      string ("yes" or "no")
    # -------------------------------------------------------------------------------------------------------------

    # iterate through the pairs in input
    for i in input:
        valid = False
        slot = i[0]
        value = i[1]
        # check if the value is valid
        if slot == 'title':
            valid = True
        elif slot == 'description':
            valid = True
        elif slot == 'time':
            valid = True
        elif slot == 'date':
            valid = True
        elif slot == 'frequency':
            valid = True
        elif slot == 'ask_description' or slot == "confirmation" or slot == "new_reminder" or slot == "correction_accepted":
            value = value.lower()
            if value == 'yes' or value == 'no':
                valid = True
        elif slot == 'to_correct':
            slots = ['title', 'description', 'date', 'time', 'frequency']
            value = value.lower()
            if value in slots:
                valid = True
        elif slot == 'ask_again':
            valid = True
        # store the value if it is valid
        if valid:
            # use the first value of the pair to access the slot
            dst[i[0]] = i[1] # fill in the value


# get_dst(slot): Retrieves the stored value for the specified slot, or the full dialogue state at the
#                current time if no argument is provided.
# Input: A string value corresponding to a slot name.
# Returns: A dictionary representation of the full dialogue state (if no slot name is provided), or the
#          value corresponding to the specified slot.
def get_dst(slot=""):
    # [YOUR CODE HERE]
    # no slot is provided
    if slot == "":
        # return the full dialogue state
        return dst
    # a slot is specified
    else:
        # return the values from the slot
        return dst[slot]


def determine_next_state(prev_state, dst):
    # initialize the next_state and the list of slot-value pairs
    next_state = 'ask_again'
    pairs = []

    # check if there is a valid value in the slot now
    # if valid, len(dst[state]) should not be 0
    # coming from: 'greeting' ----------------------------------
    if prev_state == 'greeting':
        # title is set
        if len(dst['title']) != 0:
            # move to next state
            next_state = 'ask_description'
    # coming from: 'ask_description' ---------------------------
    elif prev_state == 'ask_description':
        # the user responded indicating whether or not he/she wants to add a description
        if len(dst['ask_description']) != 0:
            if dst['ask_description'] == 'yes':
                next_state = 'set_description'
            else:
                # skip the 'set_description' state
                next_state = 'ask_date'
    # coming from: 'set_description' ---------------------------
    elif prev_state == 'set_description':
        next_state = 'ask_date'
     # coming from: 'ask_date' ----------------------------------
    elif prev_state == 'ask_date':
        # date was valid
        if len(dst['date']) != 0:
            next_state = 'ask_time'
    # coming from: 'ask_time' ----------------------------------
    elif prev_state == 'ask_time':
        # time was valid
        if len(dst['time']) != 0:
            next_state = 'ask_frequency'
    # coming from: 'ask_frequency' -----------------------------
    elif prev_state == 'ask_frequency':
        # frequency was valid
        if len(dst['frequency']) != 0:
            next_state = 'ask_confirmation'
            pairs = [('title', get_dst("title")), 
                    ('description', get_dst("description")), 
                    ('date', get_dst("date")), 
                    ('time', get_dst("time")), 
                    ('frequency', get_dst("frequency"))]
    # coming from: 'ask_confirmation' --------------------------
    elif prev_state == 'ask_confirmation':
        # a confirmation value was set
        if len(dst['confirmation']) != 0:
            # the user accepts the values of the reminder
            if dst["confirmation"] == 'yes':
                # move on to asking if the user wants to create a new reminder
                next_state = 'new_reminder'
            # user entered 'no' - does not accept the values
            else:
                next_state = 'determine_correction'
                pairs = [('title', get_dst("title")), 
                    ('description', get_dst("description")), 
                    ('date', get_dst("date")), 
                    ('time', get_dst("time")), 
                    ('frequency', get_dst("frequency"))]
    # coming from: 'new_reminder' ------------------------------
    elif prev_state == 'new_reminder':
        if len(dst['new_reminder']) != 0:
            if dst['new_reminder'] == 'yes':
                # start from the beginning ------------------------------------------------------------------- TODO
                dst.clear()
                next_state = 'greeting'
            else:
                # finish the program
                next_state = 'end_state'
    # coming from: 'determine_correction' ----------------------
    elif prev_state == 'determine_correction':
        # the user determined which part of the reminder he/she would like to change
        if len(dst['to_correct']) != 0:
            # store the slot that the user wants to change
            correction_slot = get_dst('to_correct')
            # reset the value that is going to change
            dst[correction_slot] = ''
            next_state = 'new_value'
    # coming from: 'new_value' ---------------------------------
    elif prev_state == 'new_value':
        # if the new value was accepted
        if get_dst(dst['to_correct']) != '':
            next_state = 'correction'
    # coming from: 'correction' --------------------------------
    elif prev_state == 'correction':
        if len(dst['correction_accepted']) != 0:
            if get_dst('correction_accepted') == 'yes':
                next_state = 'new_reminder'
            # the corrections were not accepted
            else:
                # reset the correction values 
                dst['to_correct'] = ''
                dst['correction_accepted'] = ''
                next_state = 'determine_correction'

    # at this point, the next_state variable is updated
    # push the next state to the history and continue
    dst["dialogue_state_history"].append(next_state)
    return next_state, pairs, dst

# dialogue_policy(dst): Selects the next dialogue state to be uttered by the chatbot.
# Input: A dictionary representation of a full dialogue state.
# Returns: A string value corresponding to a dialogue state, and a list of (slot, value) pairs necessary
#          for generating an utterance for that dialogue state (or an empty list of no (slot, value) pairs
#          are needed).
def dialogue_policy(dst=[]):
	# [YOUR CODE HERE]
    # Q1 Written -------------------------------------------------------------------------------------------------
    # Possible States: 
    # Greeting                          -> 'greeting' - greets the user and receives a title when the user responds
    # Add Description                   -> 'ask_description' - asks the user if he/she would like to add a description
    #                                                         to the reminder
    # Set Description                   -> 'set_description' - prompt the user to provide a description
    # Date                              -> 'ask_date' - prompts the user to enter a date for the reminder
    # Time                              -> 'ask_time' - prompts the user to enter a time for the reminder 
    # Frequency of reminder             -> 'ask_frequency' - prompts the user to specify how often he/she would like
    #                                                        to be reminded prior to the event
    # Confirmation                      -> 'ask_confirmation' - presents the user with a complete summary of the reminder and asks
    #                                                       if it is correct
    # Determine correction              -> 'determine_correction' - prompts the user to specify which slot needs to be changed
    # New value                         -> 'new_value' - prompts the use to provide a new value for the specified slot 
    # Correction                        -> 'correction' - prompts the user with the updated reminder info
    # New Reminder                      -> 'new_reminder' - asks the user if he/she would like to create another reminder
    # End State                         -> 'end_state' - thanks the user for using the chatbot and says goodbye
    # -------------
    # ask again                         -> 'ask_again' - asks the user to provide valid input
    #                                                  - provides the user with a hint as to what is considered valid input
    # ------------------------------------------------------------------------------------------------------------
    # extract the dialogue history for easier access
    bot_history = dst["dialogue_state_history"]
    # print('-- dialogue_policy - History: ', bot_history)

    # nothing has happened yet - starting with greeting
    if len(bot_history) == 0:
        dst["dialogue_state_history"].append("greeting")
        return "greeting", []
    # continuing the conversation
    else:
        # store the most recent state for the bot's history for later use
        last_bot_state = bot_history[len(bot_history)-1]
        next_state = ''

        # the bot asked the user to re-input an answer
        if last_bot_state == 'ask_again':
            # look at what the bot originally asked before asking the user to repeat
            count = len(bot_history) - 2 
            prev_state = bot_history[len(bot_history)-2] # storing second to last state in case it doesn't go into while loop
            # backtrack through the history to find the original prompt
            while prev_state == 'ask_again':
                prev_state = bot_history[count]
                count -= 1
            next_state, slots, dst = determine_next_state(prev_state, dst)
            # going to the ask_again state again
            if next_state == 'ask_again':
                update_dst([('ask_again', prev_state)])
                return next_state, [(prev_state, "")]
            else:
                return next_state, slots
        # bot is in its end state 
        elif last_bot_state == 'end_state':
            # flag the end of the program
            dst["dialogue_state_history"].append("terminate")
            return "terminate", []
        # the conversation continues
        else:
            next_state, slots, dst = determine_next_state(last_bot_state, dst)
            if next_state == 'ask_again':
                update_dst([('ask_again', last_bot_state)])
                # pass back the next state but also the original state before the ask_again state
                return next_state, [(last_bot_state, "")]
            else:
                return next_state, slots

 # helper function for nlg()
 # input: none
 # output: a dictionary of utterance templates
def create_nlg_templates():
    templates = defaultdict(list)

    templates['greeting'] = ['Hello! What would you like me to remind you about?', 
                            'Hello! What would you like to title this reminder?']

    templates['ask_description'] = ['Would you like to add a description to this reminder?',
                                    'Okay, would you like to add a description?']

    templates['set_description'] = ['What would you like the description to be?',
                                    'Okay so what would you like the description to be?']

    templates['ask_time'] = ['What time would you like the reminder to be set to?', 
                            'To what time would you like to set the reminder?']

    templates['ask_date'] = ['And what is the date of the reminder?', 
                            'On what date would you like to be reminded?']

    templates['ask_frequency'] = ['How frequently would you like to be reminded leading up the event?', 
                                'Leading up the event, how often would you like to be reminded?']

    templates['ask_confirmation'] = []
    # description, freqency - 0
    templates["ask_confirmation"].append('Okay, I will set your reminder for <title> at <time> <on date>. The description you added: <description>. You will be reminded <frequency>. Is this correct?')
    # no description, freqency - 1
    templates["ask_confirmation"].append('Okay, I will set your reminder for <title> at <time> <on date>. You will be reminded <frequency>. Is this correct?')
    # description, no freqency - 2
    templates["ask_confirmation"].append('Okay, I will set your reminder for <title> at <time> <on date>. The description you added: <description>. You will not be notified leading up to <title>. Is this correct?')
    # no description, no freqency - 3
    templates["ask_confirmation"].append('Okay, I will set your reminder for <title> at <time> <on date>. You will not be reminded in the time leading up to <title>. Is this correct?')
    
    templates['determine_correction'] = ['I\'m sorry. What would you like to correct?', 
                                        'Oh. What needs to be corrected?']

    templates['new_value'] = []
    # title was wrong
    templates['new_value'].append('Okay, what would you like to like the new title to be?')
    # description was wrong
    templates['new_value'].append('Okay, what would you like to like the new description to be?')
    # time was wrong
    templates['new_value'].append('Okay, what would you like to like the new time to be?')
    # date was wrong
    templates['new_value'].append('Okay, what would you like to like the new date to be?')
    # freqency was wrong
    templates['new_value'].append('Okay, how often would you like to reminded instead?')
    # notification was wrong
    templates['new_value'].append('Okay, how much time before the event would you like to be notified?')

    templates['correction'] = []
    # description, freqency - 0
    templates["correction"].append('Okay, I will set your reminder for <title> at <time> <on date>. The description you added: <description>. You will be reminded <frequency>. Is this correct?')
    # no description, freqency - 1
    templates["correction"].append('Okay, I will set your reminder for <title> at <time> <on date>. You will be reminded <frequency>. Is this correct?')
    # description, no freqency - 2
    templates["correction"].append('Okay, I will set your reminder for <title> at <time> <on date>. The description you added: <description>. Is this correct?')
    # description, freqency - 3
    templates["correction"].append('Okay, I will set your reminder for <title> at <time> <on date>. You will be reminded <frequency>. Is this correct?')
    
    templates['new_reminder'] = ['Great! Would you like to create a new reminder?', 
                                'Perfect! Is there anything else I can remind you about?']

    templates['end_state'] = ['No problem! Thank you for letting me assist you.', 
                            'Have a good day!']

    templates['ask_again'] = []
    # ask user for valid title
    templates['ask_again'].append('I didn\'t catch that. Could you please provide a valid title?')
    # ask user for valid description
    templates['ask_again'].append('Sorry, I didn\'t catch that. Please provide a valid description.')
    # ask user for valid time
    templates['ask_again'].append('Sorry, that time is not valid. Please enter a time in the following format: \'XX:XX\' or \'X:XX\' followed by \'am\' or \'pm\'.')
    # ask user for valid date
    templates['ask_again'].append('Sorry, that is not a valid date. Please provide a month and a day or a relative day such as \'today\' or \'tomorrow\'.')
    # ask user for valid frequency
    templates['ask_again'].append('Sorry, that is not a valid input. Some examples of valid input are: \'once,\' \'once a week,\' and \'every other day\'.')
    # ask user for valid confirmation answer
    templates['ask_again'].append('I\'m sorry, I didn\'t catch that. Please respond with either \'yes\' or \'no\'.')
    # ask user for valid slot to correct
    templates['ask_again'].append('I\'m sorry, that\'s not a valid slot. Please respond with one of the following: \'title,\' \'description,\' \'time,\' \'date,\' or \'freqency of reminder\'.')

    return templates

# nlg(state, slots=[]): Generates a surface realization for the specified dialogue act.
# Input: A string indicating a valid state, and optionally a list of (slot, value) tuples.
# Returns: A string representing a sentence generated for the specified state, optionally
#          including the specified slot values if they are needed by the template.
def nlg(state, slots=[]):
    # [YOUR CODE HERE]
    # if the templates subdictionary does not exist yet
    if "templates" not in dst.keys():
        # call create_nlg_templates() to create the templates
        dst["templates"] = create_nlg_templates()

    # return a template
    output = ''
    if state == 'greeting':
        output = dst['templates'][state][random.randrange(0,2)]
    elif state == 'ask_description':
        output = dst['templates'][state][random.randrange(0,2)]
    elif state == 'set_description':
        output = dst['templates'][state][random.randrange(0,2)]
    elif state == 'ask_date':
        output = dst['templates'][state][random.randrange(0,2)]
    elif state == 'ask_time':
        output = dst['templates'][state][random.randrange(0,2)]
    elif state == 'ask_frequency':
        output = dst['templates'][state][random.randrange(0,2)]
    elif state == 'ask_confirmation' or state == 'correction':
        date_val = ''
        date = get_dst('date')
        if date == 'today' or date == 'tomorrow' or date == 'tonight':
            date_val = date
        else:
            date_val = 'on ' + date

        # user entered a description - (description,_)
        if dst['description'] != '-':
            # user wants to be reminded throughout the time leading to the event - (description, frequency)
            if dst['frequency'] != 'once':
                output = dst['templates'][state][0]
                # replace the '<X>' parts of the template with the corresponding values
                output = output.replace('<title>', get_dst('title'))
                output = output.replace('<time>', get_dst('time'))
                output = output.replace('<on date>', date_val)
                output = output.replace('<description>', get_dst('description'))
                output = output.replace('<frequency>', get_dst('frequency'))
            # (description, no frequency)
            else:
                output = dst['templates'][state][2]
                output = output.replace('<title>', get_dst('title'))
                output = output.replace('<time>', get_dst('time'))
                output = output.replace('<on date>', date_val)
                output = output.replace('<description>', get_dst('description'))
        # (no description,_)
        else:
            # user wants to be reminded throughout the time leading to the event - (no description, frequency)
            if dst['frequency'] != 'once':
                # (no description, frequency)
                output = dst['templates'][state][1]
                output = output.replace('<title>', get_dst('title'))
                output = output.replace('<time>', get_dst('time'))
                output = output.replace('<on date>', date_val)
                output = output.replace('<frequency>', get_dst('frequency'))
            # (no description, no frequency)
            else:
                output = dst['templates'][state][3]
                output = output.replace('<title>', get_dst('title'))
                output = output.replace('<time>', get_dst('time'))
                output = output.replace('<on date>', date_val)
    elif state == 'determine_correction':
        output = dst['templates'][state][random.randrange(0,2)]
    elif state == 'new_value':
        if dst['to_correct'] == 'title':
            output = dst['templates'][state][0]
        elif dst['to_correct'] == 'description':
            output = dst['templates'][state][1]
        elif dst['to_correct'] == 'time':
            output = dst['templates'][state][2]
        elif dst['to_correct'] == 'date':
            output = dst['templates'][state][3]
        elif dst['to_correct'] == 'frequency':
            output = dst['templates'][state][4]
        elif dst['to_correct'] == 'notification':
            output = dst['templates'][state][5]
    elif state == 'new_reminder':
        output = dst['templates'][state][random.randrange(0,2)]
    elif state == 'end_state':
        output = dst['templates'][state][random.randrange(0,2)]
    elif state == 'ask_again':
        # look at what was the last thing in the history before any ask_again state
        prev_state = slots[0][0] # pull out the first slot's first value, which is the last state before ask_again
        if prev_state == 'greeting':
            output = dst['templates'][state][0]
        elif prev_state == 'set_description':
            output = dst['templates'][state][1]
        elif prev_state == 'ask_time':
            output = dst['templates'][state][2]
        elif prev_state == 'ask_date':
            output = dst['templates'][state][3]
        elif prev_state == 'ask_frequency':
            output = dst['templates'][state][4]
        elif prev_state == 'confirmation':
            output = dst['templates'][state][5]
        elif prev_state == 'determine_correction':
            output = dst['templates'][state][6]
    else:
        output = 'SOMETHING WENT WRONG'

    return output

# prints out a given utterance with a 'Bot' or 'User' tag to indicate who the utterance came from
# if continuing is provided and is true, it indicates that the conversation is continuing so the 
# 'user: ' tag will be printed in anticipation for the user's response
def printUtterance(utterance, continuing=False):
    print('Bot: ', utterance)
    # expecting a response
    if continuing:
        print('User: ', end='')

def main():
    # call dialogue_policy() to create the dialogue state history and intialize it with 'greeting'
    dst = get_dst()
    dst["dialogue_state_history"] = []
    # print('dst: ', dst)
    next_state, slots = dialogue_policy(dst)

    while True:
        # create an utterance for the state
        utterance = nlg(next_state, slots)

        # display the utterance for the user
        if next_state != 'end_state':
            printUtterance(utterance, True)
            # take in input
            user_input = input()

            # parse the input for slot-values
            slot_values = nlu(user_input)
            # print('- Main - extracted from input: ', slot_values)

            update_dst(slot_values)

            # print('- Main - dst after updating:')
            # for k in dst.keys():
            #     if k != 'templates':
            #         print('--- ', k , ': ', dst[k])

            # determine what the next state is
            next_state, slots = dialogue_policy(get_dst())
            # print('- Main - next state will be: ', next_state)
        else:
            # printing the last utterance of the chatbot
            printUtterance(utterance, False)
            break
        

################ Do not make any changes below this line ################
if __name__ == '__main__':
    main()