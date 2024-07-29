import copy
import random
import pandas as pd
import openai
import os
from PyPDF2 import PdfReader
import json

CHATGPT_MODEL = "gpt-4o"
client = None
MAX_LENGTH = 4096


def set_openai_api_key(api_key):
    global client
    client = openai
    client.api_key = api_key


set_openai_api_key(os.environ["OPENAI_API_KEY"])


def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text


def generate_questions_from_text(text, num_questions=20):
    messages = [
        {"role": "system", "content": "Your job is to create questions based on the provided tutorial to Concur (you should ask questions which user would normally ask)."},
        {"role": "user",
         "content": f"Generate {num_questions} questions based on the following text:\n{text}\nEnsure the response is in the following JSON format:\n[\n[{{\"role\": \"user\", \"content\": \"question 1\"}}],\n[{{\"role\": \"user\", \"content\": \"question 2\"}}],\n... \n]"}
    ]

    response = client.chat.completions.create(
        model=CHATGPT_MODEL,
        messages=messages,
        max_tokens=MAX_LENGTH,
    )

    try:
        print(response.choices[0].message.content)
        synthetic_data = json.loads(response.choices[0].message.content)
        print(synthetic_data)
    except json.JSONDecodeError:
        print("Response not in JSON format. Asking ChatGPT to correct it.")
        correction_messages = [
            {"role": "system", "content": "Your job is to correct the format of the questions."},
            {"role": "user",
             "content": f"The previous response was not in the correct format. Ensure the response is in the following JSON format:\n[\n[{{\"role\": \"user\", \"content\": \"question 1\"}}],\n[{{\"role\": \"user\", \"content\": \"question 2\"}}],\n... \n]\nHere are the questions to reformat:\n{response.choices[0].message['content']}"}
        ]

        response = client.chat.completions.create(
            model=CHATGPT_MODEL,
            messages=correction_messages,
            max_tokens=MAX_LENGTH,
        )

        synthetic_data = json.loads(response.choices[0].message.content)

    return synthetic_data



def generate_follow_up_questions_from_text(history_conversation,text):
    if random.randint(0,3) >= 2:
        messages = [
            {"role": "system", "content": "Your job is to create (very short!!! and not formal!!!!) follow up question based on the provided history of conversation (make sure that this question is connected to history of conversation) and  tutorial to Concur (you should ask questions which user would normally ask)."},
            {"role": "user",
             "content": f"Generate question based on the conversation history {history_conversation} and following Concur tutorial text:\n{text}\nEnsure the response is in the following JSON format:{{\"role\": \"user\", \"content\": \"question\"}}] (don't write ```json)"}
        ]
        print("short and not formal")
    else:
        messages = [
            {"role": "system",
             "content": "Your job is to create follow up question based on the provided history of conversation (make sure that this question is connected to history of conversation) and  tutorial to Concur (you should ask questions which user would normally ask)."},
            {"role": "user",
             "content": f"Generate question based on the conversation history {history_conversation} and following Concur tutorial text:\n{text}\nEnsure the response is in the following JSON format:{{\"role\": \"user\", \"content\": \"question\"}}] (don't write ```json)"}
        ]

    response = client.chat.completions.create(
        model=CHATGPT_MODEL,
        messages=messages,
        max_tokens=MAX_LENGTH,
    )

    try:
        print(response.choices[0].message.content)
        synthetic_data = json.loads(response.choices[0].message.content)
        print(synthetic_data)
    except json.JSONDecodeError:
        print("Response not in JSON format. Asking ChatGPT to correct it.")
        correction_messages = [
            {"role": "system", "content": "Your job is to correct the format of the questions."},
            {"role": "user",
             "content": f"The previous response was not in the correct format. Ensure the response is in the following JSON format:\n{{\"role\": \"user\", \"content\": \"question\"}}\nHere are the questions to reformat:\n{response.choices[0].message['content']}, (don't write ```json)"}
        ]

        response = client.chat.completions.create(
            model=CHATGPT_MODEL,
            messages=correction_messages,
            max_tokens=MAX_LENGTH,
        )

        synthetic_data = json.loads(response.choices[0].message.content)

    return synthetic_data




def create_answer(question, text):
    messages = [
        {"role": "system", "content": "Your job is to create an answer based on the provided question"},
        {"role": "user",
         "content": f"Answer question '{question}' based on the following text:\n{text}\nEnsure the response is in the following JSON format: {{\"role\": \"system\", \"content\": \"Answer for question\"}}, IMPORTANT -> don't write ```json in answer"}
    ]
    response = client.chat.completions.create(
        model=CHATGPT_MODEL,
        messages=messages,
        max_tokens=MAX_LENGTH,
    )

    try:
        print(response.choices[0].message.content)
        synthetic_data = json.loads(response.choices[0].message.content)
        print(synthetic_data)
        return synthetic_data
    except json.JSONDecodeError:
        try:
            print("Response not in JSON format. Asking ChatGPT to correct it.")
            correction_messages = [
                {"role": "system", "content": "Your job is to correct the format of the questions. and answer"},
                {"role": "user",
                    "content": f"The previous response was not in the correct format. Ensure the response is in the following JSON format: {{\"role\": \"system\", \"content\": \"Answer for question\"}}\n Here are the answer to reformat:\n{copy.deepcopy(response.choices[0].message.content)} use \n instead of newline. it should be later converted to json, IMPORTANT -> don't write ```json in answer"
                 }
            ]

            response = client.chat.completions.create(
                model=CHATGPT_MODEL,
                messages=correction_messages,
                max_tokens=MAX_LENGTH,
            )
            print("Error")
            print(response.choices[0].message.content)
            synthetic_data = json.loads(response.choices[0].message.content)
            return synthetic_data
        except json.JSONDecodeError:
            text = """
            {
                "role": "system",
                "content": "I'm sorry I don't know how to answer this question."        
            }
            """
            return json.loads(text)




def main():
    folder_path = 'tutorials'
    all_synthetic_data = []


    for filename in os.listdir(folder_path):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(folder_path, filename)
            print(f'Extracting text from: {filename}')
            text_content = extract_text_from_pdf(pdf_path)
            synthetic_questions = generate_questions_from_text(text_content)
            print(synthetic_questions)
            print("lenght of synthetic_data", len(synthetic_questions))
            for indx, syn_data in enumerate(synthetic_questions):
                print(syn_data)
                print(indx)
                synthetic_answer = [syn_data[0]]
                all_synthetic_data.append(copy.deepcopy(synthetic_answer))
                for i in range(random.randint(1, 3)):
                    synthetic_answer.append(copy.deepcopy(create_answer(synthetic_answer, text_content)))
                    all_synthetic_data.append(copy.deepcopy(synthetic_answer))
                    print("answer")
                    print(synthetic_answer)
                    synthetic_answer.append(copy.deepcopy(generate_follow_up_questions_from_text(synthetic_answer, text_content)))
                    all_synthetic_data.append(copy.deepcopy(synthetic_answer))
                    print("foolow up")
                    print(synthetic_answer)



            print(synthetic_questions)
            print('\n' + '-' * 80 + '\n')

    df = pd.DataFrame({
        'text': all_synthetic_data,
        'category': ['question assistant'] * len(all_synthetic_data)
    })
    #CSV
    csv_filename = 'output.csv'
    df.to_csv(csv_filename, index=False)

    excel_filename = 'output.xlsx'
    df.to_excel(excel_filename, index=False)

    json_filename = 'output.json'
    df.to_json(json_filename, orient='records')

    print(f"CSV file '{csv_filename}' has been created.")
    print(f"Excel file '{excel_filename}' has been created.")
    print(f"JSON file '{json_filename}' has been created.")




if __name__ == "__main__":
    main()
