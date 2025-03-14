from typing import List, Dict
from pydantic import BaseModel, Field, validator
import random

class PredictionQuestion(BaseModel):
    """Pydantic model for validating prediction questions"""
    question_text: str = Field(..., min_length=20, max_length=150)
    interest: str
    source_articles: List[str]
    source_links: List[str]

    @validator('question_text')
    def validate_question_format(cls, v):
        # Allow questions starting with "Who" as well
        valid_starts = ('Will ', 'Can ', 'Who will ')
        if not any(v.startswith(start) for start in valid_starts):
            raise ValueError("Question must start with 'Will', 'Can', or 'Who will'")
        
        # Must contain either:
        # 1. Numbers
        # 2. Comparisons (higher, more, better)
        # 3. Policy-related terms
        # 4. Direct comparisons between entities
        if not (
            any(char.isdigit() for char in v) or  # Has numbers
            any(term in v.lower() for term in [
                'more', 'higher', 'better', 'greater',  # Comparisons
                'policy', 'bill', 'government', 'implement',  # Policy terms
                'than', 'versus', 'vs',  # Direct comparisons
                'first', 'before', 'lead'  # Temporal/ranking comparisons
            ]) or
            'both' in v.lower() or  # Multiple entity questions
            v.lower().startswith('who will')  # Direct comparison questions
        ):
            raise ValueError("Question must contain a number, comparison, or be about policy/government")
        
        # Must contain proper names (not single letters)
        words = v.split()
        if not any(word[0].isupper() and len(word) > 2 for word in words):
            raise ValueError("Question must contain proper names (not single letters)")
        
        # Must contain a time reference
        time_markers = [
            'match on', 'game on',  # Event dates
            'quarter', 'year',      # Business periods
            'season', 'tournament'  # Sports seasons
        ]
        if not any(marker in v.lower() for marker in time_markers):
            raise ValueError("Question must contain a valid time reference")
            
        return v

class QuestionGenerator:
    def __init__(self):  # Remove api_key parameter
        # Add player patterns as class attribute
        self.player_patterns = [
            # Common cricket roles
            'batsman', 'bowler', 'all-rounder', 'keeper', 'captain',
            # Common football positions
            'striker', 'forward', 'midfielder', 'defender', 'goalkeeper',
            # Action verbs
            'scored', 'hits', 'takes', 'saves', 'plays', 'shoots',
            # Statistics
            'goals', 'assists', 'runs', 'wickets', 'catches',
            # Status words
            'injured', 'fit', 'available', 'selected', 'starting'
        ]

        self.templates = {
            'cricket': [
                # Batting comparisons
                "Will {team} score more than {runs} runs against {opponent} {time}?",
                "Will {player} score less than {runs} runs {time}?",
                "Will {team} chase down the target of {runs} runs {time}?",
                
                # Bowling comparisons
                "Will {player} take more than {wickets} wickets {time}?",
                "Will {team} restrict {opponent} under {runs} runs {time}?",
                
                # Player comparisons
                "Will {player} score more runs than {opponent_player} {time}?",
                "Will {player} hit more than {boundaries} sixes {time}?",
                "Will both {player} and {opponent_player} score above {runs} runs {time}?"
            ],
            'football': [
                "Will {team} score {goals} goals against {opponent} {time}?",
                "Can {player} score in the first {minutes} minutes {time}?",
                "Will {team} win with a {goals}-goal margin {time}?",
                "Who will score first: {player} or {opponent_player} {time}?",
                "Will {player} score more goals than {opponent_player} {time}?",
                "Can {player} get more assists than {opponent_player} {time}?",
                "Will both {player} and {opponent_player} score {goals} goals {time}?",
                "Who will have more shots on target: {player} or {opponent_player} {time}?"
            ],
            'technology': [
                # Product/Service Metrics
                "Will {company} reach {users} million users for {product} {time}?",
                "Can {product} achieve {percent}% market share {time}?",
                "Will {company}'s {product} revenue grow by {percent}% {time}?",
                
                # Product Launches
                "Will {company} launch {product} {time}?",
                "Can {company} release {product} before {opponent_company} {time}?",
                "Will both {company} and {opponent_company} release their {category} products {time}?",
                
                # Technical Achievements
                "Can {company} fix {number} critical bugs in {product} {time}?",
                "Will {company}'s AI model outperform {opponent_company}'s {time}?",
                "Can {product} process {number} million transactions {time}?",
                
                # Market Competition
                "Will {company} acquire more startups than {opponent_company} {time}?",
                "Can {company} maintain its lead over {opponent_company} in {category} {time}?",
                "Will {company}'s stock outperform {opponent_company}'s {time}?"
            ],
            'sports': [
                "Will {team} win against {opponent} by {points} points {time}?",
                "Can {player} break the {record} record {time}?",
                "Will {team} qualify for {tournament} {time}?"
            ],
            'politics': [
                # Election/Voting
                "Will {politician} get {percent}% approval rating {time}?",
                "Can {politician} win {percent}% votes in {region} {time}?",
                "Will {party} secure {number} seats in {region} {time}?",
                
                # Legislative Process
                "Can {bill} get {number} votes in parliament {time}?",
                "Will {policy} be implemented in {region} {time}?",
                "Can {politician} pass more bills than {opponent_politician} {time}?",
                
                # Political Competition
                "Will {politician} have higher approval ratings than {opponent_politician} {time}?",
                "Can {party} form government in {region} {time}?",
                "Will both {politician} and {opponent_politician} participate in {event} {time}?",
                
                # Policy Impact
                "Will {policy} affect {number} million citizens {time}?",
                "Can {politician} reduce {metric} by {percent}% in {region} {time}?",
                "Will {party}'s {policy} get more support than {opponent_party}'s {time}?"
            ]
        }
        
        # Entity data for template filling
        self.entities = {
            'cricket': {
                'team': ['India', 'Australia', 'England', 'South Africa'],
                'player': [
                    'Virat Kohli', 'Rohit Sharma', 'KL Rahul', 
                    'Steve Smith', 'David Warner', 'Marnus Labuschagne',
                    'Joe Root', 'Ben Stokes', 'Jonny Bairstow',
                    'Kane Williamson', 'Babar Azam', 'Shakib Al Hasan'
                ],
                'opponent_player': [
                    'Pat Cummins', 'Mitchell Starc', 'Josh Hazlewood',
                    'James Anderson', 'Stuart Broad', 'Jasprit Bumrah',
                    'Kagiso Rabada', 'Trent Boult', 'Shaheen Afridi'
                ],
                'runs': [150, 180, 200, 250, 300],
                'wickets': [2, 3, 4, 5],
                'boundaries': [2, 3, 4, 5],
                'opponent': ['Pakistan', 'New Zealand', 'West Indies', 'Sri Lanka']
            },
            'football': {
                'team': ['Manchester United', 'Liverpool', 'Barcelona', 'Real Madrid'],
                'player': [
                    'Erling Haaland', 'Kylian Mbappe', 'Mohamed Salah',
                    'Harry Kane', 'Kevin De Bruyne', 'Bruno Fernandes',
                    'Vinicius Jr', 'Jude Bellingham', 'Marcus Rashford'
                ],
                'opponent_player': [
                    'Robert Lewandowski', 'Victor Osimhen', 'Lautaro Martinez',
                    'Bukayo Saka', 'Phil Foden', 'Rafael Leao',
                    'Darwin Nunez', 'Gabriel Jesus', 'Julian Alvarez'
                ],
                'goals': [2, 3, 4, 5],
                'minutes': [30, 45, 60],
                'opponent': ['Chelsea', 'Arsenal', 'Bayern Munich', 'PSG']
            },
            'technology': {
                'company': ['Apple', 'Google', 'Microsoft', 'Meta', 'Amazon', 'Tesla', 'NVIDIA'],
                'opponent_company': ['Samsung', 'OpenAI', 'IBM', 'Oracle', 'Intel', 'AMD'],
                'product': ['iPhone 16', 'Pixel 9', 'Windows 12', 'ChatGPT-5', 'Tesla Model 3'],
                'category': ['AI', 'Cloud', '5G', 'VR', 'Quantum Computing', 'Electric Vehicles'],
                'percent': [5, 10, 15, 20, 25, 30],
                'users': [1, 5, 10, 50, 100],
                'number': [10, 20, 50, 100, 500]
            },
            'sports': {
                'team': ['Lakers', 'Warriors', 'Celtics', 'Heat'],
                'player': ['LeBron', 'Curry', 'Djokovic', 'Nadal'],
                'points': [10, 15, 20, 25],
                'tournament': ['Champions League', 'World Cup', 'Olympics', 'Super Bowl'],
                'record': ['scoring', 'assists', 'points', 'championship']
            },
            'politics': {
                'politician': ['Biden', 'Trump', 'Harris', 'DeSantis', 'Newsom', 'McConnell'],
                'opponent_politician': ['Sanders', 'Warren', 'Cruz', 'Pelosi', 'McCarthy'],
                'party': ['Democrats', 'Republicans', 'Progressives', 'Conservatives'],
                'opponent_party': ['GOP', 'Democratic Party', 'Liberal Party', 'Labor Party'],
                'region': ['California', 'Texas', 'Florida', 'New York', 'Washington'],
                'bill': ['Healthcare Bill', 'Tax Reform', 'Climate Act', 'Education Bill'],
                'policy': ['Healthcare Reform', 'Tax Policy', 'Climate Policy', 'Immigration Reform'],
                'event': ['Debate', 'Town Hall', 'Campaign Rally', 'Press Conference'],
                'metric': ['Unemployment', 'Inflation', 'Crime Rate', 'Carbon Emissions'],
                'percent': [30, 40, 50, 60],
                'number': [1, 5, 10, 50]
            }
        }

        # Add common words to filter out from entity extraction
        self.filter_words = {
            # Months
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
            # Days
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            # Common words that might be capitalized
            'The', 'A', 'An', 'And', 'Or', 'But', 'For', 'With', 'In', 'On', 'At',
            'To', 'By', 'From', 'Up', 'Down', 'Over', 'Under',
            # Tech terms
            'software', 'hardware', 'platform', 'system', 'device', 'app',
            # Political terms
            'government', 'congress', 'senate', 'house', 'committee'
        }

        # Update event dates to be more dynamic
        self.event_dates = {
            'cricket': {
                'IPL 2025': {
                    'dates': ['March 22', 'March 26', 'April 2', 'May 25'],
                    'teams': ['Mumbai Indians', 'Chennai Super Kings', 'Royal Challengers'],
                    'matches': {
                        'March 22': ['Mumbai Indians', 'Chennai Super Kings'],
                        'March 26': ['Royal Challengers', 'Punjab Kings'],
                        'April 2': ['Gujarat Titans', 'Rajasthan Royals'],
                        'April 6': ['Delhi Capitals', 'Kolkata Knight Riders']
                    }
                },
                'T20 World Cup 2025': {
                    'dates': ['June 15', 'June 20', 'June 25', 'July 5'],
                    'teams': ['India', 'Australia', 'England', 'South Africa'],
                    'matches': {
                        'June 15': ['India', 'Australia'],
                        'June 20': ['England', 'South Africa'],
                        'June 25': ['India', 'England'],
                        'July 5': ['Australia', 'South Africa']
                    }
                }
            },
            'football': {
                'Premier League 2025': {
                    'dates': ['March 30', 'April 6', 'April 13'],
                    'teams': ['Manchester City', 'Arsenal', 'Liverpool'],
                    'matches': {
                        'March 30': ['Manchester City', 'Arsenal'],
                        'April 6': ['Liverpool', 'Manchester United'],
                        'April 13': ['Chelsea', 'Tottenham']
                    }
                },
                'Champions League 2025': {
                    'dates': ['April 9', 'April 16', 'April 30'],
                    'matches': {
                        'April 9': ['Real Madrid', 'Bayern Munich'],
                        'April 16': ['Manchester City', 'PSG'],
                        'April 30': ['Barcelona', 'Inter Milan']
                    }
                }
            }
        }

    def generate_question(self, articles: List[str], sources: List[str], interest: str) -> Dict:
        """Generate a prediction question based on articles and interest"""
        try:
            # Extract entities with improved classification
            article_entities = self._extract_entities_from_articles(articles)
            
            # Get base templates and entities
            templates = self.templates.get(interest, self.templates['sports'])
            entities = self.entities.get(interest, self.entities['sports'])
            
            # Update entities with extracted ones
            if article_entities['players']:
                # Split players between main and opponent lists
                new_players = list(article_entities['players'])
                random.shuffle(new_players)
                mid = len(new_players) // 2
                
                if interest in ['cricket', 'football', 'sports']:
                    entities['player'] = new_players[:mid] + entities['player']
                    entities['opponent_player'] = new_players[mid:] + entities['opponent_player']
            
            if article_entities['teams']:
                if interest in ['cricket', 'football', 'sports']:
                    entities['team'] = list(article_entities['teams']) + entities['team']
                    entities['opponent'] = list(article_entities['teams']) + entities['opponent']
            
            # Choose template and ensure different players/teams for comparison
            template = random.choice(templates)
            if '{opponent_player}' in template:
                valid_players = [p for p in entities['player'] if len(p) > 2]
                valid_opponents = [p for p in entities['opponent_player'] if len(p) > 2]
                
                if not valid_players or not valid_opponents:
                    # Fall back to predefined players
                    valid_players = self.entities[interest]['player']
                    valid_opponents = self.entities[interest]['opponent_player']
                
                player = random.choice(valid_players)
                opponent_player = random.choice([p for p in valid_opponents if p != player])
                entities = {**entities, 'player': player, 'opponent_player': opponent_player}
            
            if '{team}' in template and '{opponent}' in template:
                valid_teams = [t for t in entities['team'] if len(t) > 2]
                valid_opponents = [t for t in entities['opponent'] if len(t) > 2]
                
                if not valid_teams or not valid_opponents:
                    valid_teams = self.entities[interest]['team']
                    valid_opponents = self.entities[interest]['opponent']
                
                team = random.choice(valid_teams)
                opponent = random.choice([t for t in valid_opponents if t != team])
                entities = {**entities, 'team': team, 'opponent': opponent}

            # Use actual scheduled matches for questions
            if interest in self.event_dates:
                event = random.choice(list(self.event_dates[interest].keys()))
                event_data = self.event_dates[interest][event]
                
                # Pick a scheduled match
                match_date = random.choice(list(event_data['matches'].keys()))
                teams = event_data['matches'][match_date]
                
                time_ref = f"in the {event} match on {match_date}"
                team = teams[0]
                opponent = teams[1]
            
            # Fill template with validated entities
            question = template.format(
                **{k: (random.choice(v) if isinstance(v, list) else v) 
                   for k, v in entities.items()},
                time=time_ref
            )
            
            # Validate using Pydantic model
            validated_question = PredictionQuestion(
                question_text=question,
                interest=interest,
                source_articles=articles,
                source_links=sources
            )
            
            return {
                'question': validated_question.question_text,
                'sources': sources
            }
            
        except Exception as e:
            print(f"Error generating question: {str(e)}")
            fallback = self._generate_fallback_question(articles, interest)
            return {
                'question': fallback,
                'sources': sources[:1] if sources else []  # Include at least one source if available
            }

    def _extract_entities_from_articles(self, articles: List[str]) -> dict:
        """Extract named entities from articles with improved player and team detection"""
        entities = {
            'players': set(),
            'teams': set(),
            'tournaments': set()
        }
        
        # Common team indicators and prefixes
        team_indicators = {'FC', 'United', 'City', 'Team', 'XI', 'Cricket'}
        team_prefixes = {'Real', 'Manchester', 'Inter', 'AC', 'Bayern', 'Borussia'}
        tournament_indicators = {'League', 'Cup', 'Series', 'Championship', 'Trophy'}
        
        # Minimum length requirements
        MIN_TEAM_LENGTH = 3  # Minimum characters for team name
        MIN_PLAYER_LENGTH = 4  # Minimum characters for player name
        
        for article in articles:
            sentences = article.split('.')
            for sentence in sentences:
                words = sentence.split()
                
                # Look for capitalized words
                for i, word in enumerate(words):
                    if (word[0].isupper() and 
                        len(word) > 1 and 
                        word.lower() not in self.filter_words):
                        
                        # Check if it's part of a multi-word name
                        name_parts = [word]
                        next_idx = i + 1
                        while (next_idx < len(words) and 
                               words[next_idx][0].isupper() and 
                               len(words[next_idx]) > 1):
                            name_parts.append(words[next_idx])
                            next_idx += 1
                        
                        full_name = ' '.join(name_parts)
                        
                        # Skip if name is too short
                        if len(full_name) < MIN_TEAM_LENGTH:
                            continue
                        
                        # Classify the entity
                        if (any(indicator in full_name for indicator in team_indicators) or
                            any(full_name.startswith(prefix) for prefix in team_prefixes)):
                            if len(full_name) >= MIN_TEAM_LENGTH:
                                entities['teams'].add(full_name)
                        elif any(indicator in full_name for indicator in tournament_indicators):
                            entities['tournaments'].add(full_name)
                        else:
                            # Check context for player detection
                            context = ' '.join(words[max(0, i-3):min(len(words), i+4)]).lower()
                            if (len(full_name) >= MIN_PLAYER_LENGTH and
                                (any(pattern in context for pattern in self.player_patterns) or
                                 len(name_parts) >= 2)):  # Most player names have at least two parts
                                entities['players'].add(full_name)

        return entities

    def _validate_entity_for_interest(self, entity: str, interest: str) -> bool:
        """Validate if an entity is appropriate for the given interest"""
        # Add specific validation rules for each interest
        if interest == 'cricket':
            invalid_cricket = {'Test', 'ODI', 'T20', 'Series', 'Cup', 'Trophy', 'Match'}
            return entity not in invalid_cricket
        elif interest == 'football':
            invalid_football = {'League', 'Cup', 'FC', 'United', 'City'}
            return not any(word in entity for word in invalid_football)
        elif interest == 'technology':
            tech_indicators = {'Inc', 'Corp', 'Technologies', 'Software', 'Tech'}
            return any(word in entity for word in tech_indicators)
        return True 

    def _generate_fallback_question(self, articles: List[str], interest: str) -> str:
        """Generate a simple fallback question based on interest"""
        entities = self.entities.get(interest, self.entities['sports'])
        
        # Get event-based time reference
        if interest in self.event_dates:
            event = random.choice(list(self.event_dates[interest].keys()))
            date = random.choice(self.event_dates[interest][event])
            time_ref = f"in the {event} match on {date}"
        else:
            # For non-sports interests, use next quarter/year
            time_ref = "by the end of next quarter"
        
        if interest == 'politics':
            return f"Will {random.choice(entities['politician'])} win {random.choice(entities['percent'])}% votes {time_ref}?"
        elif interest == 'technology':
            return f"Will {random.choice(entities['company'])} launch {random.choice(entities['product'])} {time_ref}?"
        else:
            team = random.choice(entities['team'])
            opponent = random.choice([t for t in entities['opponent'] if t != team])
            return f"Will {team} win against {opponent} {time_ref}?"

    def generate_multiple_questions(self, articles: List[str], sources: List[str], 
                                  interest: str, count: int = 5) -> List[Dict]:
        """Generate multiple prediction questions based on articles and interest"""
        questions = []
        attempts = 0
        max_attempts = count * 2
        
        while len(questions) < count and attempts < max_attempts:
            try:
                question = self.generate_question(articles, sources, interest)
                if question['question'] not in [q['question'] for q in questions]:
                    questions.append(question)
            except Exception as e:
                print(f"Failed to generate question: {str(e)}")
            attempts += 1
        
        return questions[:count] 