import json
import random

class QuestionManager:
    def __init__(self, questions_file='questions.json'):
        self.questions_file = questions_file
        self.load_questions()
        
    def load_questions(self):
        try:
            with open(self.questions_file, 'r') as f:
                self.questions = json.load(f)
        except FileNotFoundError:
            self.questions = {}
            
    def save_questions(self):
        with open(self.questions_file, 'w') as f:
            json.dump(self.questions, f, indent=2)
            
    def get_question(self, topic, difficulty):
        if topic not in self.questions or not self.questions[topic][difficulty]:
            return None
            
        questions = self.questions[topic][difficulty]
        unused_questions = [q for q in questions if not q.get('used', False)]
        
        if not unused_questions:
            return None  # Return None instead of resetting all questions
            
        selected_question = random.choice(unused_questions)
        
        # Format the question data to match the expected structure in the GUI
        formatted_question = {
            'question': f"{selected_question.get('passage', '')}\n\n{selected_question['prompt']}" if selected_question.get('passage') else selected_question['prompt'],
            'choices': selected_question['choices'],
            'correct_answer': selected_question['correct_answer'],
            'used': selected_question['used']
        }
        
        return formatted_question
    
    def mark_question_as_used(self, topic, difficulty, question_text):
        if topic in self.questions and difficulty in self.questions[topic]:
            questions = self.questions[topic][difficulty]
            for q in questions:
                if q['passage'] in question_text:
                    q['used'] = True
                    self.save_questions()
                    break
        else:
            print("Invalid topic or difficulty level for marking.")