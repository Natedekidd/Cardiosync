"""
messaging_client.py
Handles WhatsApp and SMS message delivery via Twilio
"""

import os

# Try to import Twilio
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False


def send_whatsapp_message(to_number, message_body):
    """
    Send WhatsApp message using Twilio
    
    Args:
        to_number (str): Recipient's phone number (e.g., "+2348012345678")
        message_body (str): Message content to send
        
    Returns:
        tuple: (success: bool, message: str)
    """
    if not TWILIO_AVAILABLE:
        return False, "Twilio not installed. Run: pip install twilio"
    
    try:
        # Get Twilio credentials from Streamlit secrets
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        from_whatsapp = os.environ.get("TWILIO_PHONE_NUMBER")
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Format phone number for WhatsApp
        if not to_number.startswith("whatsapp:"):
            to_whatsapp = f"whatsapp:{to_number}"
        else:
            to_whatsapp = to_number
        
        # Send message
        message = client.messages.create(
            body=message_body,
            from_=from_whatsapp,
            to=to_whatsapp
        )
        
        return True, f"Message sent successfully! SID: {message.sid}"
    
    except KeyError as e:
        return False, f"Missing Twilio configuration: {str(e)}"
    except Exception as e:
        return False, f"Error sending WhatsApp: {str(e)}"


def send_sms_message(to_number, message_body):
    """
    Send SMS using Twilio
    
    Args:
        to_number (str): Recipient's phone number (e.g., "+2348012345678")
        message_body (str): Message content to send (max 160 characters)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    if not TWILIO_AVAILABLE:
        return False, "Twilio not installed. Run: pip install twilio"
    
    try:
        # Get Twilio credentials from Streamlit secrets
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        from_number = os.environ.get("TWILIO_PHONE_NUMBER")
        
        if not from_number:
            return False, "SMS number not configured in secrets"
        
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Send SMS
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number
        )
        
        return True, f"SMS sent successfully! SID: {message.sid}"
    
    except KeyError as e:
        return False, f"Missing Twilio configuration: {str(e)}"
    except Exception as e:
        return False, f"Error sending SMS: {str(e)}"


def create_whatsapp_report_summary(patient_data, total_risk, genomic_factor, top_recommendations):
    """
    Create a concise WhatsApp-friendly report summary
    
    Args:
        patient_data (dict): Patient information
        total_risk (float): Calculated risk percentage
        genomic_factor (float): Genetic risk contribution
        top_recommendations (list): List of recommendation strings
        
    Returns:
        str: Formatted WhatsApp message
    """
    risk_emoji = "🔴" if total_risk > 20 else "🟡" if total_risk > 10 else "🟢"
    
    message = f"""🫀 *CardioSync Health Report*

Hi {patient_data['name']},

Your 10-year cardiovascular risk: *{total_risk:.1f}%* {risk_emoji}

"""
    
    # Risk level interpretation
    if total_risk > 20:
        message += "*HIGH RISK* - See a doctor soon!\n\n"
    elif total_risk > 10:
        message += "*MODERATE RISK* - Lifestyle changes needed\n\n"
    else:
        message += "*LOW RISK* - Keep up the good work!\n\n"
    
    # Top risk factors
    message += "*Top Risk Factors:*\n"
    
    concerns = []
    if patient_data.get('smoking') == "Current":
        concerns.append("• 🚭 Smoking (Biggest concern!)")
    if patient_data.get('bp_systolic', 0) > 140:
        concerns.append(f"• ⬆️ High blood pressure ({patient_data['bp_systolic']}/{patient_data['bp_diastolic']})")
    if patient_data.get('ldl', 0) > 160:
        concerns.append(f"• 💉 High cholesterol (LDL: {patient_data['ldl']})")
    if patient_data.get('exercise_days', 7) < 3:
        concerns.append("• 🏃 Not enough exercise")
    if genomic_factor > 5:
        concerns.append(f"• 🧬 Genetic risk: {patient_data['genomic_risk']:.1f}x average")
    
    # Add top 3-4 concerns
    for concern in concerns[:4]:
        message += concern + "\n"
    
    # Recommendations
    message += "\n*What to Do:*\n"
    for i, rec in enumerate(top_recommendations[:3], 1):
        # Clean up formatting for WhatsApp
        clean_rec = rec.replace("**", "").replace("*", "").split("-")[0].strip()
        # Remove emoji if present at start
        if clean_rec and clean_rec[0] in ['🚭', '🏃', '🥗', '💊']:
            clean_rec = clean_rec[2:].strip()
        message += f"{i}. {clean_rec}\n"
    
    message += "\n📄 Full report available for download in app\n"
    message += "\n⚠️ _This is not a diagnosis. Consult your doctor._\n"
    message += "\n---\nCardioSync - Your Digital Heart Twin"
    
    return message


def create_sms_report_summary(patient_data, total_risk):
    """
    Create ultra-short SMS version (160 character limit)
    
    Args:
        patient_data (dict): Patient information
        total_risk (float): Calculated risk percentage
        
    Returns:
        str: Formatted SMS message (max 160 characters)
    """
    risk_level = "HIGH" if total_risk > 20 else "MODERATE" if total_risk > 10 else "LOW"
    
    # Start with basic info
    message = f"CardioSync: {patient_data['name']}, your CVD risk is {total_risk:.1f}% ({risk_level}). "
    
    # Add urgency if needed
    if total_risk > 20:
        message += "See doctor ASAP. "
    elif total_risk > 10:
        message += "Lifestyle changes needed. "
    
    # Add one main actionable item
    if patient_data.get('smoking') == "Current":
        message += "Quit smoking!"
    elif patient_data.get('bp_systolic', 0) > 140:
        message += "Control BP!"
    elif patient_data.get('exercise_days', 7) < 3:
        message += "Exercise more!"
    elif patient_data.get('ldl', 0) > 160:
        message += "Check cholesterol!"
    else:
        message += "Keep it up!"
    
    # Ensure within SMS limit
    return message[:160]



def validate_phone_number(phone_number):
    """
    Validate phone number format
    
    Args:
        phone_number (str): Phone number to validate
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    # Remove spaces and dashes
    phone = phone_number.replace(" ", "").replace("-", "")
    
    # Check if it starts with +
    if not phone.startswith("+"):
        return False, "Phone number must start with country code (e.g., +234)"
    
    # Check minimum length (country code + number)
    if len(phone) < 10:
        return False, "Phone number too short"
    
    # Check if it contains only digits after the +
    if not phone[1:].isdigit():
        return False, "Phone number must contain only digits after +"
    
    # Nigerian number specific validation (optional)
    if phone.startswith("+234"):
        if len(phone) != 14:  # +234 + 10 digits
            return False, "Nigerian number should be +234 followed by 10 digits"
    
    return True, None