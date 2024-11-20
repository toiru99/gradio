import json
import ast
import pandas as pd

class DataProcessor:
    def __init__(self, csv_path, port):
        self.csv_path = csv_path
        self.port = port
        self.df = pd.read_csv(csv_path)
        self.df['left'] = 0
        self.df['right'] = 0
        self.save_votes()
    
    def save_votes(self):
        votes_df = pd.DataFrame({
            'left': self.df['left'],
            'right': self.df['right']
        })
        votes_df.to_csv(f'votes_result_{self.port}.csv', index=False)
    
    def read_data(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = file.read()
            data_dict = ast.literal_eval(data)
            return data_dict.get('memory', {}).get('messages', [])
        except (ValueError, SyntaxError) as e:
            print(f"Python 객체 변환 오류: {e}")
            return []
    
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
            
            elif msg_type == "ai":
                if "```json" in msg_content:
                    try:
                        parts = msg_content.split("```json")
                        if len(parts) > 1:
                            json_text = parts[1].split("```")[0]
                            json_text = json_text.replace('\\n', '\n').strip()
                            query_content = json.loads(json_text)
                            
                            tool_name = query_content.get("command", {}).get("name", "")
                            tool_args = query_content.get("command", {}).get("args", {})
                            
                            formatted_query = f"🔍 사용한 도구: {tool_name}\n"
                            if "query" in tool_args:
                                formatted_query += f"📝 검색어: {', '.join(tool_args.get('query', []))}"
                            elif "region" in tool_args:
                                formatted_query += f"📍 지역: {tool_args.get('region')}"
                            current_conversation["query"].append(formatted_query)
                    except Exception:
                        continue
            
            elif msg_type == "AIMessageChunk":
                formatted_answer = msg_content.replace("\\n", "\n")
                formatted_answer = "\n".join(line.strip() for line in formatted_answer.split("\n") if line.strip())
                current_conversation["answer"] = formatted_answer
        
        if current_conversation["question"]:
            parsed_conversations.append(current_conversation)
        
        return parsed_conversations

    def process_file(self, file_content):
        if not file_content:
            return []
        try:
            data_dict = ast.literal_eval(file_content)
            messages = data_dict.get("memory", {}).get("messages", [])
            return self.parse_messages(messages)
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

    def calculate_statistics(self):
        total_votes = len(self.df)
        left_votes = self.df['left'].sum()
        right_votes = self.df['right'].sum()
        
        self.save_votes()
        
        stats = f"""
### 투표 결과
- 총 투표 수: {total_votes}건
- A 선택: {left_votes}건 ({(left_votes/total_votes*100):.1f}%)
- B 선택: {right_votes}건 ({(right_votes/total_votes*100):.1f}%)
        """
        return stats