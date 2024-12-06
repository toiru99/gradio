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
        self.df['neutral'] = 0 
        self.save_votes()
    
    def save_votes(self):
        votes_df = pd.DataFrame({
            'left': self.df['left'],
            'right': self.df['right'],
            'neutral': self.df['neutral'],
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
        total_votes = len(self.df)
        left_votes = self.df['left'].sum()
        right_votes = self.df['right'].sum()
        neutral_votes = self.df['neutral'].sum()
        
        self.save_votes()
        
        stats = f"""
### 투표 결과
- 총 투표 수: {total_votes}건
- A 선택: {left_votes}건 ({(left_votes/total_votes*100):.1f}%)
- B 선택: {right_votes}건 ({(right_votes/total_votes*100):.1f}%)
- 중립: {neutral_votes}건 ({(neutral_votes/total_votes*100):.1f}%)
        """
        return stats