"""
TELESEHAT - Telemedicine Platform
Fixed for deployment on Render/PythonAnywhere
Run: gunicorn app:server
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context, ALL, MATCH
import dash_bootstrap_components as dbc
import sqlite3
import uuid
from datetime import datetime, date
import google.generativeai as genai
import pandas as pd
import json
import re
import time
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import io
from PIL import Image
import os

# ========== FIX: Use environment variable for API key ==========
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6IXbccgKM-YWMYBp_4O6IyBQkQgoD3SdVeh3JW_mNyhyA")
AGORA_APP_ID = os.environ.get("AGORA_APP_ID", "79900bea4285434da3095127036de80a")

# ========== FIX: Database path for deployment ==========
# Use /tmp for Vercel or current directory for Render
DB_PATH = '/tmp/telesehat.db' if os.environ.get('VERCEL') else 'telesehat.db'

# ========== Fix for Python 3.12 SQLite datetime adapter ==========
def adapt_datetime(dt):
    return dt.isoformat()

def convert_datetime(s):
    return datetime.fromisoformat(s.decode())

sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("TIMESTAMP", convert_datetime)

# ========== Initialize Gemini client ==========
try:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    gemini_vision_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Gemini client initialization failed: {e}")
    gemini_model = None
    gemini_vision_model = None

# ========== Initialize the app ==========
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.FLATLY,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
    ],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ]
)
app.title = "Telesehat - Telemedicine Platform"
server = app.server
app.config.suppress_callback_exceptions = True

# ========== Translations Dictionary (Abbreviated for space) ==========
translations = {
    "en": {
        "app_title": "Telesehat",
        "login_register": "Login/Register",
        "full_name": "Full Name",
        "select_role": "Select Role",
        "phone": "Phone Number",
        "village": "Village/City",
        "dob": "Date of Birth",
        "gender": "Gender",
        "male": "Male",
        "female": "Female",
        "other": "Other",
        "submit": "Submit",
        "welcome_back": "Welcome back {}!",
        "registration_success": "Registration successful!",
        "fill_all_fields": "Please fill all fields.",
        "patient": "Patient",
        "doctor": "Doctor",
        "pharmacy": "Pharmacy",
        "patient_dashboard": "Patient Dashboard",
        "doctor_dashboard": "Doctor Dashboard",
        "pharmacy_dashboard": "Pharmacy Dashboard",
        "patient_profile": "Patient Profile",
        "request_consultation": "Request Consultation",
        "consultation_reason": "Reason for consultation...",
        "request_consult_btn": "Request Consultation",
        "video_consultation": "Video Consultation",
        "ai_chatbot": "AI Chatbot",
        "ask_symptoms": "Ask about your symptoms...",
        "send": "Send",
        "medicine_availability": "Medicine Availability",
        "medicine_name": "Medicine name...",
        "search": "Search",
        "pending_consultations": "Pending Consultations",
        "update_stock": "Update Stock",
        "medicine_name_label": "Medicine Name",
        "quantity": "Quantity",
        "price": "Price",
        "update_stock_btn": "Update Stock",
        "current_stock": "Current Stock",
        "no_profile_data": "No profile data",
        "no_pending_consultations": "No pending consultations",
        "no_stock_records": "No stock records",
        "assistant_unavailable": "Sorry, the assistant is unavailable right now. Please try again later.",
        "consultation_requested": "Consultation requested successfully!",
        "stock_updated": "Stock updated successfully!",
        "no_results": "No results found",
        "enter_medicine_name": "Please enter a medicine name",
        "join_consultation": "Join Video Consultation",
        "consultation_instructions": "Click the button below to join your video consultation session. Make sure you have a working camera and microphone.",
        "join_button": "Join Now",
        "dark_mode": "Dark Mode",
        "light_mode": "Light Mode",
        "language": "Language",
        "accept": "Accept",
        "reject": "Reject",
        "patient_info": "Patient Info",
        "typing": "AI is typing...",
        "loading": "Loading...",
        "delete": "Delete",
        "edit": "Edit",
        "save": "Save",
        "actions": "Actions",
        "appointments": "Appointments",
        "schedule_appointment": "Schedule Appointment",
        "appointment_date": "Appointment Date",
        "appointment_time": "Appointment Time",
        "health_metrics": "Health Metrics",
        "blood_pressure": "Blood Pressure",
        "heart_rate": "Heart Rate",
        "temperature": "Temperature",
        "blood_sugar": "Blood Sugar",
        "add_metric": "Add Metric",
        "prescriptions": "Prescriptions",
        "write_prescription": "Write Prescription",
        "order_tracking": "Order Tracking",
        "manage_schedule": "Manage Schedule",
        "available_hours": "Available Hours",
        "day": "Day",
        "start_time": "Start Time",
        "end_time": "End Time",
        "add_slot": "Add Time Slot",
        "upcoming": "Upcoming",
        "past": "Past",
        "status": "Status",
        "date": "Date",
        "time": "Time",
        "tracking_id": "Tracking ID",
        "order_status": "Order Status",
        "track_order": "Track Order",
        "consultation_accepted": "Consultation accepted!",
        "consultation_rejected": "Consultation rejected!",
        "appointment_scheduled": "Appointment scheduled successfully!",
        "stock_deleted": "Stock item deleted successfully!",
        "error_occurred": "An error occurred. Please try again.",
        "logout": "Logout",
        "logout_success": "You have been logged out successfully!",
        "upload_image": "Upload Image",
        "image_analysis": "Image Analysis",
        "prescription_details": "Prescription Details",
        "medicine": "Medicine",
        "dosage": "Dosage",
        "instructions": "Instructions",
        "write_prescription_btn": "Write Prescription",
        "prescription_saved": "Prescription saved successfully!",
        "age": "Age",
        "years": "years",
        "select_doctor": "Select Doctor",
        "select_doctor_placeholder": "Choose a doctor...",
        "my_consultations": "My Consultations",
        "consultation_status": "Consultation Status",
        "requested": "Requested",
        "accepted": "Accepted",
        "rejected": "Rejected",
        "completed": "Completed",
        "no_consultations": "No consultations found",
        "view_details": "View Details",
        "consultation_details": "Consultation Details",
        "doctor": "Doctor",
        "reason": "Reason",
        "created": "Created",
        "no_doctor_available": "No doctors available"
    },
    "hi": {
        "app_title": "टेलीसेहत",
        "login_register": "लॉगिन/पंजीकरण",
        "full_name": "पूरा नाम",
        "select_role": "भूमिका चुनें",
        "phone": "फ़ोन नंबर",
        "village": "गाँव/शहर",
        "dob": "जन्म तिथि",
        "gender": "लिंग",
        "male": "पुरुष",
        "female": "महिला",
        "other": "अन्य",
        "submit": "जमा करें",
        "welcome_back": "वापसी पर स्वागत है {}!",
        "registration_success": "पंजीकरण सफल!",
        "fill_all_fields": "कृपया सभी फ़ील्ड भरें।",
        "patient": "मरीज़",
        "doctor": "डॉक्टर",
        "pharmacy": "फार्मेसी",
        "patient_dashboard": "मरीज़ डैशबोर्ड",
        "doctor_dashboard": "डॉक्टर डैशबोर्ड",
        "pharmacy_dashboard": "फार्मेसी डैशबोर्ड",
        "patient_profile": "मरीज़ प्रोफाइल",
        "request_consultation": "परामर्श का अनुरोध करें",
        "consultation_reason": "परामर्श का कारण...",
        "request_consult_btn": "परामर्श अनुरोध",
        "video_consultation": "वीडियो परामर्श",
        "ai_chatbot": "एआई चैटबॉट",
        "ask_symptoms": "अपने लक्षणों के बारे में पूछें...",
        "send": "भेजें",
        "medicine_availability": "दवा उपलब्धता",
        "medicine_name": "दवा का नाम...",
        "search": "खोजें",
        "pending_consultations": "लंबित परामर्श",
        "update_stock": "स्टॉक अपडेट करें",
        "medicine_name_label": "दवा का नाम",
        "quantity": "मात्रा",
        "price": "कीमत",
        "update_stock_btn": "स्टॉक अपडेट करें",
        "current_stock": "वर्तमान स्टॉक",
        "no_profile_data": "कोई प्रोफ़ाइल डेटा नहीं",
        "no_pending_consultations": "कोई लंबित परामर्श नहीं",
        "no_stock_records": "कोई स्टॉक रिकॉर्ड नहीं",
        "assistant_unavailable": "क्षमा करें, सहायक वर्तमान में उपलब्ध नहीं है। कृपया बाद में पुन: प्रयास करें।",
        "consultation_requested": "परामर्श सफलतापूर्वक अनुरोधित!",
        "stock_updated": "स्टॉक सफलतापूर्वक अपडेट किया गया!",
        "no_results": "कोई परिणाम नहीं मिला",
        "enter_medicine_name": "कृपया दवा का नाम दर्ज करें",
        "join_consultation": "वीडियो परामर्श में शामिल हों",
        "consultation_instructions": "अपने वीडियो परामर्श सत्र में शामिल होने के लिए नीचे दिए गए बटन पर क्लिक करें। सुनिश्चित करें कि आपके पास एक कार्यशील कैमरा और माइक्रोफोन है।",
        "join_button": "अभी जुड़ें",
        "dark_mode": "डार्क मोड",
        "light_mode": "लाइट मोड",
        "language": "भाषा",
        "accept": "स्वीकार करें",
        "reject": "अस्वीकार करें",
        "patient_info": "मरीज़ की जानकारी",
        "typing": "एआई टाइप कर रहा है...",
        "loading": "लोड हो रहा है...",
        "delete": "हटाएं",
        "edit": "संपादित करें",
        "save": "सहेजें",
        "actions": "कार्रवाई",
        "appointments": "अपॉइंटमेंट",
        "schedule_appointment": "अपॉइंटमेंट शेड्यूल करें",
        "appointment_date": "अपॉइंटमेंट की तारीख",
        "appointment_time": "अपॉइंटमेंट का समय",
        "health_metrics": "स्वास्थ्य माप",
        "blood_pressure": "ब्लड प्रेशर",
        "heart_rate": "हृदय गति",
        "temperature": "तापमान",
        "blood_sugar": "ब्लड शुगर",
        "add_metric": "माप जोड़ें",
        "prescriptions": "प्रिस्क्रिप्शन",
        "write_prescription": "प्रिस्क्रिप्शन लिखें",
        "order_tracking": "ऑर्डर ट्रैकिंग",
        "manage_schedule": "शेड्यूल प्रबंधित करें",
        "available_hours": "उपलब्ध समय",
        "day": "दिन",
        "start_time": "प्रारंभ समय",
        "end_time": "समाप्ति समय",
        "add_slot": "समय जोड़ें",
        "upcoming": "आगामी",
        "past": "पिछले",
        "status": "स्थिति",
        "date": "तारीख",
        "time": "समय",
        "tracking_id": "ट्रैकिंग आईडी",
        "order_status": "ऑर्डर स्थिति",
        "track_order": "ऑर्डर ट्रैक करें",
        "consultation_accepted": "परामर्श स्वीकृत!",
        "consultation_rejected": "परामर्श अस्वीकृत!",
        "appointment_scheduled": "अपॉइंटमेंट सफलतापूर्वक शेड्यूल किया गया!",
        "stock_deleted": "स्टॉक आइटम सफलतापूर्वक हटाया गया!",
        "error_occurred": "एक त्रुटि हुई। कृपया पुन: प्रयास करें।",
        "logout": "लॉग आउट",
        "logout_success": "आप सफलतापूर्वक लॉग आउट हो गए हैं!",
        "upload_image": "छवि अपलोड करें",
        "image_analysis": "छवि विश्लेषण",
        "prescription_details": "प्रिस्क्रिप्शन विवरण",
        "medicine": "दवा",
        "dosage": "खुराक",
        "instructions": "निर्देश",
        "write_prescription_btn": "प्रिस्क्रिप्शन लिखें",
        "prescription_saved": "प्रिस्क्रिप्शन सफलतापूर्वक सहेजा गया!",
        "age": "उम्र",
        "years": "वर्ष",
        "select_doctor": "डॉक्टर चुनें",
        "select_doctor_placeholder": "एक डॉक्टर चुनें...",
        "my_consultations": "मेरे परामर्श",
        "consultation_status": "परामर्श स्थिति",
        "requested": "अनुरोधित",
        "accepted": "स्वीकृत",
        "rejected": "अस्वीकृत",
        "completed": "पूर्ण",
        "no_consultations": "कोई परामर्श नहीं मिला",
        "view_details": "विवरण देखें",
        "consultation_details": "परामर्श विवरण",
        "doctor": "डॉक्टर",
        "reason": "कारण",
        "created": "बनाया गया",
        "no_doctor_available": "कोई डॉक्टर उपलब्ध नहीं"
    }
}

# ========== CUSTOM CSS ==========
custom_css = {
    "card": {
        "boxShadow": "0 4px 8px 0 rgba(0,0,0,0.1)",
        "borderRadius": "12px",
        "border": "none",
        "transition": "all 0.3s ease",
        "fontFamily": "'Inter', sans-serif"
    },
    "navbar": {
        "boxShadow": "0 2px 4px 0 rgba(0,0,0,0.1)",
        "marginBottom": "20px",
        "fontFamily": "'Inter', sans-serif",
        "padding": "0.5rem 1rem"
    },
    "chatUser": {
        "backgroundColor": "#e3f2fd",
        "padding": "12px 16px",
        "borderRadius": "18px 18px 4px 18px",
        "marginBottom": "8px",
        "maxWidth": "80%",
        "marginLeft": "auto",
        "fontFamily": "'Inter', sans-serif",
        "color": "#1a56db"
    },
    "chatAI": {
        "backgroundColor": "#f3f4f6",
        "padding": "12px 16px",
        "borderRadius": "18px 18px 18px 4px",
        "marginBottom": "8px",
        "maxWidth": "80%",
        "fontFamily": "'Inter', sans-serif",
        "color": "#374151"
    },
    "tab_selected": {
        "backgroundColor": "#1a56db",
        "color": "white",
        "border": "none",
        "fontWeight": "600",
        "fontFamily": "'Inter', sans-serif",
        "borderRadius": "8px 8px 0 0"
    },
    "tab": {
        "backgroundColor": "#f9fafb",
        "color": "#6b7280",
        "border": "none",
        "fontFamily": "'Inter', sans-serif",
        "fontWeight": "500",
        "borderRadius": "8px 8px 0 0"
    },
    "primary_color": "#1a56db",
    "secondary_color": "#0e9f6e",
    "accent_color": "#9061f9",
    "light_bg": "#f9fafb"
}

# ========== DATABASE FUNCTIONS ==========
def init_db():
    """Initialize database with all tables"""
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id TEXT PRIMARY KEY, name TEXT, role TEXT, phone TEXT, 
                 village TEXT, dob TEXT, gender TEXT, created_at TIMESTAMP)''')
    
    # Create consultations table
    c.execute('''CREATE TABLE IF NOT EXISTS consultations
                 (id TEXT PRIMARY KEY, patient_id TEXT, doctor_id TEXT,
                 status TEXT, reason TEXT, channel TEXT,
                 created_at TIMESTAMP, updated_at TIMESTAMP)''')
    
    # Create pharmacy_stock table
    c.execute('''CREATE TABLE IF NOT EXISTS pharmacy_stock
                 (id TEXT PRIMARY KEY, pharmacy_id TEXT, medicine TEXT,
                 qty INTEGER, price REAL, last_updated TIMESTAMP)''')
    
    # Create appointments table
    c.execute('''CREATE TABLE IF NOT EXISTS appointments
                 (id TEXT PRIMARY KEY, patient_id TEXT, doctor_id TEXT,
                 date TEXT, time TEXT, reason TEXT, status TEXT,
                 created_at TIMESTAMP, updated_at TIMESTAMP)''')
    
    # Create health_metrics table
    c.execute('''CREATE TABLE IF NOT EXISTS health_metrics
                 (id TEXT PRIMARY KEY, patient_id TEXT, blood_pressure TEXT,
                 heart_rate INTEGER, temperature REAL, blood_sugar REAL,
                 recorded_at TIMESTAMP)''')
    
    # Create prescriptions table
    c.execute('''CREATE TABLE IF NOT EXISTS prescriptions
                 (id TEXT PRIMARY KEY, patient_id TEXT, doctor_id TEXT,
                 medicine TEXT, dosage TEXT, instructions TEXT,
                 prescribed_at TIMESTAMP)''')
    
    # Create doctor_schedule table
    c.execute('''CREATE TABLE IF NOT EXISTS doctor_schedule
                 (id TEXT PRIMARY KEY, doctor_id TEXT, day TEXT,
                 start_time TEXT, end_time TEXT)''')
    
    # Insert sample doctors
    c.execute("SELECT COUNT(*) FROM users WHERE role = 'doctor'")
    if c.fetchone()[0] == 0:
        sample_doctors = [
            (str(uuid.uuid4()), 'Dr. Sharma', 'doctor', '9876543210', 'Delhi', '1975-05-15', 'male', datetime.now()),
            (str(uuid.uuid4()), 'Dr. Patel', 'doctor', '9876543211', 'Mumbai', '1980-08-22', 'female', datetime.now()),
            (str(uuid.uuid4()), 'Dr. Singh', 'doctor', '9876543212', 'Punjab', '1978-12-10', 'male', datetime.now()),
        ]
        c.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)", sample_doctors)
    
    # Insert sample pharmacy stock
    c.execute("SELECT COUNT(*) FROM pharmacy_stock")
    if c.fetchone()[0] == 0:
        sample_stock = [
            (str(uuid.uuid4()), 'pharmacy_1', 'Paracetamol', 100, 5.50, datetime.now()),
            (str(uuid.uuid4()), 'pharmacy_1', 'Amoxicillin', 50, 12.75, datetime.now()),
            (str(uuid.uuid4()), 'pharmacy_1', 'Ibuprofen', 75, 8.25, datetime.now()),
            (str(uuid.uuid4()), 'pharmacy_2', 'Paracetamol', 80, 5.25, datetime.now()),
            (str(uuid.uuid4()), 'pharmacy_2', 'Vitamin C', 120, 15.99, datetime.now()),
        ]
        c.executemany("INSERT INTO pharmacy_stock VALUES (?, ?, ?, ?, ?, ?)", sample_stock)
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# ========== HELPER FUNCTIONS ==========
def get_doctors(conn):
    """Get list of all doctors"""
    c = conn.cursor()
    c.execute("SELECT id, name FROM users WHERE role = 'doctor'")
    doctors = c.fetchall()
    return [{'label': doctor[1], 'value': doctor[0]} for doctor in doctors]

def calculate_age(dob):
    if not dob:
        return None
    try:
        today = date.today()
        birth_date = datetime.strptime(dob, "%Y-%m-%d").date()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    except:
        return None

def create_chat_display(chat_history):
    """Create chat display from history"""
    chat_display = []
    for msg in chat_history:
        if msg['sender'] == 'user':
            if 'image' in msg:
                chat_display.append(
                    html.Div([
                        html.Div([
                            html.Img(
                                src=msg['image'],
                                style={"maxWidth": "100%", "maxHeight": "200px", "borderRadius": "8px"}
                            ),
                            html.Small(
                                msg['timestamp'],
                                style={'textAlign': 'right', 'display': 'block', 'color': '#6c757d'}
                            )
                        ], style={'textAlign': 'right'})
                    ], style={'marginBottom': '15px'})
                )
            else:
                chat_display.append(
                    html.Div([
                        html.Div(
                            msg['message'],
                            style=custom_css["chatUser"]
                        ),
                        html.Small(
                            msg['timestamp'],
                            style={'textAlign': 'right', 'display': 'block', 'color': '#6c757d'}
                        )
                    ], style={'marginBottom': '15px'})
                )
        else:
            chat_display.append(
                html.Div([
                    html.Div(
                        msg['message'],
                        style=custom_css["chatAI"]
                    ),
                    html.Small(
                        msg['timestamp'],
                        style={'color': '#6c757d'}
                    )
                ], style={'marginBottom': '15px'})
            )
    return chat_display

def create_consultation(conn, patient_id, doctor_id, reason):
    """Create a consultation request"""
    c = conn.cursor()
    consultation_id = str(uuid.uuid4())
    now = datetime.now()
    c.execute("INSERT INTO consultations VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (consultation_id, patient_id, doctor_id, 'requested', reason, 'general', now, now))
    conn.commit()
    return True

def upsert_pharmacy_stock(conn, pharmacy_id, medicine, qty, price):
    """Insert or update pharmacy stock"""
    c = conn.cursor()
    c.execute("SELECT id FROM pharmacy_stock WHERE pharmacy_id = ? AND medicine = ?", 
              (pharmacy_id, medicine))
    existing = c.fetchone()
    
    if existing:
        c.execute("UPDATE pharmacy_stock SET qty = ?, price = ?, last_updated = ? WHERE id = ?",
                  (qty, price, datetime.now(), existing[0]))
    else:
        c.execute("INSERT INTO pharmacy_stock VALUES (?, ?, ?, ?, ?, ?)",
                  (str(uuid.uuid4()), pharmacy_id, medicine, qty, price, datetime.now()))
    conn.commit()
    return True

# ========== APP LAYOUT ==========
def create_layout():
    return html.Div([
        dbc.Container([
            html.Div(id="toast-container"),
            
            # Navbar
            dbc.Navbar(
                [
                    dbc.Row([
                        dbc.Col([
                            html.H1([
                                html.I(className="fas fa-hospital me-2", style={"color": custom_css["primary_color"]}),
                                html.Span(id="app-title", style={"color": custom_css["primary_color"], "fontWeight": "700"})
                            ], className="d-flex align-items-center mb-0")
                        ], width="auto", className="me-auto"),
                        dbc.Col([
                            dcc.Dropdown(
                                id='language-selector',
                                options=[
                                    {'label': 'English', 'value': 'en'},
                                    {'label': 'Hindi', 'value': 'hi'}
                                ],
                                value='en',
                                clearable=False,
                                style={'width': '120px', 'marginRight': '10px'},
                                className="d-inline-block"
                            ),
                            html.Div(id="logout-button-container", className="d-inline-block")
                        ], width="auto", className="d-flex align-items-center")
                    ], align="center", className="g-0 w-100"),
                ],
                color="white",
                sticky="top",
                style=custom_css["navbar"],
                className="px-3"
            ),
            
            # Tabs
            dcc.Tabs(id='tabs', value='tab-login', children=[], className="mb-3"),
            
            # Tab content
            html.Div(id='tab-content', className='mt-4'),
            
            # Stores
            dcc.Store(id='user-store', storage_type='session'),
            dcc.Store(id='language-store', data='en', storage_type='session'),
            dcc.Store(id='chat-history-store', data=[], storage_type='session'),
            dcc.Store(id='consultation-data', data={}, storage_type='session'),
            dcc.Store(id='appointment-data', data={}, storage_type='session'),
            dcc.Store(id='health-metrics-data', data={}, storage_type='session'),
            dcc.Store(id='pharmacy-stock-data', data={}, storage_type='session'),
            dcc.Store(id='prescription-data', data={}, storage_type='session')
        ], fluid=True, className="py-3"),
        
        # Modals (simplified for space)
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
                dbc.ModalBody(id="modal-body"),
                dbc.ModalFooter(dbc.Button("Close", id="close-modal", className="ms-auto", n_clicks=0)),
            ],
            id="patient-modal",
            is_open=False,
            size="lg",
        ),
        
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Appointment")),
                dbc.ModalBody([
                    dbc.Select(id='appointment-doctor', placeholder='Select Doctor...', className='mb-2'),
                    dbc.Input(id='appointment-date', type='date', className='mb-2'),
                    dbc.Input(id='appointment-time', type='time', className='mb-2'),
                    dbc.Textarea(id='appointment-reason', placeholder='Reason...', className='mb-2')
                ]),
                dbc.ModalFooter([
                    dbc.Button("Schedule", id="schedule-appointment-confirm", color="primary", className="me-2"),
                    dbc.Button("Close", id="close-appointment-modal", color="secondary")
                ]),
            ],
            id="appointment-modal",
            is_open=False,
        ),
    ], id="app-container", style={"fontFamily": "'Inter', sans-serif", "minHeight": "100vh", "backgroundColor": custom_css["light_bg"]})

app.layout = create_layout()

# ========== CALLBACKS ==========

@app.callback(
    Output('language-store', 'data'),
    Input('language-selector', 'value')
)
def set_language(language):
    return language

@app.callback(
    Output('app-title', 'children'),
    Input('language-store', 'data')
)
def update_app_title(language):
    return translations[language]["app_title"]

@app.callback(
    Output('logout-button-container', 'children'),
    Input('user-store', 'data'),
    Input('language-store', 'data')
)
def update_logout_button(user_data, language):
    if user_data:
        return dbc.Button(
            [html.I(className="fas fa-sign-out-alt me-2"), translations[language]["logout"]],
            id='logout-btn', color='secondary', className='ms-2',
            style={"borderRadius": "8px", "padding": "6px 12px"}
        )
    return None

@app.callback(
    Output('user-store', 'data', allow_duplicate=True),
    Output('chat-history-store', 'data', allow_duplicate=True),
    Output('consultation-data', 'data', allow_duplicate=True),
    Output('appointment-data', 'data', allow_duplicate=True),
    Output('health-metrics-data', 'data', allow_duplicate=True),
    Output('pharmacy-stock-data', 'data', allow_duplicate=True),
    Output('toast-container', 'children', allow_duplicate=True),
    Output('tabs', 'value', allow_duplicate=True),
    Input('logout-btn', 'n_clicks'),
    State('language-store', 'data'),
    prevent_initial_call=True
)
def handle_logout(n_clicks, language):
    if n_clicks:
        toast = dbc.Toast(
            translations[language]["logout_success"],
            header="Success", icon="success", dismissable=True, is_open=True,
            duration=4000, style={"position": "fixed", "top": 10, "right": 10, "width": 350}
        )
        return None, [], {}, {}, {}, {}, toast, 'tab-login'
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    Output('tabs', 'children'),
    Output('tabs', 'value'),
    Input('user-store', 'data'),
    Input('language-store', 'data')
)
def update_tabs(user_data, language):
    if not user_data:
        login_tab = dcc.Tab(
            label=translations[language]["login_register"], value='tab-login',
            className="custom-tab", selected_className="custom-tab--selected",
            style=custom_css["tab"], selected_style=custom_css["tab_selected"]
        )
        return [login_tab], 'tab-login'
    
    tabs = []
    role = user_data.get('role')
    if role == 'patient':
        tabs.append(dcc.Tab(
            label=translations[language]["patient_dashboard"], value='tab-patient',
            className="custom-tab", selected_className="custom-tab--selected",
            style=custom_css["tab"], selected_style=custom_css["tab_selected"]
        ))
    elif role == 'doctor':
        tabs.append(dcc.Tab(
            label=translations[language]["doctor_dashboard"], value='tab-doctor',
            className="custom-tab", selected_className="custom-tab--selected",
            style=custom_css["tab"], selected_style=custom_css["tab_selected"]
        ))
    elif role == 'pharmacy':
        tabs.append(dcc.Tab(
            label=translations[language]["pharmacy_dashboard"], value='tab-pharmacy',
            className="custom-tab", selected_className="custom-tab--selected",
            style=custom_css["tab"], selected_style=custom_css["tab_selected"]
        ))
    
    return tabs, f'tab-{role}' if role else 'tab-login'

@app.callback(
    Output('tab-content', 'children'),
    Input('tabs', 'value'),
    Input('user-store', 'data'),
    Input('language-store', 'data')
)
def render_tab(tab, user_data, language):
    if not user_data and tab != 'tab-login':
        return html.Div()
    
    if tab == 'tab-login':
        return dbc.Card([
            dbc.CardHeader([
                html.H4([html.I(className="fas fa-user-circle me-2"), translations[language]["login_register"]], 
                        className="mb-0 d-flex align-items-center"),
            ], className='text-white', style={"backgroundColor": custom_css["primary_color"], "borderRadius": "12px 12px 0 0"}),
            dbc.CardBody([
                dbc.Input(id='name-input', placeholder=translations[language]["full_name"], type='text', className='mb-3', style={"borderRadius": "8px"}),
                dbc.Select(id='role-select', options=[
                    {'label': translations[language]["patient"], 'value': 'patient'},
                    {'label': translations[language]["doctor"], 'value': 'doctor'},
                    {'label': translations[language]["pharmacy"], 'value': 'pharmacy'}
                ], placeholder=translations[language]["select_role"], className='mb-3', style={"borderRadius": "8px"}),
                dbc.Input(id='phone-input', placeholder=translations[language]["phone"], type='tel', className='mb-3', style={"borderRadius": "8px"}),
                dbc.Input(id='village-input', placeholder=translations[language]["village"], type='text', className='mb-3', style={"borderRadius": "8px"}),
                dbc.Input(id='dob-input', placeholder=translations[language]["dob"], type='date', className='mb-3', style={"borderRadius": "8px"}),
                dbc.Select(id='gender-select', options=[
                    {'label': translations[language]["male"], 'value': 'male'},
                    {'label': translations[language]["female"], 'value': 'female'},
                    {'label': translations[language]["other"], 'value': 'other'}
                ], placeholder=translations[language]["gender"], className='mb-3', style={"borderRadius": "8px"}),
                dbc.Button([html.I(className="fas fa-sign-in-alt me-2"), translations[language]["submit"]], 
                          id='login-btn', color='primary', className='w-100',
                          style={"backgroundColor": custom_css["primary_color"], "border": "none", "borderRadius": "8px", "padding": "10px"}),
                html.Div(id='login-message', className='mt-3')
            ])
        ], style=custom_css["card"])
    
    # Simplified dashboards
    elif tab == 'tab-patient':
        return html.Div([
            html.H3(translations[language]["patient_dashboard"], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([html.H5([html.I(className="fas fa-user me-2"), translations[language]["patient_profile"]])],
                                      className='text-white', style={"backgroundColor": custom_css["primary_color"]}),
                        dbc.CardBody(id='patient-profile')
                    ], style=custom_css["card"], className='mb-3')
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([html.H5([html.I(className="fas fa-stethoscope me-2"), translations[language]["request_consultation"]])],
                                      className='text-white', style={"backgroundColor": custom_css["primary_color"]}),
                        dbc.CardBody([
                            dbc.Select(id='consultation-doctor', placeholder=translations[language]["select_doctor_placeholder"], className='mb-3'),
                            dbc.Textarea(id='consult-reason', placeholder=translations[language]["consultation_reason"], className='mb-3', style={"minHeight": "80px"}),
                            dbc.Button([html.I(className="fas fa-calendar-check me-2"), translations[language]["request_consult_btn"]], 
                                      id='request-consult-btn', color='primary', className='w-100')
                        ])
                    ], style=custom_css["card"])
                ], width=6)
            ])
        ])
    
    elif tab == 'tab-doctor':
        return html.Div([
            html.H3(translations[language]["doctor_dashboard"], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([html.H5([html.I(className="fas fa-clock me-2"), translations[language]["pending_consultations"]])],
                                      className='text-white', style={"backgroundColor": custom_css["primary_color"]}),
                        dbc.CardBody(id='consultations-table')
                    ], style=custom_css["card"])
                ], width=12)
            ])
        ])
    
    elif tab == 'tab-pharmacy':
        return html.Div([
            html.H3(translations[language]["pharmacy_dashboard"], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([html.H5([html.I(className="fas fa-edit me-2"), translations[language]["update_stock"]])],
                                      className='text-white', style={"backgroundColor": custom_css["primary_color"]}),
                        dbc.CardBody([
                            dbc.Input(id='medicine-name', placeholder=translations[language]["medicine_name_label"], className='mb-3'),
                            dbc.Input(id='medicine-qty', placeholder=translations[language]["quantity"], type='number', className='mb-3'),
                            dbc.Input(id='medicine-price', placeholder=translations[language]["price"], type='number', step='0.01', className='mb-3'),
                            dbc.Button([html.I(className="fas fa-save me-2"), translations[language]["update_stock_btn"]], 
                                      id='update-stock-btn', color='primary', className='w-100')
                        ])
                    ], style=custom_css["card"])
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([html.H5([html.I(className="fas fa-database me-2"), translations[language]["current_stock"]])],
                                      className='text-white', style={"backgroundColor": custom_css["primary_color"]}),
                        dbc.CardBody(id='pharmacy-stock-table')
                    ], style=custom_css["card"])
                ], width=6)
            ])
        ])
    
    return html.Div()

# ========== LOGIN CALLBACK ==========
@app.callback(
    Output('user-store', 'data'),
    Output('login-message', 'children'),
    Output('toast-container', 'children', allow_duplicate=True),
    Output('tabs', 'value', allow_duplicate=True),
    Input('login-btn', 'n_clicks'),
    State('name-input', 'value'),
    State('role-select', 'value'),
    State('phone-input', 'value'),
    State('village-input', 'value'),
    State('dob-input', 'value'),
    State('gender-select', 'value'),
    State('language-store', 'data'),
    prevent_initial_call=True
)
def handle_login(n_clicks, name, role, phone, village, dob, gender, language):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    if not all([name, role, phone, village, dob, gender]):
        toast = dbc.Toast(
            translations[language]["fill_all_fields"],
            header="Error", icon="danger", dismissable=True, is_open=True,
            duration=4000, style={"position": "fixed", "top": 10, "right": 10, "width": 350}
        )
        return dash.no_update, dbc.Alert(translations[language]["fill_all_fields"], color="danger"), toast, dash.no_update
    
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE phone = ?", (phone,))
    user = c.fetchone()
    
    if user:
        user_data = {'id': user[0], 'name': user[1], 'role': user[2], 'phone': user[3], 'village': user[4], 'dob': user[5], 'gender': user[6]}
        message = dbc.Alert(translations[language]["welcome_back"].format(user[1]), color="success")
        toast = dbc.Toast(
            translations[language]["welcome_back"].format(user[1]),
            header="Welcome", icon="success", dismissable=True, is_open=True,
            duration=4000, style={"position": "fixed", "top": 10, "right": 10, "width": 350}
        )
        tab_value = f'tab-{user[2]}'
    else:
        user_id = str(uuid.uuid4())
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (user_id, name, role, phone, village, dob, gender, datetime.now()))
        conn.commit()
        user_data = {'id': user_id, 'name': name, 'role': role, 'phone': phone, 'village': village, 'dob': dob, 'gender': gender}
        message = dbc.Alert(translations[language]["registration_success"], color="success")
        toast = dbc.Toast(
            translations[language]["registration_success"],
            header="Success", icon="success", dismissable=True, is_open=True,
            duration=4000, style={"position": "fixed", "top": 10, "right": 10, "width": 350}
        )
        tab_value = f'tab-{role}'
    
    conn.close()
    return user_data, message, toast, tab_value

# ========== OTHER CALLBACKS (Simplified) ==========
@app.callback(
    Output('patient-profile', 'children'),
    Input('user-store', 'data'),
    Input('language-store', 'data')
)
def update_patient_profile(user_data, language):
    if user_data and user_data.get('role') == 'patient':
        age = calculate_age(user_data.get('dob'))
        age_display = f"{translations[language]['age']}: {age} {translations[language]['years']}" if age else ""
        return [
            html.H5(user_data['name']),
            html.P(f"{translations[language]['phone']}: {user_data['phone']}"),
            html.P(f"{translations[language]['village']}: {user_data['village']}"),
            html.P(f"{translations[language]['gender']}: {user_data['gender']}"),
            html.P(age_display) if age_display else None
        ]
    return translations[language]["no_profile_data"]

@app.callback(
    Output('consultation-doctor', 'options'),
    Output('appointment-doctor', 'options'),
    Input('user-store', 'data'),
    Input('language-store', 'data')
)
def get_doctors_list(user_data, language):
    if not user_data or user_data.get('role') != 'patient':
        return [], []
    try:
        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        doctors = get_doctors(conn)
        conn.close()
        if not doctors:
            return [{'label': translations[language]["no_doctor_available"], 'value': 'none', 'disabled': True}], [{'label': translations[language]["no_doctor_available"], 'value': 'none', 'disabled': True}]
        return doctors, doctors
    except Exception as e:
        print(f"Error getting doctors: {e}")
        return [], []

@app.callback(
    Output('toast-container', 'children', allow_duplicate=True),
    Output('consultation-data', 'data', allow_duplicate=True),
    Input('request-consult-btn', 'n_clicks'),
    State('consult-reason', 'value'),
    State('consultation-doctor', 'value'),
    State('user-store', 'data'),
    State('language-store', 'data'),
    prevent_initial_call=True
)
def request_consultation(n_clicks, reason, doctor_id, user_data, language):
    if not n_clicks or not reason or not doctor_id:
        return dash.no_update, dash.no_update
    try:
        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        success = create_consultation(conn, user_data['id'], doctor_id, reason)
        conn.close()
        if success:
            toast = dbc.Toast(
                translations[language]["consultation_requested"],
                header="Success", icon="success", dismissable=True, is_open=True,
                duration=4000, style={"position": "fixed", "top": 10, "right": 10, "width": 350}
            )
            return toast, {'updated': True}
    except Exception as e:
        print(f"Error: {e}")
    return dash.no_update, dash.no_update

@app.callback(
    Output('consultations-table', 'children'),
    Input('user-store', 'data'),
    Input('tabs', 'value'),
    Input('language-store', 'data'),
    Input('consultation-data', 'data')
)
def update_consultations_table(user_data, tab, language, consultation_data):
    if user_data and user_data.get('role') == 'doctor' and tab == 'tab-doctor':
        try:
            conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
            df = pd.read_sql_query(
                "SELECT c.id, u.name, c.reason, c.status FROM consultations c JOIN users u ON c.patient_id = u.id WHERE c.doctor_id = ? AND c.status = 'requested'",
                conn, params=(user_data['id'],)
            )
            conn.close()
            if df.empty:
                return html.P(translations[language]["no_pending_consultations"])
            return dash_table.DataTable(
                columns=[
                    {'name': 'Patient', 'id': 'name'},
                    {'name': 'Reason', 'id': 'reason'},
                    {'name': 'Status', 'id': 'status'},
                ],
                data=df.to_dict('records'),
                style_cell={'textAlign': 'left', 'padding': '10px'},
                page_size=10
            )
        except Exception as e:
            print(f"Error: {e}")
    return dash.no_update

@app.callback(
    Output('pharmacy-stock-table', 'children'),
    Input('user-store', 'data'),
    Input('update-stock-btn', 'n_clicks'),
    Input('pharmacy-stock-data', 'data'),
    State('language-store', 'data'),
    prevent_initial_call=True
)
def update_stock_table(user_data, update_clicks, stock_data, language):
    if user_data and user_data.get('role') == 'pharmacy':
        try:
            conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
            df = pd.read_sql_query(
                "SELECT medicine, qty, price FROM pharmacy_stock WHERE pharmacy_id = ?",
                conn, params=(user_data['id'],)
            )
            conn.close()
            if df.empty:
                return html.P(translations[language]["no_stock_records"])
            return dash_table.DataTable(
                columns=[
                    {'name': 'Medicine', 'id': 'medicine'},
                    {'name': 'Quantity', 'id': 'qty', 'type': 'numeric'},
                    {'name': 'Price', 'id': 'price', 'type': 'numeric'},
                ],
                data=df.to_dict('records'),
                style_cell={'textAlign': 'left', 'padding': '10px'},
                page_size=10
            )
        except Exception as e:
            print(f"Error: {e}")
    return dash.no_update

@app.callback(
    Output('toast-container', 'children', allow_duplicate=True),
    Output('pharmacy-stock-data', 'data', allow_duplicate=True),
    Input('update-stock-btn', 'n_clicks'),
    State('medicine-name', 'value'),
    State('medicine-qty', 'value'),
    State('medicine-price', 'value'),
    State('user-store', 'data'),
    State('language-store', 'data'),
    prevent_initial_call=True
)
def update_stock(n_clicks, medicine, qty, price, user_data, language):
    if not n_clicks or not medicine or not qty or not price:
        return dash.no_update, dash.no_update
    
    try:
        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        success = upsert_pharmacy_stock(conn, user_data['id'], medicine, int(qty), float(price))
        conn.close()
        if success:
            toast = dbc.Toast(
                translations[language]["stock_updated"],
                header="Success", icon="success", dismissable=True, is_open=True,
                duration=4000, style={"position": "fixed", "top": 10, "right": 10, "width": 350}
            )
            return toast, {'updated': True}
    except Exception as e:
        print(f"Error: {e}")
    return dash.no_update, dash.no_update

# ========== RUN THE APP ==========
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8050)))
