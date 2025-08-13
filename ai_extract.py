import openai
import re
from config import openai_client

def extract_invoice_data(text):
    prompt = f"""Extract the following details from the invoice text:
    - Invoice Number
    - Client Name
    - Invoice Date
    - Total Amount
    - The number of days that is written as a comment in a box at the bottom (The deadline for the invoice payment)

    Invoice Text:
    {text}

    Format the output as:
    Invoice Number: <invoice_number>
    Client: <client>
    Date: <date>
    Amount: <amount>
    Days: <days>"""
    
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=200
    )
    
    response_text = response.choices[0].message.content.strip()
    print(f"AI Response: {response_text}")
    
    # Try multiple regex patterns to handle different orderings
    patterns = [
        r'Client:\s*(.+?)(?:\n|$).*?Date:\s*(.+?)(?:\n|$).*?Amount:\s*(.+?)(?:\n|$)',
        r'Client:\s*(.+?)(?:\n|$).*?Amount:\s*(.+?)(?:\n|$).*?Date:\s*(.+?)(?:\n|$)',
        r'Date:\s*(.+?)(?:\n|$).*?Client:\s*(.+?)(?:\n|$).*?Amount:\s*(.+?)(?:\n|$)',
        r'Date:\s*(.+?)(?:\n|$).*?Amount:\s*(.+?)(?:\n|$).*?Client:\s*(.+?)(?:\n|$)',
        r'Amount:\s*(.+?)(?:\n|$).*?Client:\s*(.+?)(?:\n|$).*?Date:\s*(.+?)(?:\n|$)',
        r'Amount:\s*(.+?)(?:\n|$).*?Date:\s*(.+?)(?:\n|$).*?Client:\s*(.+?)(?:\n|$)'
    ]
    
    # Try to extract all fields using a more flexible approach
    client_match = re.search(r'Client:\s*(.+?)(?:\n|$)', response_text, re.DOTALL)
    date_match = re.search(r'Date:\s*(.+?)(?:\n|$)', response_text, re.DOTALL)
    amount_match = re.search(r'Amount:\s*(.+?)(?:\n|$)', response_text, re.DOTALL)
    invoice_number_match = re.search(r'Invoice Number:\s*(.+?)(?:\n|$)', response_text, re.DOTALL)
    days_match = re.search(r'Days:\s*(.+?)(?:\n|$)', response_text, re.DOTALL)
    
    if client_match and date_match and amount_match:
        client = client_match.group(1).strip()
        date = date_match.group(1).strip()
        amount = amount_match.group(1).strip()
        invoice_number = invoice_number_match.group(1).strip() if invoice_number_match else "N/A"
        days = days_match.group(1).strip() if days_match else "N/A"
        
        return client, date, amount, invoice_number, days
    
    print("Could not extract required fields (Client, Date, Amount)")
    return None, None, None, None, None