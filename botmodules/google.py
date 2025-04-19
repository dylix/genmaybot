import json, urllib.request, urllib.error, urllib.parse, re, botmodules.tools as tools
from googlesearch import search

def google_search(bot, e):
    try:
        # to search
        if e.input == '':
            e.output = "While we are all searching for the meaning of life in a general sense, you must be specific with this."
            return e
        query = e.input

        google_results = search(query, safe=None, num_results=10, advanced=True, unique=True)
        results_str = list(google_results)
        result_num = 0
        if len(results_str) == 0:
            e.output = "No results were found. Not sure why?!"
            return e
        for result in results_str:
            result_num += 1
            if result_num > 0 and result_num < 4:
                e.output += f"#{result_num} | {result.description} | {result.url} || "
        e.output = bot.tools['insert_at_closest_space'](e.output[:-3].rstrip())
    except Exception as err:
        e.output = f'Handling run-time error:{err}'
    return e

google_search.command = "!g"
google_search.helptext = "!g <query> - attempts to look up what you want to know on google"