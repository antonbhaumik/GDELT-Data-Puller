"""
This should be used to download large lists of articles to do manual analysis. If you want some nice visuals, general
trends, and/or top articles, or if you want to analyse TV data too (which this program can't do), see
https://api.gdeltproject.org/api/v2/summary/summary. Please note that this program can be buggy and/or inefficient.
If something doesn't work, try different parameters or a shorter time period. Everything here is also saved in a .csv
format because it is very easy to work with. With pandas, you can replace .to_csv with .to_excel, .to_stata, .to_json,
.to_sql, etc. (docs here: https://pandas.pydata.org/docs/reference/io.html). Remember to also replace .read_csv with
.read_*! This is written with the v2 API; when the v3 API is released, this code will still work, but the v3 API is
probably better. Here is the documentation for the v2 API: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/.
You have to wait 5 seconds between each request because of the v2 rate limit. If you no longer need this (e.g. if you
pay them to remove the rate limit for you), simply remove all lines that say "time.sleep(5)". Any code that can be run
in parallel is already threaded if you remove these lines.
"""

# Inbuilt (standard library) modules
import datetime
import functools
import io
import json
import os
import shutil
import threading
import time
import zipfile

# Modules to install (see requirements.txt)
import googletrans
import httpcore
import pandas as pd
import pandas.errors
import requests


@functools.cache
def translate(df_index, df_col, text):
    """
    This function translates the given data but caches the return value.
    This is because many headlines (although from different sources) are repeated, and proper translations are slow.
    :param df_index: The index of the to be translated
    :param df_col: The column of the text to be translated
    :param text: The text to be translated
    :return: The translated text (possibly cached).
    """
    try:
        translations[(df_index, df_col)] = translator.translate(text, dest=translation).text
    except httpcore.ReadTimeout | httpcore.ReadError:
        pass


def pull_mode(current_mode):
    """
    This function, if necessary, downloads the relevant csv for the given mode.
    :param current_mode: The mode to query.
    :return: Nothing - a csv file is created
    """
    print(f"Pulling data for: {current_mode}")
    current_url = (base_url + f'{'&EndDateTime=' + enddatetime if enddatetime != '' else ''}'
                              f'&mode={current_mode}{'&sort=DateDesc' if 'Tone' not in current_mode else ''}')
    df = pd.read_csv(io.StringIO(requests.get(current_url + '&format=csv').content.decode('utf-8')),
                     on_bad_lines='skip')
    df.to_csv(f'output/{current_mode}.csv', sep=',', encoding='utf-8', index=False)


def normalise_column_name(column_name):
    """
    Normalises headlines to make 'headline', 'headline | source1', and 'headline | source2' be the same thing.
    :param column_name: The value to normalise.
    :return: The normalised value.
    """
    return column_name.split(' | ')[0]


def push_time_back(start, hours):
    """
    Pushes the time back the number of hours specified.
    :param start: The time to push back.
    :param hours: The number of hours to push the time back.
    :return: The time that has been pushed back.
    """
    datetime_obj = datetime.datetime.strptime(start, '%Y%m%d%H%M%S')
    datetime_obj -= datetime.timedelta(hours=hours)
    return datetime_obj.strftime('%Y%m%d%H%M%S')


def format_time_user(t):
    """
    This function formats the time from YYYYMMDDHHMMSS to YYYY-MM-DD HH:MM:SS for display.
    :param t: The time to format.
    :return: The formatted time as a string.
    """
    return datetime.datetime.strptime(t, '%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')


def format_time_api(t):
    """
    This function strips /, ., -, :, and whitespace out of the given time string.
    :param t: The time to format.
    :return: The formatted time as a string.
    """
    return t.replace(' ', '').replace('.', '').replace(':', '').replace('-', '').replace('/', '')


# Here, we pull the previous input from the last config file, if it exists, and we ask whether to use it
# When printing the existing output, format it
previous_input = {}
if os.path.exists('output/input.json'):
    print('The program detected a previous configuration:\n')
    with open('output/input.json', 'r', encoding='utf-8') as f:
        temp = json.load(f)
    for key, value in temp.items():
        if value:
            if isinstance(value, list):
                print(f'{key}: {', '.join(value)}')
            elif isinstance(value, str) and value.isnumeric():
                print(f'{key}: {format_time_user(value)}')
            else:
                print(f'{key}: {value}')
    if (input('\nIf you would like to use this configuration, please type yes, otherwise leave blank.\n> ')
            .lower() == 'yes'):
        previous_input = temp

if previous_input:
    # If the previous input data exists, and the user wants to use it, set variables accordingly and skip inputs
    keywords = previous_input.get('Keywords', '')
    keyword_format = previous_input.get('Keyword Format', '')
    lang = previous_input.get('Language', '')
    country = previous_input.get('Country', '')
    domain = previous_input.get('Domain', '')
    theme = previous_input.get('Theme', '')
    custom_parameters = previous_input.get('Custom', '')
    startdatetime = previous_input.get('Start', '')
    enddatetime = previous_input.get('End', '')
    translation = previous_input.get('Translation', '')
else:
    # Gets information to be passed into the GDELT API, leaving these blank leads to default options being used.
    # Some IDEs show a warning below because of the unsecure link - unfortunately, there are no other sources that I
    # could find for this list of themes.
    keywords = (input('Please enter keywords/phrases, separated by commas (comparisons use OR).\n> ')
                .replace(', ', ',').split(','))
    keyword_format = ''
    if len(keywords) > 1:
        keyword_format = input('You entered multiple keywords/phrases. Which format would you like to use: "AND" or '
                               '"OR".\n> ').upper()
    lang = input('Please enter a language or leave blank to include all languages.\n> ')
    country = input('Please enter a country or leave blank to include all countries.\n> ')
    domain = input('Please enter a domain name to search for or leave blank to include all domain names.\n> ')

    theme = input('Please enter a theme from here http://data.gdeltproject.org/api/v2/guides/LOOKUP-GKGTHEMES.TXT or'
                  'leave blank to include all themes.\n> ').upper()
    custom_parameters = input('Please enter custom query parameters, as per the documentation '
                              'https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/,\n'
                              'e.g. \'near20:"dog cat" repeat3:"cow"\' (or leave blank to skip).\n> ')

    # Inputs default values for start and end time if not provided
    startdatetime = format_time_api(input('Please enter a start date for requests in YYYYMMDDHHMMSS (you may use -, /, '
                                          '., or : to format), or leave blank to search from 1 Jan 2017.\n> '))
    enddatetime = format_time_api(input('Please enter an end date for the requests in YYYYMMDDHHMMSS (you may use -, '
                                        '/, ., or : to format), or leave blank to search until the present.\n> '))
    if not startdatetime:
        startdatetime = '20170101000000'
    if not enddatetime:
        enddatetime = push_time_back(datetime.datetime.now().strftime('%Y%m%d%H%M%S'), 0.25)

    # This language is used for the Google Translate API with the "googletrans" package rather than for GDELT
    translation = input('Please enter a 2-5 character language code from here '
                        'https://developers.google.com/admin-sdk/directory/v1/languages to translate titles to, or '
                        'leave blank to keep titles in their original language(s).\n> ')

# This can cause issues and cause you to be rate limited - DO NOT DISABLE SLEEP TIME UNLESS YOU KNOW WHAT YOU ARE DOING.
# This value is not stored between runs, so must manually be set each time.
should_sleep = input('To disable 5 second waiting times (which prevent rate limiting) please type the phrase "I KNOW '
                     'WHAT I AM DOING!", otherwise leave blank.\n> ').upper() != 'I KNOW WHAT I AM DOING!'

# Format the keywords correctly (done regardless of input type) - this is either the keyword/phrase alone if there is
# one, or if there are multiple, then as follows: (keyword/phrase 1 OR keyword/phrase 2 OR ... OR keyword/phrase n).
# Phrases need to be in "quotation marks", otherwise the words are treated as separate.
keystring = f'{f'"{keywords[0]}"' if keywords[0] else ''}'
if len(keywords) > 1:
    if keyword_format == 'OR':
        keystring = f'("{'" OR "'.join(keywords)}")'.replace('"', "%22").replace(" ", "%20")
    elif keyword_format == 'AND':
        keystring = f'"{'" "'.join(keywords)}"'.replace(' ', '%20').replace('"', '%22')
    else:
        print(f'The keyword format entered, {keyword_format}, is invalid. Only using first keyword: {keywords[0]}.')

# Here, we empty the output/folder if it already exists, creates it if it doesn't
if os.path.exists('output/'):
    shutil.rmtree('output/')
os.makedirs("output/")

# Here, we put the parameters above into a file, to allow for importing later
inp = {
    'Keywords': keywords,
    'Keyword Format': keyword_format,
    'Language': lang,
    'Country': country,
    'Domain': domain,
    'Theme': theme,
    'Custom': custom_parameters,
    'Start': startdatetime,
    'End': enddatetime,
    'Translation': translation,
}
with open('output/input.json', 'w', encoding='utf-8') as f:
    json.dump(inp, f, indent=4)

# These options are the same no matter what we're querying (keyword, lang, country, domain, theme, startdatetime)
base_url = ('https://api.gdeltproject.org/api/v2/doc/doc'
            f'?query={keystring}'
            f'{' SourceLang:' + lang if lang else ''}'
            f'{' SourceCountry:' + country if country else ''}'
            f'{' DomainIs:' + domain if domain else ''}'
            f'{' Theme:' + theme if theme else ''}'
            f'{' ' + custom_parameters if custom_parameters else ''}'
            f'&StartDateTime={startdatetime}')

# For the following options, we want to do the same thing:
# - get the data from the API after inputting the relevant extra parameters
# - this is only done if there are no restrictions making the data obsolete (language/country)
# - see api docs for other stuff that can be added: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
# - most (if not all) of the other data is available in csv format
# - use pandas to convert the data into a dataframe
# - use pandas to dump the dataframe into a csv file
# - we have to wait 5s to avoid rate limits; the threading is currently pretty useless with the rate limit (unless the
#   API takes >5s to process the request), but if the API limit is no longer a problem, and the time.sleep(5) is
#   removed, it will be fast
threads = []
modes = ['TimelineVolRaw', 'TimelineVolInfo', 'TimelineTone', 'ToneChart']
if not lang:
    modes.append('TimelineLang')
if not country:
    modes.append('TimelineSourceCountry')
for mode in modes:
    threads.append(threading.Thread(target=pull_mode, args=(mode,)))
for thread in threads:
    thread.start()
    if should_sleep:
        time.sleep(5)
for thread in threads:
    thread.join()

# The processing for the article list is different, because of a 250 article per request limit, and also each request
# seemingly only searching the last 3 months, so we do the following:
# - create a main pandas dataframe to store everything
# - get as many articles as possible, working backwards from the end time to the start time
# - dump these 250 articles into the main dataframe
# - get the time of the earliest article
# - repeat with that time as the new end time
# - if it gets stuck, push the end time 6 hours earlier, and continue repeating
# - if there is no data, push it 3 months back (this is probably a search with sparse data, so nothing in the last 3
#   months, but potentially stuff before then, so we need to continue until we hit the start date)
# - use pandas to dump the main dataframe into a csv file after every iteration (in case the program fails/gets stuck)
# - use pandas to delete repeated rows (rare but possible, because of overlapping time periods), before dumping into csv
# - clean up csv, removing useless columns
# - we have to wait 5s to avoid rate limits :(
# - if there is no data, multiple types of error can be thrown (usually because a csv file with no data is received) - I
#   have written code to catch the ones that I observed, but if you encounter new ones, add new try-except statements
artlist_df = pd.DataFrame()

print('Pulling data for: ArtList')
seen = set()
while not enddatetime or startdatetime < enddatetime:
    if enddatetime in seen:
        enddatetime = push_time_back(enddatetime, 6)
    seen.add(enddatetime)

    print(f'Pulling until: {format_time_user(enddatetime)}')

    url = (base_url + f'&StartDateTime={startdatetime}'
                      f'{'&EndDateTime=' + enddatetime}'
                      f'&mode=ArtList&maxrecords=250&sort=DateDesc')

    try:
        x = requests.get(url + '&format=csv').content.decode('utf-8')
        translation_df = pd.read_csv(io.StringIO(x), on_bad_lines='skip')
        complete_df = pd.concat([artlist_df, translation_df], ignore_index=True)
        # This is originally in the format 'xxx    yyyy-mm-dd hh:mm:ss', where 'xxx' is the line number.
        enddatetime = min(str(complete_df.tail(1)["Date"]).split("\n")[0][-19:].replace("-", "")
                          .replace(":", "").replace(" ", ""), enddatetime)
        artlist_df = complete_df.drop_duplicates(keep='first')
        artlist_df.to_csv(f'output/ArtList.csv', sep=',', encoding='utf-8', index=False)
    except pandas.errors.EmptyDataError | KeyError:
        enddatetime = push_time_back(enddatetime, 2160)

    if should_sleep:
        time.sleep(5)

if 'MobileURL' in artlist_df.columns:
    artlist_df.drop(columns='MobileURL')
artlist_df.drop_duplicates(keep='first').to_csv(f'output/ArtList.csv', sep=',', encoding='utf-8', index=False)

# Here, we translate all the titles/headlines in the csv files in ArtList.csv to the specified language, as follows:
# - if no language is specified, don't need to translate, so skip
# - go through every column in the relevant csv files that contains the word "title"
# - iterate through the rows and translate each one, unless it is empty
# - use pandas to dump the translated data into the original csv file
# - the translations are threaded, but I can only have 100 active streams at a time with the googletrans module,
#   so I limit the number of threads to 100
if translation:
    translator = googletrans.Translator()
    for file in ('ArtList', 'TimelineVolInfo', 'ToneChart'):
        if not os.path.exists(f'output/{file}.csv'):
            continue
        print(f'Translating titles in {file}')
        translations = {}
        threads.clear()
        translation_df = pd.read_csv(f'output/{file}.csv', on_bad_lines='skip')
        for col in translation_df.columns:
            if 'Title' in col:
                for index, value in translation_df[col].items():
                    if str(value) != "nan":
                        threads.append(threading.Thread(target=translate, args=(index, col, value)))
        active_threads = []
        for thread in threads:
            while len(active_threads) >= 100:
                active_threads[0].join()
                active_threads.pop(0)
            thread.start()
            active_threads.append(thread)
        for thread in threads:
            thread.join()
        for key, val in translations.items():
            translation_df.at[key[0], key[1]] = val
        translation_df.to_csv(f'output/{file}Translated.csv', index=False)

# Here, we create a second file, that removes duplicate headlines. The normalisation is needed because we want to treat
# 'headline', 'headline | source', and 'headline ( From source)' the same. These are commonly seen in UK headlines
# (this is not exhaustive, and can miss headlines, especially outside the UK; from the code below it should be
# relatively easy to add new strings, if not then read documentation/StackOverflow or ask ChatGPT/GitHub Copilot). The
# code also removes whitespace to treat the same headline with whitespace differences as the same.
for file in ('ArtList', 'ArtListTranslated'):
    if os.path.exists(f'output/{file}.csv'):
        original_df = pd.read_csv(f'output/{file}.csv', on_bad_lines='skip')
        original_df['Normalised'] = original_df['Title'].str.split('|').str[0].str.split('(').str[0].str.strip()
        original_df = original_df.drop_duplicates(subset='Normalised', keep='first').drop(columns='Normalised')
        original_df.to_csv(f'output/{file}NoDuplicates.csv', index=False)

# Here, we shove all csv files into a .zip file, for easy exports
with zipfile.ZipFile('output.zip', 'w', zipfile.ZIP_DEFLATED) as f:
    for file in os.listdir('output/'):
        f.write('output/' + file)

# End (please write all new code before this point)
print('The program is done - ./output.zip contains all the data files, ./output/ contains individual .csv/.json files.')
