import openai
import re

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
    
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=100
    )
    match = re.search(r'Client:\s*(.+)\nDate:\s*(.+)\nAmount:\s*(.+)', response.choices[0].text.strip())
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None