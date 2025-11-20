# Test code written for Hannah witty
# Author Stephen Witty switty@level500.com
# Test uniqueness of AI responses
#
# Original example code from rollbar.com - GPT example
# Base code from AI_Probe at level500.com
#
# V1 9-30-24 - Initial release / dev
# V2 7-31-24 - Convert to generic AI models, add save prompt to file, create secondary prompt

# Add import for needed AI model
from openai import OpenAI

import time
import sys
import os
import random

# Put API key here
key = “XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX”

# AI model below
# OpenAI model
ai_model='gpt-4o'

###################### Constants ##########################################################
NUMBER_OF_CYCLES = 100                                 # Number of cycles to run before exiting
AI_RETRY_LIMIT = 25                                    # Number of times to retry AI if errors occur
PROMPT = "How many Rs are in the word strawberry?"     # Prompt
PROMPT2 = "For the below essay, pull out a quote that exemplifies the paper's thesis. This should be a direct quote from the essay and not a paraphrase or restatement."

####### Appends text to the end of a file ###########
def write_to_file(filename, text):
   try:
      with open(filename, 'a') as f:
         f.write(text)
   except Exception as e:
      print(f"An error occurred: {e}")
      sys.exit()

########## This function creates the AI prompt #######
def create_prompt():
   prompt_message = PROMPT
   return prompt_message

########### This function formats an output string ####################
def print_string(string):
   cnt = 0
   for char in string:
      if not (char == " " and cnt == 0):
         print(char, end = "")
         cnt = cnt + 1
      if (cnt > 115 and char == " "):
         print()
         cnt = 0
   print()
   sys.stdout.flush()

############### Function - Call AI #########################################
def call_ai(prompt_message):
   try:
      client = OpenAI(api_key=key)
      completion = client.chat.completions.create(model=ai_model, messages=[ {"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": prompt_message}])

   except Exception as e:
      return False, "", "WARNING:  System Error during AI call: " + str(e)

   return True, completion.choices[0].message.content, ""

###############  Start of main routine ##############################################################
number_of_cycles = 0
ai_errors = 0

prompt_txt = PROMPT
prompt2_txt = PROMPT2

#Uncomment below if you wish to read prompt from a file
with open('prompt.txt', 'r', encoding='utf-8') as file:
    prompt_txt = file.read()

print("Starting........")
print("Prompt:")
print_string(prompt_txt)
print("Prompt 2:")
print_string(prompt2_txt)
print("Model: " + ai_model)
print("------------------------\n\n")

while(number_of_cycles < NUMBER_OF_CYCLES): # Main loop to run prompts

   retry_count = 0
   success = False # Keep running prompt until we get a valid answer to check

# This block creates the essay
   while (not success):

      if (retry_count == AI_RETRY_LIMIT):
         print("\n\nERROR: Too many AI errors, exiting\n")
         sys.exit()

      success, ai_reply, error_text = call_ai(prompt_txt) # Call AI, retry if error
      if (not success):
         print(error_text)
         retry_count = retry_count + 1
         ai_errors = ai_errors + 1
         continue

      print("***** Essay number: " + str(number_of_cycles + 1) + " ****************************\n")
      print_string(ai_reply)
      print("\n")

      write_to_file("essay.txt","\n\n\n******** Essay number: " + str(number_of_cycles + 1) + " ************\n\n")
      write_to_file("essay.txt",ai_reply)

# This blocks looks for thesis of essay
   success = False # Keep running prompt until we get a valid answer to check
   while (not success):

      if (retry_count == AI_RETRY_LIMIT):
         print("\n\nERROR: Too many AI errors, exiting\n")
         sys.exit()

      # Build these prompt with thesis question and append essay from above
      thesis_prompt = prompt2_txt + "\n\n" + ai_reply

      print(">>>>> This is the thesis  prompt with essay attached >>>>>>>\n")
      print_string(thesis_prompt)

      success, ai_reply2, error_text = call_ai(thesis_prompt) # Call AI, retry if error
      if (not success):
         print(error_text)
         retry_count = retry_count + 1
         ai_errors = ai_errors + 1
         continue

      print("\n\n\n***** Thesis number: " + str(number_of_cycles + 1) + " ****************************\n")
      print_string(ai_reply2)
      print("\n")

      write_to_file("thesis.txt","\n\n******** Thesis number: " + str(number_of_cycles + 1) + " ************\n\n")
      write_to_file("thesis.txt",ai_reply2)


# back to main outside loop 
   number_of_cycles = number_of_cycles + 1

print("\n----------- Final report -------------- ")
print("AI Prompt:")
print_string(prompt_txt)
print("AI Prompt2:")
print_string(prompt2_txt)
print("AI model: " + ai_model)

print("\nNumber of cycles: " + str(number_of_cycles))
print("AI Errors: " + str(ai_errors))
