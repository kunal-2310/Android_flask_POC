from flask import Flask, request, jsonify
from flask_cors import CORS
# from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import os
import re
import json
from datetime import datetime
# load_dotenv()

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
# os.environ["GOOGLE_API_KEY"]=os.getenv("GOOGLE_API_KEY")

app = Flask(__name__)
CORS(app)

@app.route("/home", methods=['GET'])
def home():
    return jsonify({
        "str": "Welcome"
    })

@app.route('/process', methods=['POST'])
def receive_prompt():
    data = request.get_json()
    if not data or 'input' not in data:
        return jsonify({"error": "Missing input field"}), 400

    actual_prompt = data['input']
    print("actual input:- ",actual_prompt)
    # actual_prompt="Assign a medium-priority plumbing inspection task to Rohan Mehta. The site is a customer named Priya Verma. Schedule it for tomorrow at 3 PM."

    # Initialize OpenAI LLM
    llm = ChatOpenAI(model="gpt-4o-mini")
    # llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    
    extract_fields = ChatPromptTemplate.from_messages([
    ("system", """You are a precise assistant that extracts task details from a user's instruction and strictly reports any missing details.

    Today's date is {today_date} and current time is {current_time}.

    This is a sample response format for reference only:
    {{
    "taskDescription": "AC Maintenance",
    "priority": "High",
    "startTime": "16-05-2025 11:00 am",
    "endTime": "16-05-2025 1:00 pm",
    "message": "please provide [taskDescription, priority, startTime, endTime]",
    "allfilled": false
    }}

    Instructions:
    - Prompt can be in hindi also so extract these fields from that too and consider 'kal' as tommorow. 
    - if any garbage or vague input is given donot consider it as the task description, task description must be meaningful.
    - Keep the structure of the response same: [taskDescription, priority, startTime, endTime, message, allfilled].
    - Extract the following fields from the prompt I will provide:
      - taskDescription
      - Identify the priority from the input by analyzing urgency-related words or tone. The priority should be classified as one of: [Critical, High, Normal, Low].
      - startTime
      - endTime (extract only if a duration or end time is explicitly provided)

    Important rules:
    - If a field is missing, leave it blank.
    - Priority can only be one of the following: [Critical, High, Normal, Low].
    - Do not invent or assume any data.
    - The 'startTime' and 'endTime' must follow the exact format: dd-MM-yyyy hh:mm am/pm.
    - If 'startTime' is provided as time-only:
        - Attach today’s date to it.
        - Compare the given time to the current time.
        - If the given time has already passed in the current half of the day (am/pm), assign the other half (i.e., pm if it’s passed am, or am if it’s passed pm).
        - If the given time is still upcoming, assign the current am/pm period.
    - Do not fill 'startTime' if it's invalid, incomplete, or missing.
    - Do not fill 'endTime' if no time or duration is mentioned. 
     
    - The 'message' field should clearly state which of these fields are missing in this exact format:Add commentMore actions
        "please provide [taskDescription, priority, startTime, endTime]"
        listing the missing fields inside the square brackets, comma-separated.
    - The 'allfilled' should be true only if all fields except 'message' are filled, otherwise false.

    Now here is the actual prompt: '{prompt}'""")
    ])



    messages = extract_fields.format_messages(
        prompt=actual_prompt,
        today_date=datetime.now().strftime('%d-%m-%Y'),
        current_time=datetime.now().strftime('%I:%M:%S %p')
    )
    final_prompt = "\n\n".join([f"{m.type.upper()}: {m.content}" for m in messages])

    # print("Final prompt :- ",final_prompt,"Ending of final prompt ------------------------------------------")

    # Run OpenAI model
    result = llm.invoke(final_prompt)
    # print("OpenAI Result:\n", result.content)
    # print(f"Raw LLM Response: {result}")

    match = re.search(r'\{.*?\}', result.content, re.DOTALL)
    if match:
        json_part = match.group()
        result_json = json.loads(json_part)
    else:
        result_json = {
    # # Convert string JSON to Python dict
            "error": "Model did not return JSON. Prompt may be incomplete or invalid.",
            "rawResponse": result
        }
    print("response :- ",result_json)
    
    time_format = "%d-%m-%Y %I:%M %p"
    start_time_str = result_json["startTime"]
    if start_time_str:
        start_time_str.upper()
        start_time = datetime.strptime(start_time_str, time_format)
        current_time=datetime.now()
        if current_time > start_time:
            # Toggle AM/PM
            if start_time.strftime("%p") == "AM":
                new_time = start_time.replace(hour=(start_time.hour % 12) + 12)
            else:
                new_time = start_time.replace(hour=(start_time.hour % 12))
            result_json["startTime"] = new_time.strftime(time_format).lower()
    
    return jsonify({"answer":result_json})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)