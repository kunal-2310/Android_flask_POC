from flask import Flask, request, jsonify
from flask_cors import CORS
# from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import os
import re
import json
from datetime import datetime

# Set your OpenAI API key
# os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["GOOGLE_API_KEY"]=os.getenv("GOOGLE_API_KEY")

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
    # actual_prompt="Assign a medium-priority plumbing inspection task to Rohan Mehta. The site is a customer named Priya Verma. Schedule it for tomorrow at 3 PM."

    # Initialize OpenAI LLM
    # llm = ChatOpenAI(model="gpt-4o-mini")
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    
#     extract_fields = ChatPromptTemplate.from_messages([
#         ("system", "You are a good assistant, help me in extracting some data from the prompt that is provided."),
#         ("human", """This is just sample data solely meant to understand the working, do not copy the data mentioned in this example:
#     I will provide you a prompt like 'Assign a high-priority AC maintenance task.Schedule it for tomorrow at 11 AM. and duration of the task is 2 hours.'
#     It is your job to analyse the initial prompt and give me the response in JSON format like:
#     {{
#     "taskDescription": "AC Maintenance",
#     "priority": "High",
#     "startTime": "16-05-2025 11:00 am",
#     "endTime": "16-05-2025 1:00 pm",
#     "message": "This field will contain the response from LLM if any field is empty like 'please provide task description or location'.",
#     "allfilled": false
#     }}"""),
#     ("human", "Today's date is {today_date}."),
#     ("human","""important -> do not add extra fields in response other than fields specified by me"""),
#         ("human", """\n\n\n\n do not generate the output based on the above provided sample that is only for reference how to generate response \
# \n\n\n now the actual prompt is '{prompt}' and if any field data is missing then keep it blank \
# \n\n\n if all the fields except "message" are filled then "allfilled" becomes "true"\
# \n\n\n if there is nothing provided in quotes '' after the actual prompt keyword then keep the structure of the response same and leave the values blank for eg- 'name':''\
# \n\n\n assign the priority on the basis of the urgency stated in the initial prompt accordingly to one of these- ['Low','Normal','High','Critical']""")
#     ])

    extract_fields = ChatPromptTemplate.from_messages([
        ("system", "You are an assistant designed to extract specific task-related fields from a prompt and return them in a well-structured JSON format."),

        ("human", """
    This is just sample data solely meant to understand the structure of the response — do NOT copy this data into your actual output.

    For example:
    Prompt: 'Assign a high-priority AC maintenance task. Schedule it for tomorrow at 11 AM. The duration of the task is 2 hours.'
    Response:
    {{
        "taskDescription": "AC Maintenance",
        "priority": "High",
        "startTime": "16-05-2025 11:00 am",
        "endTime": "16-05-2025 1:00 pm",
        "message": "This field will contain a message listing any missing fields like 'please provide task description, location'.",
        "allfilled": false
    }}
    """),

        ("human", "Today's date is {today_date}."),

        ("human", """
    IMPORTANT INSTRUCTIONS:
    - Only extract the following fields: "taskDescription", "priority", "startTime", "endTime", "message", and "allfilled".
    - Do not add extra fields or metadata to the response.

    ACTUAL EXTRACTION RULES:
    - The 'taskDescription' should reflect the task mentioned in the prompt.
    - The 'priority' must be set based on urgency words in the prompt: choose from ['Low', 'Normal', 'High', 'Critical']. 
    If urgency is unclear, leave it blank.
    - The 'startTime' must be extracted from the given prompt only, leave it blank if explicitly not mentioned in prompt.  
    If time is mentioned like 'tomorrow at 3 PM', use the provided date context.
    - The 'endTime' should ONLY be filled if the prompt explicitly mentions a task duration or end time.  
    Otherwise, leave it blank.
    - The 'message' should dynamically list any missing fields (except 'message' itself).  
    For example: if 'priority' and 'taskDescription' are missing, message should say: "please provide taskDescription, priority"
    - The 'allfilled' field should be 'true' ONLY if 'taskDescription', 'priority', 'startTime', and 'endTime' are all filled (excluding 'message').

    ACTUAL PROMPT TO PROCESS:
    '{prompt}'
    """)
    ])


    messages = extract_fields.format_messages(
        prompt=actual_prompt,
        today_date=datetime.now().strftime('%d-%m-%Y')
    )
    final_prompt = "\n\n".join([f"{m.type.upper()}: {m.content}" for m in messages])

    print("Final prompt :- ",final_prompt,"Ending of final prompt ------------------------------------------")

    # Run OpenAI model
    result = llm.invoke(final_prompt)
    # print("OpenAI Result:\n", result.content)
    print(f"Raw LLM Response: {result}")

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
    return jsonify(result_json)

if __name__ == '__main__':
    # receive_prompt()
    app.run(host='0.0.0.0', port=5001)
