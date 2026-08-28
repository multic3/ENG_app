"""Build the two reviewed A2 locations (100 points / 500 exercises)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TYPES = ("multiple_choice", "fill_blank", "listening", "speech")
TYPE_ORDERS = (
    ("listening", "multiple_choice", "fill_blank", "speech", "multiple_choice"),
    ("multiple_choice", "fill_blank", "listening", "speech", "fill_blank"),
    ("fill_blank", "listening", "multiple_choice", "speech", "listening"),
    ("multiple_choice", "speech", "listening", "fill_blank", "speech"),
)

NAMES = (
    ("Mia", "she"), ("Leo", "he"), ("Sofia", "she"), ("Noah", "he"),
    ("Emma", "she"), ("Liam", "he"), ("Ava", "she"), ("Owen", "he"),
    ("Lily", "she"), ("Max", "he"), ("Zoe", "she"), ("Ben", "he"),
    ("Nora", "she"), ("Alex", "he"), ("Ella", "she"), ("Sam", "he"),
    ("Lucy", "she"), ("Jack", "he"), ("Maya", "she"), ("Finn", "he"),
)
COUNTRIES = (
    "Italy", "Brazil", "Japan", "Canada", "Spain", "India", "Poland",
    "Mexico", "France", "Egypt", "Greece", "Turkey", "Chile", "Korea",
    "Portugal", "Sweden", "Ireland", "Argentina", "Thailand", "Australia",
)
CITIES = (
    "Rome", "Recife", "Osaka", "Toronto", "Seville", "Pune", "Krakow",
    "Puebla", "Lyon", "Cairo", "Athens", "Izmir", "Valparaiso", "Busan",
    "Porto", "Malmö", "Cork", "Mendoza", "Chiang Mai", "Perth",
)
JOBS = (
    "chef", "student", "designer", "nurse", "mechanic", "teacher",
    "photographer", "baker", "engineer", "doctor", "musician", "driver",
    "artist", "programmer", "farmer", "waiter", "guide", "writer",
    "dentist", "shop assistant",
)
ITEMS = (
    "a red backpack", "a small camera", "a blue bicycle", "a warm jacket",
    "a guitar", "a travel notebook", "a green umbrella", "a new laptop",
    "a lunch box", "a city map", "a yellow scarf", "a tennis racket",
    "a coffee mug", "a library card", "a pair of boots", "a sketchbook",
    "a bus pass", "a silver watch", "a water bottle", "a beach towel",
)
PETS = (
    "cat", "dog", "rabbit", "parrot", "hamster", "turtle", "fish",
    "guinea pig", "small dog", "grey cat",
)

LOCATION_ONE_TITLES = (
    "A friendly hello", "Morning at the gate", "Meet the new neighbour",
    "Names at the café", "A visitor from abroad", "The village welcome desk",
    "Nagisa introduces a friend", "Pronouns on the noticeboard",
    "Short forms at the inn", "First introduction checkpoint",
    "Who is not here?", "Correcting a name", "A visitor is not a guide",
    "Questions at the gate", "Are you new here?", "Is she from Spain?",
    "A yes-or-no interview", "Negative short forms", "Meet two travellers",
    "Guided practice checkpoint", "Where are you from?", "Country and city",
    "What is your job?", "How old is the visitor?", "Who is the teacher?",
    "A profile card", "Three personal questions", "The registration queue",
    "Information desk dialogue", "Context practice checkpoint",
    "Introduce a colleague", "Fix an incorrect profile", "Ask without a model",
    "A longer self-introduction", "Meet the festival team", "Welcome a family",
    "The international table", "A quick networking round", "Voice introduction",
    "Independent practice checkpoint", "Find the missing guest",
    "Help Nagisa check the list", "Correct three introductions",
    "Welcome the musicians", "The mixed-language queue", "Festival registration",
    "Introduce the village team", "Solve the identity mix-up",
    "Rehearse the welcome speech", "Mission: open the village festival",
)

LOCATION_TWO_TITLES = (
    "What have you got?", "A bag for the journey", "My favourite possession",
    "Nagisa has a bell", "Things on the table", "A pet at home",
    "Family photos", "Two useful objects", "Our shared room",
    "Personal details checkpoint", "I haven't got a ticket", "She hasn't got a map",
    "Have you got a phone?", "Has he got a bicycle?", "What is in your bag?",
    "Where is your home?", "How old is your pet?", "Questions without clues",
    "A short personal interview", "Guided practice checkpoint",
    "Describe your family", "A class profile", "The lost backpack",
    "Compare two personal cards", "Ask about a new colleague", "A pet-owner dialogue",
    "The hobby shelf", "Information for a club", "Complete a registration form",
    "Context practice checkpoint", "Tell us what you own", "Interview a traveller",
    "Explain what you haven't got", "Ask follow-up questions", "A two-part answer",
    "Personal information by phone", "A profile without a model", "Meet the beach team",
    "Voice profile challenge", "Independent practice checkpoint", "Weak-topic review: be",
    "Weak-topic review: have got", "Weak-topic review: questions",
    "Weak-topic review: pronouns", "Weak-topic review: word order",
    "Prepare the guest list", "Check bags for the trip", "Introduce the whole team",
    "Solve the missing-details puzzle", "Mission: organise the beach expedition",
)


def profile(point_number: int) -> dict:
    index = (point_number - 1) % len(NAMES)
    name, pronoun = NAMES[index]
    second_index = (index + 7) % len(NAMES)
    second_name, second_pronoun = NAMES[second_index]
    return {
        "name": name,
        "pronoun": pronoun,
        "subject_pronoun": "She" if pronoun == "she" else "He",
        "country": COUNTRIES[index],
        "city": CITIES[index],
        "job": JOBS[index],
        "age": 19 + ((point_number * 3) % 29),
        "second_name": second_name,
        "second_pronoun": second_pronoun,
        "item": ITEMS[index],
        "second_item": ITEMS[(index + 5) % len(ITEMS)],
        "pet": PETS[index % len(PETS)],
        "pet_name": NAMES[(index + 11) % len(NAMES)][0],
    }


def mc(prompt: str, translation: str, answer: str, options: list[str], explanation: str) -> dict:
    return {
        "prompt": prompt,
        "translation": translation,
        "correct_answer": answer,
        "options": options,
        "explanation": explanation,
    }


def fill(prompt: str, translation: str, answer: str, explanation: str, accepted: list[str] | None = None) -> dict:
    return {
        "prompt": prompt,
        "translation": translation,
        "correct_answer": answer,
        "accepted_answers": accepted or [],
        "explanation": explanation,
    }


def listening(prompt: str, translation: str, audio_text: str, answer: str, options: list[str], explanation: str) -> dict:
    return {
        "prompt": prompt,
        "translation": translation,
        "audio_text": audio_text,
        "audio": {"provider": "browser_tts", "language": "en-US", "rate": 0.82},
        "correct_answer": answer,
        "options": options,
        "explanation": explanation,
    }


def speech_repeat(prompt: str, translation: str, phrase: str, explanation: str) -> dict:
    return {
        "mode": "speech_repeat",
        "prompt": prompt,
        "translation": translation,
        "phrase": phrase,
        "accepted_answers": [phrase],
        "explanation": explanation,
        "speech_settings": {
            "provider": "browser_speech_recognition",
            "language": "en-US",
            "required_concepts": phrase.lower().replace("'", "").split(),
            "target_grammar": [],
            "min_words": max(2, len(phrase.split()) - 1),
            "enforce_order": True,
            "show_model_before_attempt": True,
            "pronunciation_assessed": False,
        },
    }


def speech_response(
    prompt: str,
    translation: str,
    accepted: list[str],
    required_concepts: list[str],
    target_grammar: list[str],
    min_words: int,
    explanation: str,
    show_model: bool,
) -> dict:
    return {
        "mode": "speech_response",
        "prompt": prompt,
        "translation": translation,
        "accepted_answers": accepted,
        "explanation": explanation,
        "speech_settings": {
            "provider": "browser_speech_recognition",
            "language": "en-US",
            "required_concepts": required_concepts,
            "target_grammar": target_grammar,
            "min_words": min_words,
            "enforce_order": False,
            "show_model_before_attempt": show_model,
            "pronunciation_assessed": False,
        },
    }


def location_one_pools(point_number: int, data: dict) -> dict[str, list[dict]]:
    stage = ((point_number - 1) // 10) + 1
    name = data["name"]
    pronoun = data["subject_pronoun"]
    country = data["country"]
    city = data["city"]
    job = data["job"]
    age = data["age"]
    scenario = LOCATION_ONE_TITLES[point_number - 1]

    if stage == 1:
        return {
            "multiple_choice": [
                mc(f"At {scenario.lower()}, choose the correct introduction: ___ {name}.", "Выбери правильное представление.", "I am", ["I am", "I is", "I are", "Am I"], "Use I am before a name."),
                mc(f"Choose the pronoun for {name}: {name} is a {job}. ___ is a {job}.", "Выбери местоимение для человека.", pronoun, [pronoun, "it", "we", "they"], "Use he or she for one person."),
            ],
            "fill_blank": [
                fill(f"Complete the welcome card: Hello, I ___ {name}.", "Заполни приветственную карточку.", "am", "The verb to be with I is am."),
                fill(f"Complete the visitor note: {name} ___ from {country}.", "Заполни запись о посетителе.", "is", "Use is with one person."),
            ],
            "listening": [
                listening(f"Listen at {scenario.lower()}. Where is {name} from?", "Послушай и выбери страну.", f"Hello, I'm {name}. I'm from {country}.", country, [country, COUNTRIES[(point_number + 3) % 20], COUNTRIES[(point_number + 8) % 20], COUNTRIES[(point_number + 12) % 20]], "The speaker says I'm from followed by the country."),
                listening(f"Listen and choose {name}'s job.", "Послушай и выбери профессию.", f"Nice to meet you. I'm {name}, and I'm a {job}.", job, [job, JOBS[(point_number + 4) % 20], JOBS[(point_number + 9) % 20], JOBS[(point_number + 14) % 20]], "The job comes after I'm a."),
            ],
            "speech": [
                speech_repeat(f"Greet {name} clearly.", "Чётко произнеси приветствие.", f"Hello, {name}. Nice to meet you.", "The transcript checks the words, not pronunciation quality."),
                speech_response(f"At {scenario.lower()}, introduce yourself with your name.", "Представься и назови своё имя.", ["I am Anya", "I'm Anya", "My name is Anya"], ["i"], ["to_be"], 3, "A valid answer introduces the speaker with a complete phrase.", True),
            ],
        }

    if stage == 2:
        return {
            "multiple_choice": [
                mc(f"Correct the guest list for {scenario.lower()}: {name} ___ from {country}.", "Исправь запись в списке гостей.", "isn't", ["isn't", "aren't", "am not", "not is"], "Use isn't with one person."),
                mc(f"Choose the correct question for {name}: ___ {pronoun.lower()} a {job}?", "Выбери правильный вопрос.", "Is", ["Is", "Are", "Am", "Does"], "A yes/no question with he or she starts with Is."),
            ],
            "fill_blank": [
                fill(f"Make a negative sentence: I ___ from {country}; I'm from {CITIES[(point_number + 5) % 20]}.", "Сделай предложение отрицательным.", "am not", "Use am not after I."),
                fill(f"Complete the short question at {scenario.lower()}: ___ you new here?", "Заполни короткий вопрос.", "Are", "Questions with you begin with Are."),
            ],
            "listening": [
                listening(f"Listen and decide whether {name} is a {job}.", "Послушай и выбери ответ.", f"I'm {name}. I'm not a {job}; I'm a {JOBS[(point_number + 6) % 20]}.", "No", ["No", "Yes", "Not stated", "Both jobs"], "The speaker explicitly says I'm not."),
                listening(f"Listen to the gate question. What is the answer?", "Послушай вопрос у ворот.", f"Are you {name} from {country}? Yes, I am.", "Yes, I am.", ["Yes, I am.", "No, I'm not.", "Yes, she is.", "No, he isn't."], "The short answer agrees with a question using you."),
            ],
            "speech": [
                speech_repeat(f"Repeat the correction about {name}.", "Повтори исправление.", f"{name} isn't from {country}.", "The apostrophe does not affect transcript matching."),
                speech_response(f"Answer the question at {scenario.lower()}: Are you new here?", "Ответь, новый ли ты здесь.", ["Yes, I am", "No, I'm not", "No, I am not"], ["i"], ["to_be_question"], 3, "Use a short answer with I am or I'm not.", True),
            ],
        }

    if stage == 3:
        return {
            "multiple_choice": [
                mc(f"At {scenario.lower()}, ask about origin: ___ is {name} from?", "Спроси, откуда человек.", "Where", ["Where", "What", "Who", "How old"], "Use Where to ask about a place."),
                mc(f"Choose the correct job sentence for {name}.", "Выбери правильное предложение о профессии.", f"{pronoun} is a {job}.", [f"{pronoun} is a {job}.", f"{pronoun} are {job}.", f"{pronoun} is {job} an.", f"{pronoun} am a {job}."], "Use subject + is + a/an + singular job."),
            ],
            "fill_blank": [
                fill(f"Complete the age question for {name}: How old ___ {pronoun.lower()}?", "Заполни вопрос о возрасте.", "is", "Use is with he or she."),
                fill(f"Complete the profile: {name} is ___ {city}, {country}.", "Заполни профиль городом происхождения.", "from", "Use from before a city or country."),
            ],
            "listening": [
                listening(f"Listen to {name}'s profile. How old is the speaker?", "Послушай и выбери возраст.", f"My name is {name}. I'm {age}, and I'm from {city}.", str(age), [str(age), str(age + 1), str(age - 2), str(age + 5)], "The age follows I'm."),
                listening(f"Listen at {scenario.lower()}. Which city does {name} name?", "Послушай и выбери город.", f"I'm a {job} from {city}, but I work in {CITIES[(point_number + 2) % 20]}.", city, [city, CITIES[(point_number + 2) % 20], CITIES[(point_number + 9) % 20], CITIES[(point_number + 13) % 20]], "The phrase from identifies the home city."),
            ],
            "speech": [
                speech_repeat(f"Ask {name} about work.", "Спроси о работе.", "What is your job?", "The transcript checks the question words and order."),
                speech_response(f"Give a three-part profile at {scenario.lower()}: name, city and job.", "Назови имя, город и профессию.", [f"I'm {name}. I'm from {city}. I'm a {job}."], ["i", "from"], ["to_be", "word_order"], 7, "Include a name, origin and occupation in complete clauses.", True),
            ],
        }

    if stage == 4:
        return {
            "multiple_choice": [
                mc(f"Choose the natural reply when {name} says, 'Nice to meet you.'", "Выбери естественный ответ.", "Nice to meet you too.", ["Nice to meet you too.", "I meet nice.", "Too you are nice.", "Where meet you?"], "Reply with Nice to meet you too."),
                mc(f"Find the correct word order for {scenario.lower()}.", "Найди правильный порядок слов.", f"{name} is a {job} from {country}.", [f"{name} is a {job} from {country}.", f"Is {name} from a {job} {country}.", f"A {job} {name} from is {country}.", f"{name} a {job} is {country} from."], "English statements normally use subject + verb + complement."),
            ],
            "fill_blank": [
                fill(f"Complete the colleague introduction: This ___ {name}, our new {job}.", "Закончи представление коллеги.", "is", "Use This is when introducing a person."),
                fill(f"Complete the dialogue: 'Are you from {country}?' 'Yes, I ___.'.", "Закончи диалог.", "am", "Repeat the auxiliary in a short answer."),
            ],
            "listening": [
                listening(f"Listen to the introduction at {scenario.lower()}. Who is new?", "Послушай и выбери нового участника.", f"Everyone, this is {name}. {pronoun} is our new {job} from {city}.", name, [name, data["second_name"], "Nagisa", "The speaker"], "This is introduces the new person."),
                listening(f"Listen and choose the accurate profile.", "Послушай и выбери точный профиль.", f"Hi, I'm {name}. I'm {age}. I'm from {country}, and I'm a {job}.", f"{name}, {age}, {country}, {job}", [f"{name}, {age}, {country}, {job}", f"{name}, {age + 4}, {city}, {job}", f"{data['second_name']}, {age}, {country}, student", f"{name}, {age}, Canada, teacher"], "Match all four details from the audio."),
            ],
            "speech": [
                speech_repeat(f"Introduce {name} to the group.", "Представь человека группе.", f"This is {name}. {pronoun} is from {country}.", "The transcript checks the introduction, not accent."),
                speech_response(f"Without reading a model, welcome a new person during {scenario.lower()}.", "Без готового образца поприветствуй нового человека.", ["Hello, nice to meet you", "Hi, welcome to the village", "Welcome, it's nice to meet you"], ["welcome"], ["greeting"], 4, "A suitable answer contains a greeting or welcome phrase.", False),
            ],
        }

    return {
        "multiple_choice": [
            mc(f"During {scenario.lower()}, select the accurate correction: '{name} are from {country}.'", "Выбери правильное исправление.", f"{name} is from {country}.", [f"{name} is from {country}.", f"{name} am from {country}.", f"{name} are {country}.", f"Is {name} from {country}."], "Use is in a statement about one person."),
            mc(f"Choose the best opening for the festival interview with {name}.", "Выбери лучшее начало интервью.", "Hello. What's your name?", ["Hello. What's your name?", "Name is what you?", "Where your name is?", "Are name you?"], "A polite interview begins with a greeting and a correctly ordered question."),
        ],
        "fill_blank": [
            fill(f"Repair the mission note: {name} and {data['second_name']} ___ from different cities.", "Исправь запись миссии.", "are", "Use are with two people."),
            fill(f"Complete the final welcome: We ___ happy to meet you, {name}.", "Закончи финальное приветствие.", "are", "Use are after we."),
        ],
        "listening": [
            listening(f"Listen to the festival desk during {scenario.lower()}. Which detail is wrong on the card?", "Послушай и найди неверную деталь.", f"I'm {name}, I'm from {city}, and I'm a {job}. The card says I'm from {CITIES[(point_number + 4) % 20]}.", "city", ["city", "name", "job", "nothing"], "The speaker contrasts the real city with the card."),
            listening(f"Listen to two introductions. Who is from {country}?", "Послушай два представления.", f"{name} is a {job} from {country}. {data['second_name']} is from {COUNTRIES[(point_number + 6) % 20]}.", name, [name, data["second_name"], "both people", "neither person"], "The first introduction contains the target country."),
        ],
        "speech": [
            speech_repeat(f"Rehearse the clear festival announcement for {name}.", "Повтори объявление для фестиваля.", f"Welcome {name}, our new {job} from {country}.", "The app checks transcript content only."),
            speech_response(f"Complete the mission at {scenario.lower()}: give a connected introduction with at least two personal details.", "Заверши миссию: представься и назови минимум две детали.", [f"I'm {name}. I'm from {city}, and I'm a {job}."], ["i", "from"], ["to_be", "personal_introduction"], 8, "A successful response is connected and contains at least two personal details.", False),
        ],
    }


def location_two_pools(point_number: int, data: dict) -> dict[str, list[dict]]:
    stage = ((point_number - 1) // 10) + 1
    name = data["name"]
    pronoun = data["subject_pronoun"]
    item = data["item"]
    second_item = data["second_item"]
    pet = data["pet"]
    pet_name = data["pet_name"]
    scenario = LOCATION_TWO_TITLES[point_number - 1]

    if stage == 1:
        return {
            "multiple_choice": [
                mc(f"At {scenario.lower()}, choose the correct form: I ___ {item}.", "Выбери правильную форму.", "have got", ["have got", "has got", "am got", "got have"], "Use have got with I."),
                mc(f"Choose the correct sentence about {name} and {item}.", "Выбери правильное предложение.", f"{pronoun} has got {item}.", [f"{pronoun} has got {item}.", f"{pronoun} have got {item}.", f"{pronoun} is got {item}.", f"{pronoun} got has {item}."], "Use has got with he or she."),
            ],
            "fill_blank": [
                fill(f"Complete the inventory: We ___ two useful bags.", "Заполни список вещей.", "have got", "Use have got with we."),
                fill(f"Complete {name}'s profile: {pronoun} ___ a {pet} called {pet_name}.", "Заполни профиль питомца.", "has got", "Use has got with he or she."),
            ],
            "listening": [
                listening(f"Listen at {scenario.lower()}. What has {name} got?", "Послушай и выбери вещь.", f"I'm {name}, and I've got {item} for the trip.", item, [item, second_item, ITEMS[(point_number + 7) % 20], ITEMS[(point_number + 11) % 20]], "I've got is the contracted form of I have got."),
                listening(f"Listen and choose {name}'s pet.", "Послушай и выбери питомца.", f"At home, I've got a {pet}. Its name is {pet_name}.", pet, [pet, PETS[(point_number + 2) % 10], PETS[(point_number + 5) % 10], PETS[(point_number + 8) % 10]], "The pet follows I've got a."),
            ],
            "speech": [
                speech_repeat(f"Say what is in your travel set.", "Скажи, что есть в дорожном наборе.", f"I've got {item} and {second_item}.", "The transcript checks the stated possessions."),
                speech_response(f"At {scenario.lower()}, name one thing you have got.", "Назови одну вещь, которая у тебя есть.", [f"I have got {item}", f"I've got {item}", f"I have {item}"], ["i"], ["have_got"], 4, "Use I have got, I've got or I have plus an object.", True),
            ],
        }

    if stage == 2:
        return {
            "multiple_choice": [
                mc(f"Choose the negative form for {scenario.lower()}: {name} ___ {item}.", "Выбери отрицательную форму.", "hasn't got", ["hasn't got", "haven't got", "isn't got", "doesn't got"], "Use hasn't got with he or she."),
                mc(f"Choose the question about {name}'s {pet}: ___ {pronoun.lower()} got a {pet}?", "Выбери правильный вопрос.", "Has", ["Has", "Have", "Is", "Does"], "Questions with he or she begin with Has."),
            ],
            "fill_blank": [
                fill(f"Complete the negative inventory: I ___ {second_item} today.", "Заполни отрицательное предложение.", "haven't got", "Use haven't got with I."),
                fill(f"Complete the bag question: What ___ you got in your backpack?", "Заполни вопрос о содержимом сумки.", "have", "A have got question with you begins What have you got...?"),
            ],
            "listening": [
                listening(f"Listen during {scenario.lower()}. Which item is missing?", "Послушай и выбери отсутствующую вещь.", f"I've got {item}, but I haven't got {second_item}.", second_item, [second_item, item, ITEMS[(point_number + 9) % 20], "nothing"], "The missing object follows haven't got."),
                listening(f"Listen to the question and choose the short answer.", "Послушай вопрос и выбери короткий ответ.", f"Has {name} got a {pet}? Yes, {pronoun.lower()} has.", f"Yes, {pronoun.lower()} has.", [f"Yes, {pronoun.lower()} has.", f"Yes, {pronoun.lower()} is.", "Yes, I have.", f"No, {pronoun.lower()} haven't."], "Repeat has in the short answer."),
            ],
            "speech": [
                speech_repeat(f"Ask the practical question at {scenario.lower()}.", "Повтори практический вопрос.", "Have you got a phone?", "The word order Have you got is important."),
                speech_response(f"Answer honestly at {scenario.lower()}: Have you got a travel bag?", "Ответь, есть ли у тебя дорожная сумка.", ["Yes, I have", "No, I haven't", "Yes, I have got one", "No, I have not"], ["i"], ["have_got_question"], 3, "Use a short answer with have or haven't.", True),
            ],
        }

    if stage == 3:
        return {
            "multiple_choice": [
                mc(f"Choose the best question for the profile at {scenario.lower()}: ___ have you got?", "Выбери вопрос для профиля.", "What hobbies", ["What hobbies", "Where hobbies", "How old hobbies", "Who hobby"], "Use What to ask for information about things or activities."),
                mc(f"Choose the complete family detail about {name}.", "Выбери полную информацию о семье.", f"{pronoun} has got one sister and a {pet}.", [f"{pronoun} has got one sister and a {pet}.", f"{pronoun} have one sister a {pet}.", f"Has got {pronoun.lower()} sister and {pet}.", f"{pronoun} is got one sister."], "Use subject + has got + details."),
            ],
            "fill_blank": [
                fill(f"Complete the personal question: Where ___ your family from?", "Заполни вопрос о семье.", "is", "Family is normally treated as singular here."),
                fill(f"Complete the pet question: How old ___ {pet_name}?", "Заполни вопрос о возрасте питомца.", "is", "Use is in a question about one pet."),
            ],
            "listening": [
                listening(f"Listen to {name}'s family profile. How many brothers are mentioned?", "Послушай и выбери количество братьев.", f"I've got one sister and two brothers. We've also got a {pet} called {pet_name}.", "two", ["two", "one", "three", "none"], "The speaker says two brothers."),
                listening(f"Listen at {scenario.lower()}. Where is the family from?", "Послушай и выбери страну.", f"My family is from {data['country']}, but we live in {data['city']} now.", data["country"], [data["country"], data["city"], COUNTRIES[(point_number + 5) % 20], "not stated"], "From introduces origin; live in introduces the current city."),
            ],
            "speech": [
                speech_repeat(f"Repeat the two-detail profile for {name}.", "Повтори профиль с двумя деталями.", f"{name} has got {item} and a {pet}.", "The transcript checks both details."),
                speech_response(f"At {scenario.lower()}, give two details about your family, pet or possessions.", "Назови две детали о семье, питомце или вещах.", [f"I have got a {pet} and {item}", f"I've got {item}. My family is from {data['country']}"], ["i"], ["have_got", "personal_information"], 7, "Give at least two connected personal details.", True),
            ],
        }

    if stage == 4:
        return {
            "multiple_choice": [
                mc(f"Choose the natural follow-up at {scenario.lower()}: 'I've got a {pet}.'", "Выбери естественный дополнительный вопрос.", "What's its name?", ["What's its name?", "Where name it?", "How got its?", "Is name have?"], "A follow-up question asks for a related detail."),
                mc(f"Select the well-ordered profile sentence for {name}.", "Выбери предложение с правильным порядком слов.", f"{name} has got {item}, but {pronoun.lower()} hasn't got {second_item}.", [f"{name} has got {item}, but {pronoun.lower()} hasn't got {second_item}.", f"Has {name} {item}, but not got {second_item}.", f"{name} got has {item} and hasn't {second_item} got.", f"{pronoun} {name} has {item} got."], "Place has got after the subject and hasn't got after but."),
            ],
            "fill_blank": [
                fill(f"Complete the phone interview: 'Have you got any pets?' 'Yes, I ___.'.", "Заверши телефонное интервью.", "have", "Use have in a short answer to Have you got...?"),
                fill(f"Complete the connected answer: I've got {item}, ___ I haven't got {second_item}.", "Свяжи две части ответа.", "but", "Use but to contrast a positive and a negative fact."),
            ],
            "listening": [
                listening(f"Listen to the full profile at {scenario.lower()}. Which statement is true?", "Послушай профиль и выбери верное утверждение.", f"I'm {name} from {data['city']}. I'm a {data['job']}. I've got {item} and a {pet}, but I haven't got {second_item}.", f"{name} has got {item}.", [f"{name} has got {item}.", f"{name} is from {data['country']} city.", f"{name} has got {second_item}.", f"{name} has no pet."], "The correct statement repeats one explicit detail."),
                listening(f"Listen to two answers. Who has got the {pet}?", "Послушай два ответа.", f"{name} has got a {pet}. {data['second_name']} has got {second_item}, but no pets.", name, [name, data["second_name"], "both people", "neither person"], "Only the first person is described with the pet."),
            ],
            "speech": [
                speech_repeat(f"Repeat the connected contrast at {scenario.lower()}.", "Повтори связное противопоставление.", f"I've got {item}, but I haven't got {second_item}.", "The app checks the transcript, not pronunciation quality."),
                speech_response(f"Without a complete model, answer two questions: Where are you from, and what have you got for a trip?", "Без полного образца назови происхождение и вещь для поездки.", [f"I'm from {data['city']}, and I've got {item}"], ["from", "got"], ["to_be", "have_got"], 8, "The answer should combine origin and possession.", False),
            ],
        }

    return {
        "multiple_choice": [
            mc(f"During {scenario.lower()}, choose the accurate mixed profile.", "Выбери точный смешанный профиль.", f"{name} is from {data['country']} and has got {item}.", [f"{name} is from {data['country']} and has got {item}.", f"{name} are from {data['country']} and have got {item}.", f"Is {name} {data['country']} and got {item}.", f"{name} has from {data['country']} and is got {item}."], "Combine to be for origin with has got for possession."),
            mc(f"Choose the best follow-up after {name} says, 'I haven't got a ticket.'", "Выбери лучший уточняющий вопрос.", "Have you got your phone?", ["Have you got your phone?", "Are you got a phone?", "Where phone have?", "Has you a phone got?"], "A useful follow-up uses Have you got...?"),
        ],
        "fill_blank": [
            fill(f"Repair the expedition list: We ___ got three bags, but we haven't got a map.", "Исправь список экспедиции.", "have", "Use have got with we."),
            fill(f"Complete the identity check: {name} ___ from {data['city']} and has got a {pet}.", "Заверши проверку личности.", "is", "Use is for origin before has got adds another detail."),
        ],
        "listening": [
            listening(f"Listen during {scenario.lower()}. What must the team still find?", "Послушай и выбери недостающую вещь.", f"We've got {item}, {second_item} and water. We haven't got the tickets yet.", "tickets", ["tickets", item, second_item, "water"], "The missing item follows haven't got."),
            listening(f"Listen to the corrected profile. Which two details belong to {name}?", "Послушай исправленный профиль.", f"The first card is wrong. {name} is from {data['country']} and has got a {pet}, not a rabbit.", f"{data['country']} and a {pet}", [f"{data['country']} and a {pet}", f"{data['city']} and a rabbit", f"Canada and {item}", f"{data['country']} and no pet"], "The correction states both origin and pet."),
        ],
        "speech": [
            speech_repeat(f"Rehearse the expedition check for {scenario.lower()}.", "Повтори проверку перед экспедицией.", "We've got our bags, but we haven't got the tickets.", "The transcript checks the contrast and required items."),
            speech_response(f"Complete the mission: introduce yourself and give at least three personal details, including one possession.", "Заверши миссию: представься и назови минимум три детали, включая одну вещь.", [f"I'm {name}. I'm from {data['city']}. I'm a {data['job']}, and I've got {item}."], ["i", "from", "got"], ["to_be", "have_got", "personal_information"], 12, "A complete mission response combines identity, origin and possession.", False),
        ],
    }


def stage_name(point_number: int) -> str:
    return (
        "introduction" if point_number <= 10 else
        "guided_practice" if point_number <= 20 else
        "context_application" if point_number <= 30 else
        "independent_use" if point_number <= 40 else
        "review_mission"
    )


def build_exercise(
    location_id: int,
    point_number: int,
    exercise_number: int,
    exercise_type: str,
    seed: dict,
    grammar_tags: list[str],
    vocabulary_tags: list[str],
) -> dict:
    difficulty = ((point_number - 1) // 10) + 1
    exercise = {
        "id": f"L{location_id:03d}-P{point_number:02d}-E{exercise_number}",
        "cefr": "A2",
        "location_id": location_id,
        "point_id": point_number,
        "type": exercise_type,
        "skill": {
            "multiple_choice": "grammar_recognition",
            "fill_blank": "grammar_production",
            "listening": "listening_comprehension",
            "speech": "spoken_production",
        }[exercise_type],
        "grammar_tags": grammar_tags,
        "vocabulary_tags": vocabulary_tags,
        "difficulty": difficulty,
        **seed,
    }
    options = exercise.get("options")
    if options:
        shift = (location_id + point_number + exercise_number) % len(options)
        exercise["options"] = options[shift:] + options[:shift]
    return exercise


def build_location(location_id: int, manifest_location: dict) -> dict:
    titles = LOCATION_ONE_TITLES if location_id == 1 else LOCATION_TWO_TITLES
    points = []

    for point_number in range(1, 51):
        data = profile(point_number + ((location_id - 1) * 9))
        stage = stage_name(point_number)
        if location_id == 1:
            pools = location_one_pools(point_number, data)
            grammar_tags = (
                ["to_be", "personal_pronouns", "word_order"]
                if point_number <= 20 else
                ["to_be", "wh_questions", "personal_information"]
            )
            vocabulary_tags = ["greetings", "countries", "jobs", "personal_information"]
        else:
            pools = location_two_pools(point_number, data)
            grammar_tags = ["have_got", "wh_questions", "personal_information"]
            if point_number >= 41:
                grammar_tags += ["to_be", "personal_pronouns", "word_order"]
            vocabulary_tags = ["possessions", "family", "pets", "personal_information"]

        exercises = []
        used_per_type = {exercise_type: 0 for exercise_type in TYPES}
        for exercise_number, exercise_type in enumerate(
            TYPE_ORDERS[(point_number - 1) % len(TYPE_ORDERS)],
            start=1,
        ):
            pool_index = used_per_type[exercise_type]
            used_per_type[exercise_type] += 1
            exercise = build_exercise(
                    location_id,
                    point_number,
                    exercise_number,
                    exercise_type,
                    pools[exercise_type][pool_index],
                    grammar_tags,
                    vocabulary_tags,
                )
            scenario = titles[point_number - 1]
            prompt = exercise["prompt"]
            prompt = prompt.replace(f"At {scenario.lower()}", "In this scene")
            prompt = prompt.replace(f"at {scenario.lower()}", "in this scene")
            prompt = prompt.replace(f"During {scenario.lower()}", "In this scene")
            prompt = prompt.replace(f"during {scenario.lower()}", "in this scene")
            exercise["prompt"] = f"{scenario} — {prompt}"
            exercises.append(exercise)

        global_point_id = ((location_id - 1) * 50) + point_number
        points.append(
            {
                "id": global_point_id,
                "location_id": location_id,
                "point_number": point_number,
                "title": titles[point_number - 1],
                "stage": stage,
                "cefr": "A2",
                "boss": point_number == 50,
                "grammar_tags": grammar_tags,
                "vocabulary_tags": vocabulary_tags,
                "grammar_help": {
                    "title": manifest_location["title"],
                    "summary": manifest_location["grammar_summary"],
                    "rules": manifest_location["grammar"],
                    "examples": [
                        {
                            "en": exercises[0].get("audio_text", exercises[0]["prompt"]),
                            "ru": exercises[0]["translation"],
                        },
                        {
                            "en": exercises[-1].get("phrase", exercises[-1]["prompt"]),
                            "ru": exercises[-1]["translation"],
                        },
                    ],
                },
                "exercises": exercises,
            }
        )

    return {
        **manifest_location,
        "name": manifest_location["title"],
        "description": manifest_location["communicative_goal"],
        "points": points,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    locations = [
        build_location(location_id, manifest["locations"][location_id - 1])
        for location_id in (1, 2)
    ]
    output = {
        "schema_version": 2,
        "locations": locations,
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    count = sum(len(point["exercises"]) for location in locations for point in location["points"])
    print(f"Wrote {len(locations)} locations, 100 points and {count} exercises")


if __name__ == "__main__":
    main()
