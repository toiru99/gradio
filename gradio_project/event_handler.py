import gradio as gr
import pandas as pd

class EventHandler:
    def __init__(self, data_processor):
        self.data_processor = data_processor
    
    def load_initial_page(self):
        # 현재 페이지의 매핑 가져오기
        mapping = self.data_processor.get_mapping_for_page(0)
        
        # 매핑에 따라 데이터 순서 변경
        file_contents = []
        display_methods = []  # 각 모델별 display 메소드 저장
        
        # 1과 2에 대해서만 반복 (모델 2개)
        for i in ['1', '2']:  # 문자열로 직접 지정
            model = mapping[i]  # 이미 문자열이므로 변환 불필요
            file_contents.append(self.data_processor.df[f'data{ord(model)-64}'][0])
            # A 모델은 display_conversations, B 모델은 display_conversations_refactored 사용
            display_methods.append(
                self.data_processor.display_conversations if model == 'A' 
                else self.data_processor.display_conversations_refactored
            )
        
        current_page = f"현재 페이지: 1 / {len(self.data_processor.df)}"
        
        return (
            display_methods[0](file_contents[0]),
            display_methods[1](file_contents[1]),
            current_page
        )

    def update_page(self, page_index):
        # 현재 페이지의 매핑 가져오기
        mapping = self.data_processor.get_mapping_for_page(page_index)
        
        # 매핑에 따라 데이터 순서 변경
        file_contents = []
        display_methods = []
        
        # 1과 2에 대해서만 반복 (모델 2개)
        for i in ['1', '2']:
            model = mapping[i]
            file_contents.append(self.data_processor.df[f'data{ord(model)-64}'][page_index])
            display_methods.append(
                self.data_processor.display_conversations if model == 'A' 
                else self.data_processor.display_conversations_refactored
            )
        
        current_page = f"현재 페이지: {page_index + 1} / {len(self.data_processor.df)}"
        
        # 현재 페이지의 best 모델만 가져오기
        best_model = self.data_processor.df.at[page_index, 'best_model']
        
        # 중립 상태 확인 (worst 모델 제거)
        is_neutral = best_model == 'N'
        
        # 각 버튼의 상태 설정 (best 모델만)
        button_states = []
        for i in ['1', '2']:
            model = mapping[i]
            if best_model == model:
                button_states.append(gr.Button(value=f"모델 {i} (선택됨)", interactive=not is_neutral))
            else:
                button_states.append(gr.Button(value=f"모델 {i}", interactive=not is_neutral))
        
        # 툴 평가 버튼 상태
        tool_button_states = []
        for i in ['1', '2']:
            model = mapping[i]
            up_state = "👍 완료" if self.data_processor.df.at[page_index, f'model{model}_up'] > 0 else f"모델 {i} 툴 good"
            down_state = "👎 완료" if self.data_processor.df.at[page_index, f'model{model}_down'] > 0 else f"모델 {i} 툴 bad"
            tool_button_states.extend([up_state, down_state])
        
        return [
            display_methods[0](file_contents[0]),
            display_methods[1](file_contents[1]),
            page_index,
            current_page,
            *button_states,  # best 모델 버튼들만
            gr.Button(value="선택 취소", interactive=True),
            *[gr.Button(value=state) for state in tool_button_states]
        ]

    def cancel_selection(self, page_index, slider):
        # best 모델만 초기화
        self.data_processor.df.at[page_index, 'best_model'] = ''
        
        # 툴 평가 상태 초기화
        for model in ['A', 'B']:
            self.data_processor.df.at[page_index, f'model{model}_up'] = 0
            self.data_processor.df.at[page_index, f'model{model}_down'] = 0
        
        self.data_processor.save_votes()
        
        stats = self.data_processor.calculate_statistics()
        return self.update_page(page_index) + [page_index, str(stats), True]

    def move_page(self, page_index, direction):
        new_page = max(0, min(len(self.data_processor.df) - 1, page_index + direction))
        return self.update_page(new_page) + [new_page]

    def update_tool_vote(self, page_index, display_num, vote_type):
        # 현재 페이지의 매핑 가져오기
        mapping = self.data_processor.get_mapping_for_page(page_index)
        # 표시 번호를 실제 모델로 변환
        actual_model = mapping[str(display_num)]  # A, B, C 중 하나
        
        # 이전 선택 초기화
        opposite_vote = "down" if vote_type == "up" else "up"
        self.data_processor.df.at[page_index, f'model{actual_model}_{opposite_vote}'] = 0
        
        # 새로운 선택 기록 (1로 고정)
        column_name = f'model{actual_model}_{vote_type}'
        current_value = self.data_processor.df.at[page_index, column_name]
        # 이미 1이면 0으로, 아니면 1로 설정 (토글 기능)
        self.data_processor.df.at[page_index, column_name] = 0 if current_value == 1 else 1
        
        self.data_processor.save_votes()
        
        stats = self.data_processor.calculate_statistics()
        return self.update_page(page_index) + [page_index, str(stats)]

    def update_model_vote(self, page_index, model_num, vote_type):
        # 중립 선택 시
        if model_num == 'N':
            self.data_processor.df.at[page_index, 'best_model'] = 'N'
            self.data_processor.save_votes()
            stats = self.data_processor.calculate_statistics()
            return self.update_page(page_index) + [page_index, str(stats)]
        
        # 일반 모델 선택 시
        mapping = self.data_processor.get_mapping_for_page(page_index)
        actual_model = mapping[str(model_num)]
        
        # best 모델만 업데이트
        self.data_processor.df.at[page_index, 'best_model'] = actual_model
        
        self.data_processor.save_votes()
        stats = self.data_processor.calculate_statistics()
        return self.update_page(page_index) + [page_index, str(stats)]
    
    def change_session(self, session):
        # 세션 번호 추출 (예: "세션 1" -> 1)
        session_num = int(session.split()[-1])
        
        # 데이터 프로세서의 세션 변경
        self.data_processor.session = session_num
        
        # 이전 세션의 투표 데이터 로드 (만약 있다면)
        try:
            previous_votes = pd.read_csv(f'votes_result_session_{session_num}.csv')
            self.data_processor.df['best_model'] = previous_votes['best_model']
            self.data_processor.df['worst_model'] = previous_votes['worst_model']
            self.data_processor.df['model1_up'] = previous_votes['model1_up']
            self.data_processor.df['model1_down'] = previous_votes['model1_down']
            self.data_processor.df['model2_up'] = previous_votes['model2_up']
            self.data_processor.df['model2_down'] = previous_votes['model2_down']
        except FileNotFoundError:
            # 파일이 없으면 초기화
            self.data_processor.df['best_model'] = ''
            self.data_processor.df['worst_model'] = ''
            self.data_processor.df['model1_up'] = 0
            self.data_processor.df['model1_down'] = 0
            self.data_processor.df['model2_up'] = 0
            self.data_processor.df['model2_down'] = 0
        
        self.data_processor.save_votes()
        stats = self.data_processor.calculate_statistics()
        
        # 페이지 초기화 및 데이터 로드
        return self.update_page(0) + [0, str(stats)]