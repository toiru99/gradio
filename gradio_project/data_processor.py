import json
import ast
import pandas as pd
import random

class DataProcessor:
    def __init__(self, csv_path, session=1):
        self.csv_path = csv_path
        self.session = session
        self.df = pd.read_csv(csv_path)
        
        # 세션별 매핑 파일 경로
        self.mapping_file = f'session_{session}_mapping.json'
        
        # 각 페이지별 매핑 생성 또는 로드
        self.page_mappings = self.load_or_create_page_mappings()
        
        # 기존 열 초기화...
        if 'best_model' not in self.df.columns:
            self.df['best_model'] = ''
        if 'worst_model' not in self.df.columns:
            self.df['worst_model'] = ''
        
        # 모델별 투표 열 초기화 (A, B, C 기준)
        for model in ['A', 'B', 'C']:
            if f'model{model}_up' not in self.df.columns:
                self.df[f'model{model}_up'] = 0
            if f'model{model}_down' not in self.df.columns:
                self.df[f'model{model}_down'] = 0
        
        self.save_votes()
    
    def load_or_create_page_mappings(self):
        try:
            # 기존 매핑 파일이 있으면 로드
            with open(self.mapping_file, 'r') as f:
                mappings = json.load(f)
                # 새로운 페이지가 추가된 경우 처리
                if len(mappings) < len(self.df):
                    for i in range(len(mappings), len(self.df)):
                        mappings[str(i)] = self.generate_random_mapping()
                    with open(self.mapping_file, 'w') as f:
                        json.dump(mappings, f)
                return mappings
        except FileNotFoundError:
            # 없으면 모든 페이지에 대해 새로 생성
            mappings = {str(i): self.generate_random_mapping() for i in range(len(self.df))}
            with open(self.mapping_file, 'w') as f:
                json.dump(mappings, f)
            return mappings
    
    def generate_random_mapping(self):
        models = ['A', 'B', 'C']
        random.shuffle(models)
        return {i+1: model for i, model in enumerate(models)}
    
    def get_mapping_for_page(self, page_index):
        return self.page_mappings[str(page_index)]
    
    def save_votes(self):
        # 각 페이지의 매핑 정보 저장
        votes_df = pd.DataFrame({
            'best_model': self.df['best_model'],
            'worst_model': self.df['worst_model'],
            'model_mapping': [str(self.page_mappings[str(i)]) for i in range(len(self.df))],
            'modelA_up': self.df['modelA_up'],
            'modelA_down': self.df['modelA_down'],
            'modelB_up': self.df['modelB_up'],
            'modelB_down': self.df['modelB_down'],
            'modelC_up': self.df['modelC_up'],
            'modelC_down': self.df['modelC_down'],
        })
        votes_df.to_csv(f'votes_result_{self.session}.csv', index=False)
    
    def parse_messages(self, data):
        parsed_conversations = []
        current_conversation = {"question": "", "query": [], "answer": ""}
        
        for msg in data:
            msg_content = msg.get("data", {}).get("content", "") if msg.get("data") else msg
            msg_type = msg.get("type", "")
            
            if msg_type == "human":
                if current_conversation["question"]:
                    parsed_conversations.append(current_conversation)
                    current_conversation = {"question": "", "query": [], "answer": ""}
                current_conversation["question"] = msg_content
            
            elif msg_type == "ai" and 'tool_name' in msg.get('data', {}).get('additional_kwargs', {}):
                current_conversation["query"].append(msg_content)
            
            elif msg_type == "AIMessageChunk" and 'tool_name' not in msg.get('data', {}).get('content', {}):
                formatted_answer = msg_content.replace("\\n", "\n")
                formatted_answer = "\n".join(line.strip() for line in formatted_answer.split("\n") if line.strip())
                current_conversation["answer"] = formatted_answer
        
        if current_conversation["question"]:
            parsed_conversations.append(current_conversation)
        
        return parsed_conversations
    
    def parse_messages_refactored(self, data):
        parsed_conversations = []
        current_conversation = {"question": "", "query": [], "answer": ""}
        
        for msg in data:
            msg_type = msg.get("type", "")
            msg_data = msg.get("data", {})
            
            if msg_type == "human":
                if current_conversation["question"]:
                    parsed_conversations.append(current_conversation)
                    current_conversation = {"question": "", "query": [], "answer": ""}
                current_conversation["question"] = msg_data.get("content", "")
            
            elif msg_type == "ai":
                # AI가 직접 답변을 제공하는 경우
                if msg_data.get("content"):
                    current_conversation["answer"] = msg_data.get("content", "")
                    
                # Tool 사용이 있는 경우 
                if msg_data.get('tool_calls'):
                    tool_calls = msg_data.get('tool_calls', [])
                    for call in tool_calls:
                        tool_info = {
                            'name': call.get('name'),
                            'args': call.get('args', {})
                        }
                        current_conversation["query"].append(tool_info)
            
            elif msg_type == "tool":
                tool_content = msg_data.get("content", "")
                tool_name = msg_data.get("name", "")
                
                # 모든 tool 응답을 처리
                if tool_content:
                    try:
                        # 코드블록이 있는 경우
                        if "```" in tool_content:
                            # 코드블록 추출을 더 안전하게 처리
                            parts = tool_content.split("```")
                            if len(parts) >= 3:  # 정상적인 코드블록이 있는 경우
                                formatted_content = parts[1].strip()
                            else:
                                formatted_content = tool_content.strip()
                        else:
                            # JSON이나 일반 텍스트인 경우
                            formatted_content = tool_content.strip()
                        
                        # Tool 이름과 함께 응답 저장
                        current_conversation["answer"] += f"\n[{tool_name}] {formatted_content}"
                    except Exception as e:
                        print(f"Error processing tool content: {e}")
                        # 에러가 발생하면 원본 내용을 그대로 저장
                        current_conversation["answer"] += f"\n[{tool_name}] {tool_content}"

        if current_conversation["question"]:
            parsed_conversations.append(current_conversation)
        
        return parsed_conversations
    
        
    def process_file(self, file_content):
        if not file_content or pd.isna(file_content):
            return []
        try:
            data_dict = ast.literal_eval(file_content)
            messages = data_dict.get("memory", {}).get("messages", [])
            return self.parse_messages(messages)
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            return []
        
    def process_file_refactored(self, file_content):
        if not file_content or pd.isna(file_content):
            return []
        try:
            data_dict = ast.literal_eval(file_content)
            messages = data_dict.get('messages', [])
            return self.parse_messages_refactored(messages)
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            return []

    def display_conversations(self, file_content):
        try:
            conversations = self.process_file(file_content)
            responses = []
            
            for conv in conversations:
                # 기본 문자열 타입으로 변환하여 저장
                question = str(conv.get("question", "")) if conv.get("question") else None
                if question:
                    responses.append([question, None])
                
                queries = conv.get("query", [])
                if queries:
                    query_text = "\n".join(str(q) for q in queries)
                    responses.append([None, query_text])
                
                answer = str(conv.get("answer", "")) if conv.get("answer") else None
                if answer:
                    responses.append([None, answer])
            
            return responses
        except Exception as e:
            print(f"Error in display_conversations: {e}")
            return []
        
    def display_conversations_refactored(self, file_content):
        try:
            conversations = self.process_file_refactored(file_content)
            responses = []
            
            for conv in conversations:
                # 기본 문자열 타입으로 변환하여 저장
                question = str(conv.get("question", "")) if conv.get("question") else None
                if question:
                    responses.append([question, None])
                
                queries = conv.get("query", [])
                if queries:
                    query_texts = [f"```json\n{json.dumps(query, indent=2, ensure_ascii=False)}\n```" for query in queries]
                    query_text = "\n".join(query_texts)
                    responses.append([None, query_text])
                
                answer = str(conv.get("answer", "")) if conv.get("answer") else None
                if answer:
                    responses.append([None, answer])
            
            return responses
        except Exception as e:
            print(f"Error in display_conversations: {e}")
            return []

    def calculate_statistics(self):
        total_votes = len(self.df[self.df['best_model'] != ''])
        if total_votes == 0:
            return "아직 투표 결과가 없습니다."
        
        # 베스트 모델 통계
        best_counts = self.df['best_model'].value_counts()
        best_stats = "\n### 베스트 모델 투표 결과\n"
        for model in ['A', 'B', 'C', 'N']:
            count = best_counts.get(model, 0)
            percentage = (count/total_votes*100) if total_votes > 0 else 0
            model_name = "중립" if model == 'N' else f"모델 {model}"
            best_stats += f"- {model_name}: {count}건 ({percentage:.1f}%)\n"
        
        # 워스트 모델 통계
        worst_counts = self.df['worst_model'].value_counts()
        worst_stats = "\n### 워스트 모델 투표 결과\n"
        for model in ['A', 'B', 'C', 'N']:
            count = worst_counts.get(model, 0)
            percentage = (count/total_votes*100) if total_votes > 0 else 0
            model_name = "중립" if model == 'N' else f"모델 {model}"
            worst_stats += f"- {model_name}: {count}건 ({percentage:.1f}%)\n"
        
        # 툴 평가 통계 추가
        tool_stats = "\n### 툴 평가 결과\n"
        for model in ['A', 'B', 'C']:
            up_votes = self.df[f'model{model}_up'].sum()
            down_votes = self.df[f'model{model}_down'].sum()
            tool_stats += f"- 모델 {model}: 👍 {up_votes}건, 👎 {down_votes}건\n"
        
        return best_stats + worst_stats + tool_stats
    
    def get_displayed_model_name(self, actual_model):
        # 실제 모델 이름을 표시용 이름으로 변환
        reverse_mapping = {v: k for k, v in self.page_mappings[str(actual_model)].items()}
        return f"모델 {reverse_mapping[actual_model]}"