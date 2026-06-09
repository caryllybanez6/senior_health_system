class AIPriorityScorer:
    """
    AI-Enhanced Priority Scoring System
    Rules-based intelligent queue prioritization
    """
    
    @staticmethod
    def calculate_age_priority(age):
        """Older seniors get higher priority - Scale: 0-100 points"""
        if age >= 90:
            return 100
        elif age >= 80:
            return 85
        elif age >= 70:
            return 70
        elif age >= 65:
            return 60
        elif age >= 60:
            return 50
        else:
            return 30
    
    @staticmethod
    def calculate_emergency_priority(symptoms, is_emergency):
        """Emergency keywords trigger higher priority - Returns: 0-100 points"""
        if is_emergency:
            return 100
            
        emergency_keywords = [
            'chest pain', 'difficulty breathing', 'stroke', 'heart attack',
            'unconscious', 'bleeding', 'severe headache', 'high fever',
            'fall', 'fracture', 'confusion', 'seizure', 'dizziness',
            'nausea', 'vomiting', 'palpitations', 'shortness of breath'
        ]
        
        symptoms_lower = symptoms.lower() if symptoms else ""
        
        for keyword in emergency_keywords:
            if keyword in symptoms_lower:
                return 90
        return 0
    
    @staticmethod
    def calculate_waiting_time_priority(waiting_minutes):
        """Longer wait times increase priority - Scale: 0-50 points"""
        if waiting_minutes >= 120:
            return 50
        elif waiting_minutes >= 90:
            return 40
        elif waiting_minutes >= 60:
            return 30
        elif waiting_minutes >= 30:
            return 20
        else:
            return 10
    
    @staticmethod
    def calculate_medical_condition_priority(medical_conditions):
        """Pre-existing conditions increase priority - Scale: 0-80 points"""
        high_risk_conditions = [
            'heart disease', 'diabetes', 'hypertension', 'kidney disease',
            'respiratory', 'cancer', 'dementia', 'parkinson', 'asthma',
            'copd', 'stroke', 'arthritis', 'osteoporosis'
        ]
        
        conditions_lower = medical_conditions.lower() if medical_conditions else ""
        
        score = 0
        for condition in high_risk_conditions:
            if condition in conditions_lower:
                score += 15
                
        return min(score, 80)
    
    @staticmethod
    def calculate_total_priority(senior_age, symptoms, is_emergency, 
                                  waiting_minutes=0, medical_conditions=""):
        """Calculate TOTAL priority score (0-330+) - Higher score = higher queue priority"""
        age_score = AIPriorityScorer.calculate_age_priority(senior_age)
        emergency_score = AIPriorityScorer.calculate_emergency_priority(symptoms, is_emergency)
        waiting_score = AIPriorityScorer.calculate_waiting_time_priority(waiting_minutes)
        medical_score = AIPriorityScorer.calculate_medical_condition_priority(medical_conditions)
        
        total_score = age_score + emergency_score + waiting_score + medical_score
        
        return total_score
    
    @staticmethod
    def get_priority_level(score):
        """Convert numeric score to priority level"""
        if score >= 250:
            return "🚨 CRITICAL - IMMEDIATE ATTENTION"
        elif score >= 200:
            return "🔴 HIGH - See within 15 minutes"
        elif score >= 150:
            return "🟠 HIGH - See within 30 minutes"
        elif score >= 100:
            return "🟡 MEDIUM - See within 1 hour"
        elif score >= 50:
            return "🟢 NORMAL - See within 2 hours"
        else:
            return "⚪ LOW - Routine Check"
    
    @staticmethod
    def get_priority_color(score):
        """Get color code for priority level"""
        if score >= 200:
            return "#dc3545"  # Red - Critical
        elif score >= 150:
            return "#fd7e14"  # Orange - High
        elif score >= 100:
            return "#ffc107"  # Yellow - Medium
        elif score >= 50:
            return "#28a745"  # Green - Normal
        else:
            return "#6c757d"  # Gray - Low
    
    @staticmethod
    def arrange_queue(appointments_data):
        """AI-powered queue arrangement - Sorts appointments by priority score (highest first)"""
        for app in appointments_data:
            app['priority_score'] = AIPriorityScorer.calculate_total_priority(
                senior_age=app.get('age', 65),
                symptoms=app.get('symptoms', ''),
                is_emergency=app.get('is_emergency', False),
                waiting_minutes=app.get('waiting_minutes', 0),
                medical_conditions=app.get('medical_conditions', '')
            )
        
        # Sort by priority score (descending) and then by waiting time
        sorted_queue = sorted(appointments_data, 
                             key=lambda x: (x['priority_score'], x.get('waiting_minutes', 0)), 
                             reverse=True)
        
        # Assign queue positions
        for idx, app in enumerate(sorted_queue, 1):
            app['queue_position'] = idx
            app['queue_number'] = f"Q{idx:04d}"
            app['priority_level'] = AIPriorityScorer.get_priority_level(app['priority_score'])
            app['priority_color'] = AIPriorityScorer.get_priority_color(app['priority_score'])
        
        return sorted_queue