import streamlit as st
import pandas as pd
from youtube_transcript_api import YouTubeTranscriptApi
import time
import spacy
import json
from pysbd.utils import PySBDFactory
import pysbd
import altair as alt
#from selenium import webdriver
#from selenium.webdriver.common.by import By



def main():
    link = st.text_input("YouTube video link", "https://www.youtube.com/watch?v=Up5VhPD2xZc")
    link = link.split('v=')[-1]
    data = get_subs(link)
    #with open ('demo.txt','r') as f:
    #    data = f.read()

    #data = json.loads(data)
    text = convert(data)
    text = ''.join(map(str,text))
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    pos = [(token.text, token.pos_) for token in doc]
    df = pd.DataFrame(pos, columns = ['word','pos'])

    select_pos = st.sidebar.multiselect('Parts of Speech',['SCONJ', 'PRON', 'VERB', 'PUNCT', 'AUX', 'PART', 'NOUN','DET', 'ADJ', 'PROPN', 'ADP', 'ADV','CCONJ','INTJ', 'NUM','SYM', 'X'],['VERB', 'ADJ','NOUN'])
    add_selectbox = st.sidebar.slider('Word mentions', min_value=1,max_value=100, value=5, step=1)
    #drop rows that contain any value in the list
    values = ['PUNCT', 'NUM', 'X', 'SYM']
    df = df[df.pos.isin(values) == False]
    df = df.groupby('pos')['word'].value_counts().reset_index(level=0)
    df['base_word'] = df.index
    df = df.reset_index(drop=True)
    df = df.rename({'word':'mentions'}, axis=1)

    df_level = pd.read_csv("cambridge_britisheng.csv")
    df_level = df_level.sort_values(by='level',ascending=True)
    df_level = df_level.drop_duplicates(subset=['base_word'], keep='first')
    df_level = df_level[['base_word','level']]
    df_level['level'] = df_level['level'].str.replace('<NA>', '-', regex=False)
    df = pd.merge(df_level, df, on='base_word', how='right')

    #df['translation'] = df.base_word.apply(lambda x: translate(x))

    #plotbar(df)
    for p in select_pos:
        st.subheader(posdic[str(p)])
        filtered = df[df.pos == str(p)]

		#Show table
        filtered = filtered[filtered.mentions >= add_selectbox]
        st.dataframe(filtered)

    #csv = convert_df(df)
    #st.download_button("Press to Download",df,"file.csv","text/csv",key='download-csv')

def plotbar(df):
    #chart_data = df['level'].dropna().value_counts().reset_index()
    #chart_data = df['mentions'].dropna().value_counts().reset
    chart = alt.Chart(df['mentions']).mark_bar().encode(alt.X("mentions", bin=True),y='count()')

    st.altair_chart(chart)

	#st.write(y)

    #st.write(labels = df['level'].dropna().unique())
    #st.write(labels)
	#chart_data = pd.DataFrame(y,columns=labels)
	#st.write(chart_data)
	#chart_data = pd.DataFrame(
	#np.random.randn(50, 3),
	#columns=["a", "b", "c"])

@st.cache
def get_subs(link):
    data = YouTubeTranscriptApi.get_transcript(link)
    return data

def convert(data):
    j = json.dumps(data)
    j = json.loads(j)
    counter = 0
    subs = []
    for i in j:
        counter += 1
        #start timestamp
        start = time.strftime('%H:%M:%S', time.gmtime(float(i['start'])))
        #end timestamp
        end = start + time.strftime('%H:%M:%S', time.gmtime(float(i['duration'])))

        #subtitle text
        #s = f"{counter}\n{start} --> {end}\n{i['text']}\n"
        #subs.append(s)

        subs.append(i['text'])

    return subs

def select_pos():
	selected_pos = st.selectbox("Select part of speech",
		 ('VERB','ADJECTIVE','NOUN'))
	return selected_pos

def pysbd_sentence_boundaries(doc):
    seg = pysbd.Segmenter(language="en", clean=False, char_span=True)
    sents_char_spans = seg.segment(doc.text)
    char_spans = [doc.char_span(sent_span.start, sent_span.end) for sent_span in sents_char_spans]
    start_token_ids = [span[0].idx for span in char_spans if span is not None]
    for token in doc:
        token.is_sent_start = True if token.idx in start_token_ids else False
    return doc

def get_sentances(text):
    nlp = spacy.blank('en')
    nlp.add_pipe('sbd')
    doc = nlp(text)
    return st.write(list(doc.sents))
    # [My name is Jonas E. Smith., Please turn to p. 55.]

def translate(word):
    chrome_path = r"home/dr-robin/Dev/ytstudy/chromedriver"
    driver = webdriver.Chrome(chrome_path)
    try:
        driver.get('https://papago.naver.com/')
        xpath = '//*[@id="txtSource"]'
        element = driver.find_element(By.XPATH, xpath)
        element.click()
        element.send_keys("{word)")
        xpath = '//*[@id="txtTarget"][span]'
        translated = driver.find_element(By.XPATH, xpath).text
    except:
        translated = "Not found"
    return translated


@st.cache
def convert_df(df):
   return df.to_csv().encode('utf-8')



posdic = {'VERB': 'verb','ADJ': 'adjective','ADV': 'adverb','AUX': 'auxiliary','CONJ': 'conjunction','CCONJ': 'coordinating conjunction',
'DET': 'determiner','INTJ': 'interjection','NOUN': 'noun','NUM': 'numeral','PART': 'particle',
'PRON': 'pronoun','PROPN': 'proper noun','PUNCT': 'punctuation','SCONJ': 'subordinating conjunction',
'SYM': 'symbol','X': 'other', 'ADP': 'adposition'}

if __name__ == "__main__":
    main()
