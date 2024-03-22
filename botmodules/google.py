import json, urllib.request, urllib.error, urllib.parse, re, botmodules.tools as tools
from googlesearch import search

def google_search(bot, e):
    # to search
    if e.input == '':
        e.output = "While we are all searching for the meaning of life in a general sense, you must be specific with this."
        return e
    query = e.input
    google_results = search(query, num_results=2, advanced=True)
    #print ("list", list(google_results))
    #print(google_results.SearchResult.title)
    result_num = 0
    #print(len(google_results))
    for result in google_results:
        e.output += f"#{result_num+1} | {result.description} | {result.url} || "
        result_num += 1
    e.output = bot.tools['insert_at_closest_space'](e.output[:-3].rstrip())
    return e
    
google_search.command = "!g"
google_search.helptext = "!g <query> - attempts to look up what you want to know on google"