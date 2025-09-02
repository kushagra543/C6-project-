import streamlit as st
from groq import Groq
import os
import dotenv
import json
import re

dotenv.load_dotenv()
groq_api = os.getenv("groq_api")
client = Groq(api_key=groq_api)

def fetch_questions(text_content, quiz_level, num_questions):
    RESPONSE_JSON = {
        "mcqs": [
            {
                "mcq": "multiple choice question",
                "options": {
                    "a": "choice here1",
                    "b": "choice here2",
                    "c": "choice here3",
                    "d": "choice here4"
                },
                "correct": "correct choice option"
            }
        ]
    }

    PROMPT_TEMPLATE = f"""
    Text: {text_content}

    You are an expert in generating MCQ type quiz on the basis of provided content.  
    Given the above text, create a quiz of {num_questions} multiple choice questions keeping difficulty level as {quiz_level}.  

    Make sure the questions are not repeated and all the questions conform to the given text.  
    Make sure to format your response like RESPONSE_JSON below and use it as a guide.  
    Ensure to make an array of {num_questions} MCQs in the exact same JSON structure.  

    Here is the RESPONSE_JSON:
    {RESPONSE_JSON}
    """
    formatted_template = PROMPT_TEMPLATE
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",   # Groq ka free Llama model
        messages=[
            {
                "role": "user",
                "content": formatted_template
            }
        ],
        temperature=0.3,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    expected_response = response.choices[0].message.content
    print("Groq response:", expected_response)  # Debug print

    if not expected_response or expected_response.strip() == "":
        st.error("No response from Groq API. Please check your API key, prompt, or try again.")
        return []

    # Extract JSON from response using regex
    match = re.search(r'\{[\s\S]*\}', expected_response)
    if match:
        json_str = match.group(0)
        # Replace single quotes with double quotes for valid JSON
        json_str = json_str.replace("'", '"')
        try:
            data = json.loads(json_str)
            if "mcqs" in data and isinstance(data["mcqs"], list):
                return data["mcqs"]
            else:
                st.error("Response JSON does not contain 'mcqs' as a list. Please check your prompt or try again.")
                return []
        except json.JSONDecodeError:
            st.error("Failed to decode response. Please check your API key, prompt, or try again.")
            return []
    else:
        st.error("No valid JSON found in response. Please check your prompt or try again.")
        return []



def main():
    st.title("Quiz Generator App")
  
    text_content = st.text_area("Paste the text content here:")
   
    quiz_level = st.selectbox("Select quiz level:", ["Easy", "Medium", "Hard"])
    # Convert quiz level to lower casing
    quiz_level_lower = quiz_level.lower()
    num_questions = st.number_input("Number of questions:", min_value=1, max_value=20, value=5)
    if "questions" not in st.session_state:
        st.session_state["questions"] = []
    if "correct_answers" not in st.session_state:
        st.session_state["correct_answers"] = []
    if "selected_options" not in st.session_state:
        st.session_state["selected_options"] = []

    if st.button("Generate Quiz"):
        questions = fetch_questions(text_content=text_content, quiz_level=quiz_level_lower, num_questions=num_questions)
        if not questions:
            st.warning("No questions generated. Please check your input and try again.")
            st.session_state["questions"] = []
            st.session_state["correct_answers"] = []
            st.session_state["selected_options"] = []
        else:
            st.session_state["questions"] = questions
            st.session_state["correct_answers"] = [q["options"][q["correct"]] for q in questions]
            st.session_state["selected_options"] = [None] * len(questions)

    if st.session_state["questions"]:
        for idx, question in enumerate(st.session_state["questions"]):
            options = list(question["options"].values())
            selected = st.radio(question["mcq"], options, index=None, key=f"option_{idx}")
            st.session_state["selected_options"][idx] = selected
        if st.button("Submit"):
            marks = 0
            st.header("Quiz Result:")
            for i, question in enumerate(st.session_state["questions"]):
                selected_option = st.session_state["selected_options"][i]
                correct_option = st.session_state["correct_answers"][i]
                st.subheader(f"{question['mcq']}")
                st.write(f"You selected: {selected_option}")
                st.write(f"Correct answer: {correct_option}")
                if selected_option == correct_option:
                    marks += 1
            st.subheader(f"You scored {marks} out of {len(st.session_state['questions'])}")

if __name__ == "__main__":
    main()