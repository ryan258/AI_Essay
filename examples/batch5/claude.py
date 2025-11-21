# Test code written for Hannah witty
# Author Stephen Witty switty@level500.com
# Test uniqueness of AI responses
#
# Original example code from rollbar.com - GPT example
# Base code from AI_Probe at level500.com
#
# V1 9-30-24 - Initial release / dev
# V2 7-31-25 - Convert to generic AI models, add save prompt to file, create secondary prompt
# V3 9-12-25 - Read essays in and then combine each essay with the prmopt from a file 

# Add import for needed AI model
#from openai import OpenAI #OpenAi
#from google import genai #Gemini
#from google.genai import types #Gemini
import anthropic #Claude import
#from xai_sdk import Client #Grok import
#from xai_sdk.chat import user,system #Grok import

import time
import sys
import os
import random

# Put API key here
key = “XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX”

# AI model below
#ai_model='gpt-4o' #OpenAI model
#ai_model="gemini-2.5-flash" #Gemini model
ai_model="claude-sonnet-4-20250514" #Claude model
#ai_model="grok-3-fast" # Grok model

###################### Constants ##########################################################
NUMBER_OF_CYCLES = 100                                # Number of cycles to run before exiting
AI_RETRY_LIMIT = 25                                    # Number of times to retry AI if errors occur
PROMPT = "In one or two words state the topic of the below essay. For example, if the essay is about learning to write, then you would say that the topic of the essay is \"writing.\" This can be applied to other topics, such as but not limited to: \"public speech,\" \"dance,\" \"reading,\" or \"public performance.\""     # Prompt
#PROMPT2 = "For the below essay, pull out a quote that exemplifies the paper's thesis. This should be a direct quote from the essay and not a paraphrase or restatement."

####### Appends text to the end of a file ###########
def write_to_file(filename, text):
   try:
      with open(filename, 'a') as f:
         f.write(text)
   except Exception as e:
      print(f"An error occurred: {e}")
      sys.exit()

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

#  OpenAI ############## Function - Call AI #########################################
#def call_ai(prompt_message):
#   try:
#      client = OpenAI(api_key=key)
#      completion = client.chat.completions.create(model=ai_model, messages=[ {"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": prompt_message}])
#
#   except Exception as e:
#      return False, "", "WARNING:  System Error during AI call: " + str(e)
#
#   return True, completion.choices[0].message.content, ""


#  Gemini ############## Function - Call AI #########################################
#def call_ai(prompt_message):
#   try:
#      client = genai.Client(api_key=key)
#      response = client.models.generate_content(
#      model=ai_model,
#      contents=prompt_message,
#      config=types.GenerateContentConfig(
#        thinking_config=types.ThinkingConfig(thinking_budget=0)),)

#   except Exception as e:
#      return False, "", "WARNING:  System Error during AI api  call: " + str(e)

#   return True, response.text, ""

#  Claude ############# Function - Call AI ##############
def call_ai(prompt_message):
   try:
      client = anthropic.Anthropic(api_key=key)

      message = client.messages.create(
         model="claude-opus-4-20250514",
         max_tokens=1000,
         temperature=1,
         system="You are a helpful assistant.",
         messages=[
            {
                  "role": "user",
                  "content": [
                     {
                        "type": "text",
                        "text": prompt_message
                     }
                  ]
            }
         ]
      )

   except Exception as e:
      return False, "", "WARNING:  System Error during AI api  call: " + str(e)

   return True, message.content[0].text, ""

#def call_ai(prompt_message):
#   try:
#      client = Client(api_key=key)
#      chat = client.chat.create(model=ai_model)
#      chat.append(system("You are Grok, a highly intelligent, helpful AI assistant."))
#      chat.append(user(prompt_message))

#      response = chat.sample()

#   except Exception as e:
#      return False, "", "WARNING:  System Error during AI api  call: " + str(e)

#   return True, response.content, ""


def extract_essay(filename, target_number):
   essay = ""
   found_essay=False
   found_one=False

   with open(filename, "r", encoding="utf-8") as f:
      for line in f:
         if line.startswith("******** Essay number: " + str(target_number) + " ************"):
            found_essay=True
            found_one=True
            continue

         if (found_essay==True and line.startswith("******** Essay number: ")):
            found_essay=False
            continue

         if (found_essay==True):
            essay = essay + line

   if (found_one==False):
      print("\n\nERROR: Essay not found, exiting, essay number: " + str(target_number))
      sys.exit()

   return essay

###############  Start of main routine ##############################################################
number_of_cycles = 0
ai_errors = 0

prompt_txt = PROMPT
#prompt2_txt = PROMPT2

#Uncomment below if you wish to read prompt from a file
#with open('prompt.txt', 'r', encoding='utf-8') as file:
#    prompt_txt = file.read()

print("Starting........")
print("Prompt:")
print_string(prompt_txt)
#print("Prompt 2:")
#print_string(prompt2_txt)
print("Model: " + ai_model)
print("------------------------\n\n")


while(number_of_cycles < NUMBER_OF_CYCLES): # Main loop to run prompts

   retry_count = 0
   success = False # Keep running prompt until we get a valid answer
   while (not success):

      if (retry_count == AI_RETRY_LIMIT):
         print("\n\nERROR: Too many AI errors, exiting\n")
         sys.exit()

      # Build prompt using static prompt and then essay read from file
      topic_prompt = prompt_txt + "\n\n" + extract_essay("essay.txt",number_of_cycles+1)

      print(">>>>>>>>>>>> Essay number: " + str(number_of_cycles+1) + " This is the topic prompt with essay attached >>>>>>>\n")
      print_string(topic_prompt)

      success, ai_reply, error_text = call_ai(topic_prompt) # Call AI, retry if error
      if (not success):
         print(error_text)
         retry_count = retry_count + 1
         ai_errors = ai_errors + 1
         continue

      print("\n***** Topic number: " + str(number_of_cycles + 1) + " ****************************\n")
      print_string(ai_reply)
      print("\n")

      write_to_file("topic.txt","\n\n******** Topic number: " + str(number_of_cycles + 1) + " ************\n\n")
      write_to_file("topic.txt",ai_reply)


# back to main outside loop 
   number_of_cycles = number_of_cycles + 1

print("\n----------- Final report -------------- ")
print("AI Prompt:")
print_string(prompt_txt)
#print("AI Prompt2:")
#print_string(prompt2_txt)
print("AI model: " + ai_model)

print("\nNumber of cycles: " + str(number_of_cycles))
print("AI Errors: " + str(ai_errors))
