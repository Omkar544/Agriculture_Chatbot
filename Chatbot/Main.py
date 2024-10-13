import streamlit as st
from hugchat import hugchat
from hugchat.login import Login
from googletrans import Translator
from PIL import Image
import os
import requests
import base64

# App title
st.set_page_config(page_title="🌾🤖 Agriculture Chatbot")

# Custom CSS for background color, logo, and spacing
st.markdown("""
    <style>
        .main {
            background-color: #000000;  /* Set background color to black */
            color: #ffffff;  /* Set text color to white for better visibility */
        }
        .st-chat-message {
            background-color: #333333;  /* Set background color of chat messages */
            color: #ffffff;  /* Set text color of chat messages */
        }
        .st-sidebar {
            background-color: #222222;  /* Set background color of sidebar */
            color: #ffffff;  /* Set text color of sidebar */
        }
        .centered-image {
            display: block;
            margin-left: auto;
            margin-right: auto;
            margin-bottom: 10px;  /* Adjust margin between logo and other content */
        }
    </style>
    """, unsafe_allow_html=True)

# Display the logo at the top of the app
logo_path = "images/logo3.jpg"  # Path to your logo image
if os.path.exists(logo_path):
    with open(logo_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f'<div style="text-align: center;"><img src="data:image/jpeg;base64,{encoded_image}" class="centered-image" width="200" height="225"></div>', 
        unsafe_allow_html=True
    )
else:
    st.warning("Logo image not found. Please check the file path.")

# Adding a placeholder for custom margin (if needed)
st.markdown('<div style="margin-top: 10px;"></div>', unsafe_allow_html=True)

# Hugging Face Credentials
with st.sidebar:
    st.title('🌾🤖 Agriculture Chatbot')
    if 'EMAIL' in st.secrets and 'PASS' in st.secrets:
        st.success('Login credentials already provided!', icon='✅')
        hf_email = st.secrets['EMAIL']
        hf_pass = st.secrets['PASS']
    else:
        hf_email = st.text_input('Enter E-mail:', type='password')
        hf_pass = st.text_input('Enter password:', type='password')
        if not (hf_email and hf_pass):
            st.warning('Please enter your credentials!', icon='⚠️')
        else:
            st.success('Proceed to entering your prompt message!', icon='👉')

# Language selection
language = st.sidebar.selectbox("Choose your language:", ['Marathi', 'Hindi', 'English'])

# Initialize the translator
translator = Translator()

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "Ask me anything about agriculture"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Function to fetch weather details using OpenWeatherMap API
def fetch_weather(city_name, api_key):
    try:
        base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
        response = requests.get(base_url)
        weather_data = response.json()
        st.write(weather_data)  # Debug: Print the entire response
        
        if weather_data.get("cod") == 200:  # Check if the response code is 200 (OK)
            main = weather_data.get("main", {})
            weather_description = weather_data.get("weather", [{}])[0].get("description", "No description available")
            temperature = main.get("temp", "No temperature data available")
            return f"The temperature in {city_name} is {temperature}°C with {weather_description}."
        else:
            return f"Error: {weather_data.get('message', 'Weather information not found.')}"
    except Exception as e:
        return f"Error fetching weather data: {e}"

# Function to fetch market rates (Placeholder)
def fetch_market_rate(product_name):
    # Implement the API call to get market rates
    # Here, we're using a placeholder response
    return f"The current market rate of {product_name} is ₹5000 per quintal."

# Function for generating LLM response
def generate_response(prompt_input, email, passwd):
    try:
        # Hugging Face Login
        sign = Login(email, passwd)
        cookies = sign.login()
        # Create ChatBot
        chatbot = hugchat.ChatBot(cookies=cookies.get_dict())
        response = chatbot.chat(prompt_input)
        # Ensure response is a string
        return response if isinstance(response, str) else str(response)
    except Exception as e:
        return f"Error during response generation: {e}"

# User-provided prompt
if prompt := st.chat_input(disabled=not (hf_email and hf_pass)):
    try:
        # Translate the user input to English if it's in Marathi or Hindi
        if language != 'English':
            prompt_en = translator.translate(prompt, src='auto', dest='en').text
        else:
            prompt_en = prompt

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Generate a new response if the last message is not from the assistant
        if st.session_state.messages[-1]["role"] != "assistant":
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Check for specific keywords to fetch weather or market rate details
                    if "weather" in prompt_en.lower():
                        city_name = "Kolhapur"  # Default city, change as needed
                        api_key = st.secrets["OPENWEATHER_API_KEY"]
                        response_en = fetch_weather(city_name, api_key)
                    elif "market rate" in prompt_en.lower():
                        product_name = "Soybean"  # Default product, change as needed
                        response_en = fetch_market_rate(product_name)
                    else:
                        response_en = generate_response(prompt_en, hf_email, hf_pass)
                    
                    # Ensure response_en is a string
                    if response_en:
                        if isinstance(response_en, str):
                            # Translate the response back to the selected language if necessary
                            if language != 'English':
                                response = translator.translate(response_en, src='en', dest=language.lower()).text
                            else:
                                response = response_en
                            st.write(response)
                        else:
                            st.write("Error: Received a non-string response.")
                    else:
                        st.write("Error: No response generated.")
            message = {"role": "assistant", "content": response}
            st.session_state.messages.append(message)
    except Exception as e:
        st.write(f"Error during processing: {e}")

# Add buttons to display weather and market rates
with st.sidebar:
    st.subheader("Get Real-Time Information")
    
    # Input field for city name
    city_name = st.text_input("Enter city name for weather:", value="Kolhapur")
    
    if st.button("Show Weather"):
        api_key = st.secrets["OPENWEATHER_API_KEY"]
        weather_info = fetch_weather(city_name, api_key)
        st.info(weather_info)

    if st.button("Show Market Rate"):
        product_name = "Soybean"  # Default product, change as needed
        market_rate_info = fetch_market_rate(product_name)
        st.info(market_rate_info)
