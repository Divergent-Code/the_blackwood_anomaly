import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

def roll_d20(difficulty_class: int) -> str:
    """Rolls a 20-sided die to determine the success or failure of a risky player action.
    
    Args:
        difficulty_class: The target number to meet or exceed for success.
    """
    import random
    roll = random.randint(1, 20)
    if roll >= difficulty_class:
        return f"Roll: {roll} >= {difficulty_class}. Success."
    else:
        return f"Roll: {roll} < {difficulty_class}. Failure."

client = genai.Client()

formatted_history = [
    {"role": "user", "parts": [{"text": "I try to pick the lock to the heavy iron door."}]}
]

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=formatted_history,
    config={"tools": [roll_d20]}
)

print("Text:", response.text)
if response.function_calls:
    print("Function calls:")
    for fc in response.function_calls:
        print("name:", fc.name)
        print("args:", fc.args)
        
        # Intercept and execute
        dc = int(fc.args["difficulty_class"])
        result = roll_d20(dc)
        print("Tool result:", result)
        
        # Append to history
        formatted_history.append(response.candidates[0].content) # The function call part
        
        # Add the function response
        func_resp_part = types.Part.from_function_response(
            name=fc.name,
            response={"result": result}
        )
        formatted_history.append({"role": "user", "parts": [func_resp_part]})
        
        # Call again
        response2 = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=formatted_history,
            config={"tools": [roll_d20]}
        )
        print("Final response:", response2.text)
