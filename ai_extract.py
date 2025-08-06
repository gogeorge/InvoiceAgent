import openai
import re
from config import openai_client

def extract_invoice_data(text):
    prompt = f"""Extract the following details from the invoice text:
    - Client Name
    - Invoice Date
    - Total Amount

    Invoice Text:
    {text}

    Format the output as:
    Client: <client>
    Date: <date>
    Amount: <amount>"""
    
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=100
    )
    
    response_text = response.choices[0].message.content.strip()
    match = re.search(r'Client:\s*(.+)\nDate:\s*(.+)\nAmount:\s*(.+)', response_text)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None