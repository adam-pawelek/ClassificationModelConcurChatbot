import openai
import os
from PyPDF2 import PdfReader
import json

CHATGPT_MODEL = "gpt-4o"
client = None
MAX_LENGTH = 1000


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


def main():
    folder_path = 'tutorials'
    all_synthetic_data = []

    for filename in os.listdir(folder_path):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(folder_path, filename)
            print(f'Extracting text from: {filename}')
            text_content = extract_text_from_pdf(pdf_path)
            synthetic_data = generate_questions_from_text(text_content)
            all_synthetic_data.extend(synthetic_data)
            print(json.dumps(synthetic_data, indent=4))
            print('\n' + '-' * 80 + '\n')

    # Save the synthetic data to a file
    with open('synthetic_data.json', 'w') as outfile:
        json.dump(all_synthetic_data, outfile, indent=4)


if __name__ == "__main__":
    main()
