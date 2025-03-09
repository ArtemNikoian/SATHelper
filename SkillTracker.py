import csv
import random
from datetime import datetime
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SkillTracker:
    def __init__(self, filename='skill_data.csv'):
        self.filename = resource_path(filename)
        self.window_size = 20
        
    def load_data(self):
        try:
            with open(self.filename, 'r') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except FileNotFoundError:
            return []

    def save_attempt(self, topic, difficulty, correct):
        csv_path = resource_path(self.filename)
        data = self.load_data()
        
        attempt = {
            'topic': topic,
            'difficulty': difficulty,
            'correct': correct,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        data.append(attempt)
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['topic', 'difficulty', 'correct', 'date'])
            writer.writeheader()
            writer.writerows(data)

    def calculate_knowledge(self, topic):
        data = self.load_data()
        topic_attempts = [d for d in data if d['topic'] == topic][-self.window_size:]
        
        if not topic_attempts:
            return 0
                
        scores = {
            'e': {'wrong': -3, 'right': 1},
            'm': {'wrong': -2, 'right': 2}, 
            'h': {'wrong': -1, 'right': 3}
        }
        
        total_score = 0
        actual_max_possible = 0
        actual_min_possible = 0
        
        for attempt in topic_attempts:
            diff = attempt['difficulty']
            correct = attempt['correct'] == 'True'
            score_type = 'right' if correct else 'wrong'
            
            # Add the actual score
            total_score += scores[diff][score_type]
            
            # Calculate the actual maximum and minimum possible for this attempt
            actual_max_possible += scores[diff]['right']
            actual_min_possible += scores[diff]['wrong']
        
        # Normalize to 0-100 scale
        score_range = actual_max_possible - actual_min_possible
        if score_range == 0:
            return 50
        
        normalized_score = ((total_score - actual_min_possible) / score_range) * 100
        
        return round(normalized_score)

    def generate_synthetic_data(self, topic, scores):
        """
        Add attempts for a topic using a list of 6 numbers:
        scores = [e_wrong, m_wrong, h_wrong, e_right, m_right, h_right]
        """
        # Calculate totals for each difficulty
        e_total = scores[0] + scores[3]
        m_total = scores[1] + scores[4]
        h_total = scores[2] + scores[5]
        
        total_attempts = sum(scores)
        
        if total_attempts > self.window_size:
            # Calculate success rates for each difficulty
            e_success_rate = scores[3] / e_total if e_total > 0 else 0
            m_success_rate = scores[4] / m_total if m_total > 0 else 0
            h_success_rate = scores[5] / h_total if h_total > 0 else 0
            
            # Calculate proportions of each difficulty in original data
            e_proportion = e_total / total_attempts
            m_proportion = m_total / total_attempts
            h_proportion = h_total / total_attempts
            
            # Calculate new counts maintaining proportions (rounded to nearest integer)
            new_e = round(self.window_size * e_proportion)
            new_m = round(self.window_size * m_proportion)
            new_h = self.window_size - new_e - new_m  # Ensure total is exactly 15
            
            # Calculate right/wrong split for each difficulty
            e_right = round(new_e * e_success_rate)
            m_right = round(new_m * m_success_rate)
            h_right = round(new_h * h_success_rate)
            
            results = []
            # Add wrong attempts
            results.extend([('e', False)] * (new_e - e_right))
            results.extend([('m', False)] * (new_m - m_right))
            results.extend([('h', False)] * (new_h - h_right))
            
            # Add right attempts
            results.extend([('e', True)] * e_right)
            results.extend([('m', True)] * m_right)
            results.extend([('h', True)] * h_right)
        else:
            # If total attempts ≤ 15, use original data
            results = []
            results.extend([('e', False)] * scores[0])
            results.extend([('m', False)] * scores[1])
            results.extend([('h', False)] * scores[2])
            results.extend([('e', True)] * scores[3])
            results.extend([('m', True)] * scores[4])
            results.extend([('h', True)] * scores[5])
        
        # Shuffle the results to avoid patterns
        random.shuffle(results)
        
        # Save attempts
        for difficulty, correct in results:
            self.save_attempt(topic, difficulty, str(correct))