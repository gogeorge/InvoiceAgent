import openai
import re
from config import openai_client
import unicodedata

# === TRANSLITERATION (Greek -> Latin) ===
# Map common Greek characters to Latin approximations
TRANSLITERATION_MAP = {
    # Uppercase
    'Α': 'A', 'Β': 'B', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E', 'Ζ': 'Z', 'Η': 'I', 'Θ': 'TH',
    'Ι': 'I', 'Κ': 'K', 'Λ': 'L', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'X', 'Ο': 'O', 'Π': 'P',
    'Ρ': 'R', 'Σ': 'S', 'Τ': 'T', 'Υ': 'Y', 'Φ': 'F', 'Χ': 'CH', 'Ψ': 'PS', 'Ω': 'O',
    # Lowercase
    'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'i', 'θ': 'th',
    'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o', 'π': 'p',
    'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't', 'υ': 'y', 'φ': 'f', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o',
}

def transliterate_text(text: str) -> str:
    """Convert Greek characters in text to Latin using TRANSLITERATION_MAP.
    Removes diacritics and leaves non-Greek characters untouched.
    Example: "ΤΔΑ 34" -> "TDA 34"
    """
    if not text:
        return text
    # Decompose characters to strip diacritics (τονους)
    decomposed = unicodedata.normalize('NFD', text)
    stripped = ''.join(ch for ch in decomposed if unicodedata.category(ch) != 'Mn')
    # Map character-by-character
    return ''.join(TRANSLITERATION_MAP.get(ch, ch) for ch in stripped)

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


def build_invoice_filename(invoice_number, client, date, amount):
    """
    Build a human-friendly invoice filename using AI-extracted fields.
    Example: "TDA 34 - 15 06 2025 CLIENTNAME.pdf"
    """
    parts = []
    if invoice_number and invoice_number != "N/A":
        parts.append(transliterate_text(str(invoice_number)) + ' -')
    if date:
        parts.append(' '.join(reversed(date.split('/'))))
    if client:
        parts.append(transliterate_text(client))
    if not parts:
        return "invoice.pdf"
    print(" ".join(parts) + ".pdf")
    return " ".join(parts) + ".pdf"
