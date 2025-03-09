import json
import random
import time
import os
import anthropic

# User Configuration 
API_KEY = 'your_anthropic_api_key'
INPUT_DATA_FILE = 'Path to a txt file with example questions for the topic'
TOPIC_NAME = "Name of a topic you want to generate questions for"
NUM_QUESTIONS_TO_GENERATE = 12

QUESTIONS_OUTPUT_FILE = 'questions.json'
QUESTIONS_SEPARATOR = "\n\n"
MODEL_NAME = "claude-3-7-sonnet-20250219"  # Use the appropriate Claude model
REASONING_MODEL_NAME = "claude-3-7-sonnet-20250219"  # Use a suitable Claude model for reasoning
BATCH_SIZE = 4  # Number of questions to validate in one batch
NUM_EXAMPLES_PER_GENERATION = 3

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=API_KEY)

def batch_validate_answers(question_data_list, topic):
    """
    Validate multiple generated questions in a single API call
    """
    if not question_data_list:
        return []
    
    validation_prompt = f"""I need you to solve multiple SAT questions on the topic of {topic}. For each question, provide ONLY the single digit number (0, 1, 2, or 3) of the correct answer.
If none of the answers fit or make sense, or the question is not answerable or relevant to the topic of {topic}, respond with "INVALID" for that question.

IMPORTANT: Respond with ONLY a comma-separated list of answers in the exact order of the questions presented.
For example: 2,1,INVALID,0

Here are the questions:
"""

    for i, question_data in enumerate(question_data_list, 1):
        validation_prompt += f"""
---
{i}. Passage: {question_data['passage']}

Question: {question_data['prompt']}

Choices:
0. {question_data['choices'][0]}
1. {question_data['choices'][1]}
2. {question_data['choices'][2]}
3. {question_data['choices'][3]}

"""

    try:
        response = client.messages.create(
            model=REASONING_MODEL_NAME,
            max_tokens=1500,
            temperature=1,
            thinking={
                "type": "enabled",
                "budget_tokens": 1024
            },
            messages=[{"role": "user", "content": validation_prompt}]
        )
        result_text = response.content[1].text.strip()
        print(f"Batch validation response: {result_text}")
        
        # Parse the comma-separated results
        results = []
        answer_texts = result_text.replace(" ", "").split(',')
        
        for answer_text in answer_texts:
            if answer_text == 'INVALID':
                results.append(None)
            else:
                try:
                    results.append(int(answer_text))
                except ValueError:
                    results.append(None)
        
        # If we didn't get enough results, pad with None
        while len(results) < len(question_data_list):
            results.append(None)
            
        # If we got too many results, trim the excess
        if len(results) > len(question_data_list):
            results = results[:len(question_data_list)]
            
        return results
        
    except Exception as e:
        print(f"Batch validation error: {str(e)}")
        return [None] * len(question_data_list)

def generate_question(client, examples, example_text, topic):
    """
    Generate a question using Claude API
    """
    prompt = f"""Generate a new SAT question focused specifically on the topic of {topic}, similar to the examples below. Focus on maintaining the same difficulty level and testing similar concepts. Follow this exact JSON format:
{example_text}

Consider these elements when generating:
1.  The passage context and style should be similar to the examples, and should provide context, NOT include the actual question itself. Ensure the passage is relevant to {topic}.
2.  The question should test the same transition skills within {topic}.
3.  Answer choices should follow similar patterns
4.  Distractors should be plausible but clearly incorrect
5.  Ensure that even for math non-multiple choice questions you always generate choices
6.  Ensure that the question itself is located in the question section and not in the passage.  The passage should set up the problem, and the 'prompt' field should contain the actual question to be answered.

Here are {len(examples)} example questions:
{examples}

Provide only the JSON output, with no additional text or explanation. Always set the right answer to 0."""

    try:
        response = client.messages.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.content[0].text
    except Exception as e:
        print(f"Question generation error: {str(e)}")
        return None

def main():
    # Read existing JSON file
    try:
        with open(QUESTIONS_OUTPUT_FILE, 'r') as json_file:
            all_data = json.load(json_file)
    except FileNotFoundError:
        all_data = {}

    # Read the input data file
    with open(INPUT_DATA_FILE, 'r') as file:
        text = file.read()

    # Split on double newlines
    chunks = text.split(QUESTIONS_SEPARATOR)

    # Example JSON text
    example_text = """{
    "passage": "Passage",
    "prompt": "The question?",
    "choices": [
        "choice 1",
        "choice 2",
        "choice 3",
        "choice 4"
    ],
    "correct_answer": 0,
    "used": false
    }"""

    # Ensure topic exists in all_data
    topic = TOPIC_NAME
    if topic not in all_data:
        all_data[topic] = {"e": [], "m": [], "h": []}

    # Generate questions
    generated_questions = 0
    questions_to_validate = []
    
    while generated_questions < NUM_QUESTIONS_TO_GENERATE:
        # Generate questions until we have enough for a batch or met our target
        while len(questions_to_validate) < BATCH_SIZE and generated_questions + len(questions_to_validate) < NUM_QUESTIONS_TO_GENERATE:
            # Randomly sample examples
            example_chunks = random.sample(chunks, min(NUM_EXAMPLES_PER_GENERATION, len(chunks)))
            examples = "\n\nExample 1:\n" + example_chunks[0]
            if len(example_chunks) > 1:
                examples += "\n\nExample 2:\n" + example_chunks[1]
            if len(example_chunks) > 2:
                examples += "\n\nExample 3:\n" + example_chunks[2]

            # Generate question
            response_text = generate_question(client, examples, example_text, topic)
            
            if not response_text:
                print("Failed to generate question. Trying again...")
                continue

            try:
                # Parse the generated question
                question_data = json.loads(response_text)
                questions_to_validate.append(question_data)
                print(f"Generated question {len(questions_to_validate)}, waiting for batch validation")
                
            except json.JSONDecodeError:
                print("Failed to parse JSON for question")
                continue
        
        # Validate batch of questions
        if questions_to_validate:
            print(f"Validating batch of {len(questions_to_validate)} questions...")
            validation_results = batch_validate_answers(questions_to_validate, topic)
            
            # Process validation results
            valid_questions = []
            for i, (question, result) in enumerate(zip(questions_to_validate, validation_results)):
                if result is not None:
                    # Update the correct answer in the question data
                    question['correct_answer'] = result
                    valid_questions.append(question)
                    generated_questions += 1
                else:
                    print(f"Question {i+1} in batch is invalid, skipping")
            
            # Add valid questions to all_data
            all_data[topic]["h"].extend(valid_questions)
            
            # Write the updated data
            with open(QUESTIONS_OUTPUT_FILE, 'w') as json_file:
                json.dump(all_data, json_file, indent=2)
                print(f"Added {len(valid_questions)} questions to the JSON file")
            
            # Clear the batch
            questions_to_validate = []

    print(f"Added a total of {generated_questions} questions to the JSON file")

if __name__ == "__main__":
    main()