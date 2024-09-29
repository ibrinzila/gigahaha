import re
from groq import Groq
from textblob import TextBlob
import os
import json

client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

# Obținem calea către directorul curent
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construim calea către fișierul JSON
json_path = os.path.join(current_dir, 'responses.json')

# Încărcăm dataset-ul
try:
    with open(json_path, 'r', encoding='utf-8') as f:
        responses = json.load(f)
except FileNotFoundError:
    print(f"Error: The file {json_path} was not found.")
    responses = {}
except json.JSONDecodeError:
    print(f"Error: The file {json_path} is not a valid JSON file.")
    responses = {}

def detect_language(text):
    # Listele de cuvinte specifice fiecărei limbi
    romanian_words = set(['salut', 'buna', 'ajutor', 'probleme', 'internet', 'parola', 'wifi'])
    russian_words = set(['привет', 'здравствуйте', 'помощь', 'проблемы', 'интернет', 'пароль'])
    english_words = set(['hello', 'hi', 'help', 'issues', 'internet', 'password', 'wifi'])

    # Convertim textul la lowercase și îl împărțim în cuvinte
    words = set(text.lower().split())

    # Verificăm suprapunerea cu listele de cuvinte
    ro_count = len(words.intersection(romanian_words))
    ru_count = len(words.intersection(russian_words))
    en_count = len(words.intersection(english_words))

    # Determinăm limba bazată pe cea mai mare suprapunere
    if ro_count >= ru_count and ro_count >= en_count:
        return 'ro'
    elif ru_count > ro_count and ru_count > en_count:
        return 'ru'
    else:
        return 'en'

def process_intent(text):
    lang = detect_language(text)
    print(f"Detected language: {lang}")

    intent_prompts = {
        'ro': f"Clasifică intenția următorului text în română: '{text}'. Intențiile posibile sunt: salut, am_nevoie_de_ajutor, probleme_cu_internetul, schimbare_parola_wifi, verificare_viteza, upgrade_plan, intrebare_facturare. Returnează doar numele intenției.",
        'ru': f"Классифицируйте намерение следующего текста на русском: '{text}'. Возможные намерения: приветствие, нужна_помощь, проблемы_с_интернетом, изменение_пароля_wifi, проверка_скорости, обновление_плана, вопрос_о_счете. Верните только название намерения.",
        'en': f"Classify the intent of the following English text: '{text}'. Possible intents are: greeting, need_help, internet_issues, change_wifi_password, check_speed, upgrade_plan, billing_inquiry. Return only the intent name."
    }

    prompt = intent_prompts.get(lang, intent_prompts['en'])
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.2-90b-text-preview",
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7,
            max_tokens=50,
            top_p=1,
            stream=False,
            stop=None
        )
        intent = completion.choices[0].message.content.strip().lower()
        print(f"Classified intent: {intent}")
        return intent, lang
    except Exception as e:
        print(f"Error in process_intent: {str(e)}")
        return "unknown", lang

def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment_score = blob.sentiment.polarity

    if sentiment_score < -0.5:
        return "very negative", sentiment_score
    elif sentiment_score < 0:
        return "negative", sentiment_score
    elif sentiment_score == 0:
        return "neutral", sentiment_score
    elif sentiment_score <= 0.5:
        return "positive", sentiment_score
    else:
        return "very positive", sentiment_score
def should_escalate(sentiment, sentiment_score):
    return sentiment in ['very negative', 'negative'] and sentiment_score < -0.3
def get_escalation_message(lang):
    messages = {
        'ro': "Îmi pare rău pentru inconveniențele create. Un reprezentant al serviciului clienți vă va contacta în curând pentru a vă ajuta cu problema dumneavoastră.",
        'ru': "Приносим извинения за доставленные неудобства. Представитель службы поддержки свяжется с вами в ближайшее время, чтобы помочь решить вашу проблему.",
        'en': "I'm sorry for the inconvenience. A customer service representative will contact you shortly to assist you with your issue."
    }
    return messages.get(lang, messages['en'])

def extract_entities(text):
    entities = {}
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    
    email_match = re.search(email_pattern, text)
    if email_match:
        entities['email'] = email_match.group()
    
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        entities['phone'] = phone_match.group()
    
    return entities

def generate_response(intent, entities, lang):
    print(f"Generating response for intent: {intent}, language: {lang}")
    
    # Mapare intenții pentru fiecare limbă
    intent_mapping = {
        'ro': {
            'salut': 'salut',
            'am_nevoie_de_ajutor': 'am_nevoie_de_ajutor',
            'probleme_cu_internetul': 'probleme_cu_internetul',
            'schimbare_parola_wifi': 'schimbare_parola_wifi'
        },
        'ru': {
            'приветствие': 'приветствие',
            'нужна_помощь': 'нужна_помощь',
            'проблемы_с_интернетом': 'проблемы_с_интернетом',
            'изменение_пароля_wifi': 'изменение_пароля_wifi'
        },
        'en': {
            'greeting': 'greeting',
            'need_help': 'need_help',
            'internet_issues': 'internet_issues',
            'change_wifi_password': 'change_wifi_password'
        }
    }
    
    # Folosim maparea pentru a obține cheia corectă pentru răspunsurile predefinite
    mapped_intent = intent_mapping.get(lang, {}).get(intent, intent)
    
    # Verificăm dacă avem un răspuns predefinit
    if responses and lang in responses and mapped_intent in responses[lang]:
        return responses[lang][mapped_intent]
    
    # Dacă nu avem un răspuns predefinit, generăm unul folosind modelul de limbaj
    prompts = {
        'ro': f"Generează un răspuns de asistență pentru clienți în limba română pentru următoarea intenție: '{intent}'. Entități: {entities}",
        'ru': f"Создайте ответ службы поддержки клиентов на русском языке для следующего намерения: '{intent}'. Сущности: {entities}",
        'en': f"Generate a customer support response in English for the following intent: '{intent}'. Entities: {entities}"
    }
    
    prompt = prompts.get(lang, prompts['en'])
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.2-90b-text-preview",
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None
        )
        response = completion.choices[0].message.content.strip()
        return response
    except Exception as e:
        print(f"Error in generate_response: {str(e)}")
        return "Îmi cer scuze, dar întâmpin dificultăți în generarea unui răspuns în acest moment. Vă rugăm să încercați din nou mai târziu."